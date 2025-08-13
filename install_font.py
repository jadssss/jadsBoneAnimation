import requests
import os

url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"  # Ссылка на Roboto Regular
font_path = "default_font.ttf"

if os.path.exists(font_path):
    print("Шрифт уже установлен.")
else:
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(font_path, 'wb') as f:
            f.write(response.content)
        print(f"Шрифт скачан и сохранён как {font_path}")
    except Exception as e:
        print(f"Ошибка скачивания: {e}")