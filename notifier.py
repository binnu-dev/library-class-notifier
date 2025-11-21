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
            "title": f"[{lecture.get('library', '도서관')}] {lecture['title']}",
            "description": f"새로운 강좌가 등록되었습니다!\n\n**기간**: {lecture['date']}\n**상태**: {lecture['status']}",
            "url": lecture['link'],
            "color": 5814783,  # Blue/Purple color
            "footer": {
                "text": "Library Class Notifier"
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
