import os
import requests
import json

class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_notification(self, lecture):
        if not self.webhook_url:
            print("No webhook URL provided.")
            return

        embed = {
            "title": f"📚 새로운 수업: {lecture['title']}",
            "url": lecture['link'],
            "color": 5814783,  # Blue-ish
            "fields": [
                {
                    "name": "상태",
                    "value": lecture['status'],
                    "inline": True
                },
                {
                    "name": "일시",
                    "value": lecture['date'],
                    "inline": True
                }
            ],
            "footer": {
                "text": "청천도서관 알리미"
            }
        }

        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            print(f"Notification sent for: {lecture['title']}")
        except Exception as e:
            print(f"Failed to send notification: {e}")
