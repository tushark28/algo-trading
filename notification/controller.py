import requests
from django.conf import settings

class Discord:
    
    @staticmethod
    def notify_discord(message):
        if not message:
            print("Empty discord message")
            return
        
        payload = {'content': message}
        response = requests.post(settings.algo_trading_notification_url, json=payload)

        if response.status_code != 204:
            print('Error while Notifying on discord',response.text)

        return