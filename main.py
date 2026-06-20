import requests
from bs4 import BeautifulSoup
import time
import re

def parse_tg_history(channel_name, pages_depth = 3):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    }
    current_url = f"https://t.me/s/{channel_name}"
    all_collected_messages = []

    for page in range(1, pages_depth + 1):
        print(f"📡 Загружаем страницу {page} | URL: {current_url}")
        response = requests.get(current_url, headers=HEADERS)

        if response.status_code != 200:
            print("🤷‍♂️ Больше сообщений не найдено или сработала защита.")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_bubble')

        if not messages:
            print("🤷‍♂️ Больше сообщений не найдено или сработала защита.")
            break

        print(f"   -> Найдено {len(messages)} постов на этой странице.")

        for msg in messages:
            text_block = msg.find('div', class_='tgme_widget_message_text')
            text = text_block.get_text(separator='\n').strip() if text_block else "[Медиа или репост]"

            time_block = msg.find('time', class_='time')
            post_time = time_block.get('datetime') if time_block else "Неизвестно"
            
            all_collected_messages.append({"time": post_time, "text": text})
        
        first_msg = messages[0]

        date_link = first_msg.find('a', class_='tgme_widget_message_date')
        if date_link and 'href' in date_link.attrs:
            href = date_link['href']
            match = re.search(r'/(\d+)$', href)
            if match:
                first_msg_id = match.group(1)
                
                current_url = f"https://t.me/s/{channel_name}?before={first_msg_id}"
            else:
                print("❌ Не удалось определить ID поста для листания.")
                break
        else:
            print("❌ Не нашли ссылку на дату поста.")
            break

        time.sleep(2)
        print("-" * 30)
    all_collected_messages.sort(key = lambda x: x['time'])
    print(f"\n🎉 Сбор окончен! Всего собрано уникальных постов: {len(all_collected_messages)}")
    print("=" * 50)
    
    for i, msg in enumerate(all_collected_messages, 1):
        print(f"Собранный пост №{i} | Время: {msg['time']}")
        print(msg['text'])
        print("." * 40)

if __name__ == "__main__":
    parse_tg_history('pekagame', pages_depth=3)