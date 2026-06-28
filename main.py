import requests
from bs4 import BeautifulSoup
import time
import re
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def format_time(time_str):
    try:
        if '+' in time_str:
            time_str = time_str.split('+')[0]
        dt = datetime.fromisoformat(time_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return time_str

def extract_channel_name(url):
    pattern = r'(?:https?://)?(?:www\.)?t\.me/([a-zA-Z0-9_]+)'
    
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else:
        return None

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
        count = 1
        for msg in messages:
            text_block = msg.find('div', class_='tgme_widget_message_text')
            text = text_block.get_text(separator='\n').strip() if text_block else "[Медиа или репост]"
            if text:
                time_block = msg.find('time', class_='time')
                post_time = time_block.get('datetime') if time_block else "Неизвестно"

                post_id = "0"
                date_link = msg.find('a', class_='tgme_widget_message_date')
                if date_link and 'href' in date_link.attrs:
                    id_match = re.search(r'/(\d+)$', date_link['href'])
                    if id_match:
                        post_id = id_match.group(1)

                all_collected_messages.append({
                    "count": count, 
                    "time": post_time, 
                    "text": text,
                    "id": post_id
                })
                count += 1
        
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
    all_collected_messages.sort(key = lambda x: x['time'])
    print(f"\n🎉 Сбор окончен! Всего собрано уникальных постов: {len(all_collected_messages)}")
    return all_collected_messages


def analyze_with_ai(posts, topic):
    # Название функции оставил прежним, чтобы вам не пришлось менять вызовы в __main__
    if not posts:
        print("На странице канала не найдено текстовых постов для анализа.")
        return None

    print(f"\nФормируем общую ленту из {len(posts)} постов для ИИ...")

    full_texts_to_analyze = ""
    for post in posts:
        full_texts_to_analyze += f"--- ПОСТ №{post['count']} (Дата: {post['time']}) ---\n{post['text']}\n\n"

    prompt = (
        f'Ты профессиональный медиа-аналитик. Перед тобой текст последних постов из Telegram-канала.\n'
        f'Найди посты, связанные с темой "{topic}", и верни ТОЛЬКО НОМЕРА этих постов через запятую в одну строчку.\n'
        f'Пример ответа: 3, 7, 12'
    )
    
    API_KEY = os.getenv("OPENROUTER_API_KEY")

    if not API_KEY:
        print("Ошибка. Переменная OPENROUTER_API_KEY не найдена в файле .env!")
        return None

    # Настройки для запроса к OpenRouter
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY.strip()}",
        "Content-Type": "application/json", 
        "HTTP-Referer": "https://github.com/", 
        "X-Title": "TG AI Smart Search"
    }
    
    data = {
        "model": "openrouter/free",  # Автоматически выберет лучшую бесплатную модель (Llama 3, Qwen и др.)
        "messages": [
            {"role": "user", "content": f"{prompt}\n\nВот посты:\n{full_texts_to_analyze}"}
        ]
    }

    try:
        print("🚀 Отправляем запрос в ИИ через OpenRouter (ждём ответ)...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result['choices'][0]['message']['content']
            
            print("\n СЫРОЙ ОТВЕТ ИИ:")
            print("=" * 60)
            print(ai_text)
            print("=" * 60)
            return ai_text
        else:
            print(f"❌ Ошибка API: Код {response.status_code} | {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при отправке запроса: {e}")
        return None


if __name__ == "__main__":
    print("Умный AI тг поиск")
    while True:
        try:
            tg_url = str(input("Вставьте ссылку на тг канал: "))
            topic = str(input("Введите тему постов для поиска: "))
            pages_depth = int(input("Введите глубину просмотра постов (20~ постов * n): "))
            break
        except Exception as e:
            print(f"Произошла ошибка ({e}) попробуйте ещё раз.")
            continue
    channel_name = extract_channel_name(tg_url)
    if not channel_name:
        print("❌ Не удалось извлечь имя канала из ссылки!")
        exit()
    collected_post = parse_tg_history(channel_name, pages_depth = pages_depth)

    ai_response = analyze_with_ai(collected_post, topic)
    if ai_response:
        numbers = re.findall(r'\d+', ai_response)
        if numbers:
                print("\n📊 НАЙДЕННЫЕ ПОСТЫ ПО ТЕМЕ:")
                for num_str in numbers:
                    post_num = int(num_str)
                    if 0 <= post_num - 1 < len(collected_post):
                        post = collected_post[post_num - 1]
                        
                        post_link = f"https://t.me/{channel_name}/{post['id']}" if post['id'] != "0" else "Ссылка недоступна"
                        print("-" * 60)
                        print(f"пост №{post_num} | время: {format_time(post['time'])} | 🔗 Ссылка на пост: {post_link}")
                        print("-" * 60)
                        print(post['text'])
                        print()
                    else:
                        print(f"⚠️ Пост №{post_num} не найден в собранных данных")
        else:
                print("ℹ️ GigaChat не нашёл постов по указанной теме.")
    else:
            print("❌ Не удалось получить ответ от GigaChat.")


    