import pandas as pd
import requests
from bs4 import BeautifulSoup
import time 

MAX_PAGES     = 10      # максимум страниц (None = все ~1991)
DELAY_SECONDS = 1.5     # пауза между запросами
OUTPUT_FILE   = "mashina_kg_cars.csv"
# nth page. = https://mashina.kg/search/passenger?page=N
URL = 'https://mashina.kg/search/passenger'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def fetch_html(url: str,tries:int = 3)->str:
    for attempt in range (1, tries+1):
        try:
            response = SESSION.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print (f"Try {attempt}/{tries} was not succesful for {url}: {e}")
            if attempt == tries:
                return None
            time.sleep(attempt**2)

# получили url теперь его обрабатываем
def get_total_pages(soup):
    buttons = soup.find_all('button', class_='pagination_button')
    numbers = []
    for i in buttons:
        try:
            num = int(i.text)
            numbers.append(num)
        except:
            pass
    return max(numbers)
# узнали сколько страниц
# я в шоке
def parse_card(card):
    url = 'https://mashina.kg'+card['href']
    title = card.find('h3').text.strip()
    city = card.find('span',class_='text-white text-sm leading-5 truncate').text.strip()
    img_tag = card.find('img')
    price_usd = '0'
    price = card.find('span',class_='font-bold text-xs leading-4 text-text-secondary whitespace-nowrap').text
    clean_kgs = price.replace('⃀', '')
    digits_only = "".join([char for char in clean_kgs if char.isdigit()])
    price_kgs = int(digits_only) if digits_only else 0
    engine = ''
    transmission= ''
    year_mil_tg = card.find('span',class_='text-xs leading-4 whitespace-nowrap shrink-0')
    if year_mil_tg:
        raw = year_mil_tg.text
        if '/' in raw:
            parts = raw.split('/')
            year_digits = "".join([char for char in parts[0] if char.isdigit()])
            year = int(year_digits) if year_digits else None

            mileage_raw = parts[1].lower()
            is_miles = 'mile' in mileage_raw or 'мил' in mileage_raw
            
            mileage_digits = "".join([char for char in mileage_raw if char.isdigit()])
            
            if mileage_digits:
                val = int(mileage_digits)
                milleage_km = round(val * 1.60924) if is_miles else val
            else:
                milleage_km = None

    if img_tag:
        image_url = img_tag.get('src')
    else:
        image_url = 'no image'

    all_spans = card.find_all('span')

    for s in all_spans:
        text = s.text
        if '$' in text:
            clean_usd = text.replace('$', '')
            digits_only = "".join([char for char in clean_usd if char.isdigit()])
            price_usd = int(digits_only) if digits_only else 0
            
        elif 'л.' in text and '/' in text:
            eng_parts = text.split('/')
            engine = eng_parts[0].strip()
            transmission = eng_parts[1].strip()
    print(title)
    return {
    "url": url,
    "title": title,
    'city':city,
    'price_usd':price_usd,
    'price_kgs':price_kgs,
    'year':year,
    'milleage_km':milleage_km,
    'engine':engine,
    'transmission':transmission,
    'image_url':image_url
    }

def parse_page(html):
    soup = BeautifulSoup(html,'lxml')
    cards = soup.find_all('a',class_='group block cursor-pointer')
    page_info =[]
    for card in cards:
        try:
            info = parse_card(card)
            page_info.append(info)
        except Exception as e:
            print(f"Error: {e} ocurred")
    return page_info


def fetch_all_pages(session):
    all_cars = []
    html_main = fetch_html(URL)
    soup = BeautifulSoup(html_main,'lxml')
    pages = get_total_pages(soup)
    limit = min(MAX_PAGES,pages)
    for i in range (1,limit+1):
        url = f'https://mashina.kg/search/passenger?page={i}'
        parsed_html=fetch_html(url)
        cars=parse_page(parsed_html)
        all_cars.extend(cars)
        time.sleep(DELAY_SECONDS)
    return all_cars



def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename,index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} cars to {filename}")

def main():
    data = fetch_all_pages(SESSION)
    if data:
        # extend and append difference is essential !!!
        #do not confuse list with dictionary
        print("ТИП ДАННЫХ:", type(data))
        print("ПЕРВЫЙ ЭЛЕМЕНТ:", data[0])
    if data:
        save_to_csv(data,OUTPUT_FILE)
        print('DONE!')
    else:
        print('something is wrong')

if __name__ == "__main__":
    main()