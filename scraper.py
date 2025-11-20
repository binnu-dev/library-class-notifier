import requests
from bs4 import BeautifulSoup
import re

class CheongcheonScraper:
    BASE_URL = "https://www.bppl.or.kr/chungcheon/menu/10400/program/30022/lectureList.do"
    DETAIL_BASE_URL = "https://www.bppl.or.kr/chungcheon/menu/10400/program/30022/lectureDetail.do?lectureIdx="

    def get_lectures(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.BASE_URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            lectures = []
            rows = soup.select('#board_tbody > tr')
            
            for row in rows:
                try:
                    # Title
                    title_elem = row.select_one('td.title dt.title a span')
                    title = title_elem.text.strip() if title_elem else "No Title"
                    
                    # Link (extract lectureIdx)
                    link_elem = row.select_one('td.title dt.title a')
                    link = "N/A"
                    if link_elem and 'onclick' in link_elem.attrs:
                        onclick = link_elem['onclick']
                        match = re.search(r"fnDetail\('(\d+)'\)", onclick)
                        if match:
                            link = self.DETAIL_BASE_URL + match.group(1)
                    
                    # Date
                    date_elem = row.select_one('td.center.td4')
                    date = date_elem.get_text(strip=True) if date_elem else "N/A"
                    
                    # Status
                    status_elem = row.select_one('td.center.last.td6 b.stat')
                    status = status_elem.text.strip() if status_elem else "N/A"
                    
                    lectures.append({
                        'title': title,
                        'link': link,
                        'date': date,
                        'status': status
                    })
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
                    
            return lectures
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

if __name__ == "__main__":
    scraper = CheongcheonScraper()
    lectures = scraper.get_lectures()
    for l in lectures:
        print(l)
