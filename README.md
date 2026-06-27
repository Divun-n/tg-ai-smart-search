# Умный AI поиск по Telegram-каналам

Скрипт позволяет скачивать историю постов из любого публичного Telegram-канала и использовать нейросеть GigaChat от Сбера для поиска постов на конкретную тему. Скрипт выдает текст постов и прямые кликабельные ссылки на них.

## Как запустить проект:

1. Склонируйте репозиторий.
2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Для Windows: .venv\Scripts\activate
   pip install requests beautifulsoup4 python-dotenv gigachat