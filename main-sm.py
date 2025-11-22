import os
import requests
import json

# API URL
url = "https://web.aynaott.com/api/player/categories?language=en&operator_id=1fb1b4c7-dbd9-469e-88a2-c207dc195869&device_id=582CC788D250CFADCA1B694D868288A7&density=1.25&client=browser&platform=mobile&os=ios&page=1&per_page=10&display_on_main_screen=1&content_page=1&content_per_page=20"

# Headers
headers = {
    "accept": "*/*",
    "authorization": f"Bearer {os.getenv('AYNA_TOKEN')}",
    "user-agent": "Mozilla/5.0"
}

def fetch_api_and_save():
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            # JSON ফাইলে লেখা
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print("✅ data.json ফাইল তৈরি হয়ে গেছে!")
        else:
            print("❌ Error:", response.status_code, response.text)

    except Exception as e:
        print("❌ Exception:", e)

if __name__ == "__main__":
    fetch_api_and_save()
