import requests
from bs4 import BeautifulSoup
import time
import re
import os
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()

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
            if text:
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
    all_collected_messages.sort(key = lambda x: x['time'])
    print(f"\n🎉 Сбор окончен! Всего собрано уникальных постов: {len(all_collected_messages)}")
    return all_collected_messages


def analyze_with_gigachat(posts):
    if not posts:
        print("На странице канала не найдено текстовых постов для анализа.")

    print(f"\nФормируем общую ленту из {len(posts)} постов для GigaChat...")

    full_texts_to_analyze = ""
    for i, post in enumerate(posts, 1):
        full_texts_to_analyze += f"--- ПОСТ №{i} (Дата: {post['time']}) ---\n{post['text']}\n\n"

    promt = (
        "Ты профессиональный медиа-аналитик. Перед тобой текст последних постов из Telegram-канала. "
        "Сделай краткую, емкую и структурированную выжимку этих событий: "
        "выдели главные темы, ключевые тезисы автора и важные инсайды. "
        "Ответ напиши в красивом и понятном стиле, используя списки с буллитами."
        )
    MY_DIRECT_KEY = os.getenv("GIGACHAT_CREDINTIALS")

    if not MY_DIRECT_KEY:
        print("Ошибка. Переменная GIGACHAT_CREDINTIALS не найдена в файле .env!")
        return
    clean_MY_DIRECT_KEY = MY_DIRECT_KEY.strip()
    try:
        with GigaChat(credentials = clean_MY_DIRECT_KEY, scope = "GIGACHAT_API_PERS", verify_ssl_certs=False) as giga:
            user_message = f"{promt}\n\Вот посты:\n{full_texts_to_analyze}"

            print("Отправляем запрос в GigaChat (ждём ответ)...")
            response  = giga.chat(user_message)

            ai_text = response.choices[0].message.content

            print("\n ОТВЕТ GIGACHAT:")
            print("=" * 60)
            print(ai_text)
            print("=" * 60)
    except Exception as e:
        print(f"Ошибка GigaChat API: {e}")


if __name__ == "__main__":
    collected_post = parse_tg_history('dejavu041', pages_depth=1)

    analyze_with_gigachat(collected_post)