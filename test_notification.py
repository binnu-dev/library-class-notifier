import os
from dotenv import load_dotenv
from scraper import CheongcheonScraper
from notifier import DiscordNotifier

# Load environment variables
load_dotenv()

def test_single_notification():
    print("Testing single notification...")
    
    # Initialize
    scraper = CheongcheonScraper()
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL not set.")
        return

    notifier = DiscordNotifier(webhook_url)

    # Scrape
    print("Fetching lectures...")
    lectures = scraper.get_lectures()
    
    if not lectures:
        print("No lectures found to test with.")
        return

    # Pick the first one
    test_lecture = lectures[0]
    print(f"Sending test notification for: {test_lecture['title']}")
    
    # Send
    notifier.send_notification(test_lecture)
    print("Test notification sent!")

if __name__ == "__main__":
    test_single_notification()
