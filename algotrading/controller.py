import json
import requests
from django.shortcuts import redirect
from django.db.models import Count, Sum, Case, When, F
from django.conf import settings

import re
import pandas as pd
import csv
from datetime import datetime
import ssl
import asyncio
import upstox_client
import websockets
from google.protobuf.json_format import MessageToDict


from algotrading.models import *
from notification.controller import Discord
from user.models import User
import algotrading.format_pb2 as pb

BROKER_CHARGE = 0


class TokenError(Exception):
    pass


class Upstox:
    BASE_API_URL = "https://api-v2.upstox.com/"

    def __init__(self, user: User) -> None:
        token = AccessToken.objects.latest("date")
        if token.date.date() != datetime.today().date():
            raise TokenError(f"Upstox-Auth login required by user {user}")
        self.auth_code = AuthCode.objects.latest("date").code
        self.user = user
        self.access_token = token
        self.headers = {
            "accept": "application/json",
            "Api-Version": "2.0",
            "Authorization": f"Bearer {self.access_token}",
        }

    def call_upstox_api(
        self, endpoint, type="GET", headers=None, data=None, params=None
    ):
        if headers == None:
            headers = self.headers

        response = requests.request(
            type, url=self.BASE_API_URL, headers=headers, data=data, params=params
        )
        return response.json()

    # def get_stock_info(self,stock):
    #     nse = Nse()
    #     nse_data = nse.get_quote(stock,all_data=True)
    #     price = nse_data.get("priceInfo").get("lastPrice")
    #     issued_volume = nse_data.get("securityInfo").get("issuedSize")
    #     previous_close = nse_data.get("priceInfo").get("")

    @staticmethod
    def api_login(user: User, code):
        """
        Upstox's API Login when Morning Authorization is done.
        """

        url = Upstox.BASE_API_URL + "login/authorization/token"
        headers = {
            "accept": "application/json",
            "Api-Version": "2.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "code": code,
            "client_id": user.upstox_api_key,
            "client_secret": user.upstox_api_secret,
            "redirect_uri": user.upstox_redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.request("POST", url=url, headers=headers, data=data).json()
        AccessToken.objects.create(user=user, token=response["access_token"])

        return response["access_token"]

    # get user fund and margin
    def get_user_fund_and_margin(self):
        data = {"segment": "SEC"}

        response = self.call_upstox_api("user/get-funds-and-margin", data=data)

        try:
            UserFund.objects.create(
                user=self.user,
                available_money=response.get("data")
                .get("equity")
                .get("available_margin"),
            )
        except Exception as e:
            print(e.args)

        return

    def market_quote(self, instrument_symbl_list):
        data = {}
        endpoint = "market-quote/quotes"

        params = {"symbol": ",".join(instrument_symbl_list)}

        response = self.call_upstox_api(endpoint, params=params)
        # TODO error handling

        for dicts in response["data"].values():
            stock = StockData.objects.get(symbl=dicts.get("symbol"))
            stock.rate = dicts.get("last_price")
            data[dicts.get("instrument_token")] = stock.rate
            stock.save()
            # dicts.get('volume') can be useful

        return data

    def keep_watch_on_stocks(self, instrument_symbl_list):
        endpoint = "market-quote/quotes"
        params = {"symbol": ",".join(instrument_symbl_list)}

        response = self.call_upstox_api(endpoint=endpoint, params=params)
        # TODO error handling

        for dicts in response["data"].values():
            stock = StockData.objects.get(symbl=dicts.get("symbol"))
            latest_price = dicts.get("last_price")
            if latest_price <= stock.rate * (99 / 100):
                print("stock sold")
                # TODO sell the stock
                msg_str = "----------------------------\n"
                msg_str += f"{stock.symbl} SOLD\n"
                msg_str += f'Selling Price -> {format(latest_price,".2f")}\n'
                # msg_str += f'Bought for -> {format(stock.price_bought,".2f")}\n'
                # msg_str += f'Total Profit -> {format(latest_price - stock.price_bought - BROKER_CHARGE,".2f")}\n'
                # msg_str +=  f'{format(((latest_price - stock.price_bought - BROKER_CHARGE)/stock.price_bought)*100,".2f")}\n'
                msg_str += f"{len(instrument_symbl_list)} Left for Today\n"
                msg_str += "----------------------------\n"
                Discord.notify_discord(msg_str)

                # TODO remove the stock from list
            stock.rate = latest_price
            stock.day_high = dicts.get("ohlc").get("high")
            stock.day_open = dicts.get("ohlc").get("open")
            stock.save()

    def morning_update(self):
        """
        updates all the stock rates,
        Ideally before 9:15,
        should only be run once.
        """
        stocks = StockData.objects.filter().values_list("instrument_symbl", flat=True)
        count = 0
        for x in range(int(len(stocks) / 500) + (len(stocks) % 500 != 0)):
            endpoint = "market-quote/quotes"

            params = {"symbol": ",".join(stocks[500 * x : 500 * (x + 1)])}

            response = self.call_upstox_api(endpoint=endpoint, params=params)

            for dicts in response["data"].values():
                count += 1
                stock = StockData.objects.get(symbl=dicts.get("symbol"))
                stock.rate = dicts.get("last_price")
                stock.day_open = dicts.get("ohlc").get("low")
                stock.day_high = dicts.get("ohlc").get("high")
                stock.save()

        msg_str = "----------------------------\n"
        msg_str += f"Morning Stock Updation Done : {datetime.now().time()}\n"
        msg_str += f"Stocks Updated: {count}\n----------------------------"
        Discord.notify_discord(msg_str)

    def buy_stocks(self, instrument_symbl_list):
        data = self.market_quote(instrument_symbl_list)
        fund = UserFund.objects.filter(user=self.user).latest("date").available_money
        for instrument, price in data:
            avail_price = fund / len(instrument_symbl_list)
            amount_to_buy = avail_price / 5

    @staticmethod
    def update_stock_list():
        """
        Updates Upstox's listed trading symbols
        """
        with open("NSE.csv", mode="r") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader, None)
            for row in csv_reader:
                object = NseSheetStock.objects.filter(symbl=row[2])
                if len(object) > 0:
                    if row[4] == "":
                        price = 0
                    else:
                        price = row[4]
                    try:
                        StockData.objects.create(
                            symbl=row[2], instrument_symbl=row[0], rate=price
                        )
                    except Exception as e:
                        print(e)

    @staticmethod
    def get_insight(user: User, start_date: datetime, end_date: datetime) -> dict:
        # fields to annotate upon
        sell_count = Count(
            Case(
                When(type="SELL", then=F("quantity")),
                output_field=models.IntegerField(),
            )
        )
        buy_count = Count(
            Case(
                When(type="BOUGHT", then=F("quantity")),
                output_field=models.IntegerField(),
            )
        )
        sell_sum = Sum(
            Case(When(type="SELL", then=F("price")), output_field=models.DecimalField())
        )
        buy_sum = Sum(
            Case(
                When(type="BOUGHT", then=F("price")), output_field=models.DecimalField()
            )
        )

        data = {}

        closed_transactions = StockTransaction.objects.filter(
            user=user, datetime__gte=start_date, datetime__lte=end_date, closed=True
        ).annotate(
            sell_count=sell_count,
            buy_count=buy_count,
            sell_sum=sell_sum,
            buy_sum=buy_sum,
        )

        data["closed"] = {
            "buy_sum": closed_transactions["buy_sum"],
            "sell_sum": closed_transactions["sell_sum"],
            "p&l": closed_transactions["sell_sum"] - closed_transactions["buy_sum"],
        }

        open_transactions = StockTransaction.objects.filter(
            user=user, datetime__gte=start_date, datetime__lte=end_date, closed=False
        )

        if len(open_transactions) > 0:
            data["open"] = {"buy_sum": 0, "p&l": 0, "table_list": []}
            for transactions in open_transactions:
                data["open"]["buy_sum"] += transactions.price
                data["open"]["p&l"] += transactions.price - (
                    transactions.symbl.rate * transactions.quantity
                )
                data["open"]["table_list"].append(
                    [
                        transactions.symbl.symbl,
                        transactions.quantity,
                        transactions.symbl.rate,
                        transactions.rate,
                        transactions.price
                        - (transactions.symbl.rate * transactions.quantity),
                    ]
                )

        return data
    
    @staticmethod
    def get_upstox_redirect_uri(user : User) -> str:
        return settings.WEBSITE_BASE_URL + 'trade/upstox-auth/' + user.pk
    
    async def fetch_market_through_websocket(self, instrument_dict):


        def get_market_data_feed_authorize(api_version, configuration):
            """Get authorization for market data feed."""
            api_instance = upstox_client.WebsocketApi(
                upstox_client.ApiClient(configuration))
            api_response = api_instance.get_market_data_feed_authorize(api_version)
            return api_response


        def decode_protobuf(buffer):
            """Decode protobuf message."""
            feed_response = pb.FeedResponse()
            feed_response.ParseFromString(buffer)
            return feed_response


        # Create default SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Configure OAuth2 access token for authorization
        configuration = upstox_client.Configuration()
        configuration.access_token = self.access_token

        # create an instance of the API class
        api_instance = upstox_client.WebsocketApi(upstox_client.ApiClient(configuration))
        api_version = '2.0'


        # Get market data feed authorization
        response = get_market_data_feed_authorize(
            api_version, configuration)

        # Connect to the WebSocket with SSL context
        async with websockets.connect(response.data.authorized_redirect_uri, ssl=ssl_context) as websocket:
            print('Connection established')

            await asyncio.sleep(1)  # Wait for 1 second

            # Data to be sent over the WebSocket
            data = {
                "guid": "someguid",
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": [x for x in instrument_dict.keys()]
                }
            }

            # Convert data to binary and send over WebSocket
            binary_data = json.dumps(data).encode('utf-8')
            await websocket.send(binary_data)

            pe_pattern = r'\D+(\d+)PE'
            ce_pattern = r'\D+(\d+)CE'
            
            # Continuously receive and decode data from WebSocket

            while True:
                message = await websocket.recv()
                decoded_data = decode_protobuf(message)

                # Convert the decoded data to a dictionary
                data_dict = MessageToDict(decoded_data)
                pe_dict = dict()
                ce_dict = dict()
                for x in data_dict['feeds'].keys():
                    if "CE" in instrument_dict[x]:
                        match = re.search(ce_pattern, instrument_dict[x])
                        if match:
                            data_dict["feeds"][x]['price'] = int(match.group(1))
                        ce_dict[x] = data_dict["feeds"][x]

                    else:
                        match = re.search(pe_pattern, instrument_dict[x])
                        if match:
                            data_dict["feeds"][x]['price'] = int(match.group(1))
                        pe_dict[x] = data_dict["feeds"][x]

                ce_dict = dict(sorted(ce_dict.items(), key=lambda x: x[1]['price']))
                pe_dict = dict(sorted(pe_dict.items(), key=lambda x: x[1]['price']))

                #TODO pub-sub this data.
                
                # with ThreadPoolExecutor() as executor:
                #     future1 = executor.submit(scraping_data_to_excel,ce_dict, "CE", price, expiry_date)
                #     future2 = executor.submit(scraping_data_to_excel,pe_dict, "PE", price, expiry_date)

                #     wait([future1, future2])
            

def get_stocks_by_nsesheet():
    """
    gets all the stocks listed in NSE's site
    """

    with open("nse.csv", mode="r") as csv_file:
        csv_reader = csv.reader(csv_file)

        for row in csv_reader:
            NseSheetStock.objects.create(symbl=row[0])
