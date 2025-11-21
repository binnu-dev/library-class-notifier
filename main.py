
import os
from dotenv import load_dotenv
from scraper import LibraryScraper
from notifier import DiscordNotifier
from storage import Storage

# List of libraries to monitor
LIBRARIES = [
    {"name": "청천도서관", "url": "https://www.bppl.or.kr/chungcheon/menu/10400/program/30022/lectureList.do"},
    {"name": "부개도서관", "url": "https://www.bppl.or.kr/bugae/menu/10624/program/30022/lectureList.do"},
    {"name": "삼산도서관", "url": "https://www.bppl.or.kr/samsan/menu/10210/program/30022/lectureList.do"},
    {"name": "부평기적의도서관", "url": "https://www.bppl.or.kr/miracle/menu/10305/program/30022/lectureList.do"},
    {"name": "갈산도서관", "url": "https://www.bppl.or.kr/galsan/menu/10495/program/30022/lectureList.do"},
    {"name": "부개어린이도서관", "url": "https://www.bppl.or.kr/bugaech/menu/11222/program/30022/lectureList.do"}
]

# Load environment variables
load_dotenv()

def main():
    print("Starting Library Class Notifier...")
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL is not set.")
        return

    notifier = DiscordNotifier(webhook_url)
    storage = Storage()
    seen_lectures = storage.load_seen_lectures()
    
    new_lectures_count = 0
    
    for lib_config in LIBRARIES:
        print(f"Checking {lib_config['name']}...")
        scraper = LibraryScraper(lib_config['name'], lib_config['url'])
        lectures = scraper.get_lectures()
        
        for lecture in lectures:
            # Use link as unique identifier
            lecture_id = lecture['link']
            
            if lecture_id not in seen_lectures:
                print(f"New lecture found in {lib_config['name']}: {lecture['title']}")
                notifier.send_notification(lecture)
                seen_lectures.append(lecture_id)
                new_lectures_count += 1
            else:
                # print(f"Already seen: {lecture['title']}")
                pass
    
    if new_lectures_count > 0:
        print(f"Sent {new_lectures_count} new notifications.")
        storage.save_seen_lectures(seen_lectures)
    else:
        print("No new lectures found.")

if __name__ == "__main__":
    main()
