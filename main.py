import os
from dotenv import load_dotenv
from scraper import CheongcheonScraper
from notifier import DiscordNotifier
from storage import Storage

# Load environment variables
load_dotenv()

def main():
    print("Starting Library Class Notifier...")
    
    # Initialize components
    scraper = CheongcheonScraper()
    storage = Storage()
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("WARNING: DISCORD_WEBHOOK_URL is not set. Notifications will not be sent.")
    
    notifier = DiscordNotifier(webhook_url)

    # 1. Scrape current lectures
    print("Fetching lectures...")
    current_lectures = scraper.get_lectures()
    print(f"Found {len(current_lectures)} lectures.")

    # 2. Check for new lectures
    new_lectures = storage.get_new_lectures(current_lectures)
    print(f"New lectures: {len(new_lectures)}")

    # 3. Notify
    for lecture in new_lectures:
        notifier.send_notification(lecture)

    # 4. Update storage
    # We save the current state as the new 'seen' state
    # Note: This simple logic assumes if it's on the page, it's 'current'.
    # If items disappear from the page, they will be removed from storage.
    # If they reappear, they will be treated as new. This is usually acceptable.
    storage.save_seen_lectures(current_lectures)
    print("Done.")

if __name__ == "__main__":
    main()
