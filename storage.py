import json
import os

class Storage:
    FILE_PATH = 'data/lectures.json'

    def __init__(self):
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.FILE_PATH), exist_ok=True)

    def load_seen_lectures(self):
        if not os.path.exists(self.FILE_PATH):
            return []
        try:
            with open(self.FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def save_seen_lectures(self, lectures):
        # We store the list of lecture links or IDs to identify uniqueness
        # Storing the full object is fine too for simple comparison
        try:
            with open(self.FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(lectures, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def get_new_lectures(self, current_lectures):
        seen = self.load_seen_lectures()
        seen_links = {l['link'] for l in seen}
        
        new_lectures = []
        for lecture in current_lectures:
            if lecture['link'] not in seen_links:
                new_lectures.append(lecture)
        
        return new_lectures
