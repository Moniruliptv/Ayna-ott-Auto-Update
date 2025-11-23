import os
import json
import requests

# Stream API Base
STREAM_API = (
    "https://web.aynaott.com/api/player/streams?"
    "language=en&operator_id=1fb1b4c7-dbd9-469e-88a2-c207dc195869"
    "&device_id=582CC788D250CFADCA1B694D868288A7"
    "&density=1.25&client=browser&platform=web&os=windows&media_id="
)

# Required Headers
BASE_HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "connection": "keep-alive",
    "content-type": "application/json",
    "host": "web.aynaott.com",
    "referer": "https://web.aynaott.com/channels",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    "x-user-id": "78be6644-0a65-48ec-81a4-089ac65a2619"
}

def fetch_stream_url(media_id):
    HEADERS = BASE_HEADERS.copy()
    HEADERS["authorization"] = f"Bearer {os.getenv('AYNA_TOKEN')}"

    url = STREAM_API + media_id
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("❌ Error for:", media_id)
        return None

    try:
        data = r.json()
        return data["content"][0]["src"]["url"]
    except:
        return None


def load_single_json(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"📥 Loaded: {file_name} ({len(data)} channels)")
            return data
    except:
        print(f"⚠ Failed to load: {file_name}")
        return []


# -------------------------
# LOAD ALL 4 JSON FILES + REMOVE DUPLICATES
# -------------------------
def load_all_channels():
    files = [
        "Ayna_id.json",
        "Ayna_id_sm.json",
        "Ayna_id_ok.json",
        "ayna_exp.json"
    ]

    unique_channels = {}  # KEY = id

    for file in files:
        data = load_single_json(file)

        for ch in data:
            ch_id = ch["id"]

            if ch_id not in unique_channels:
                unique_channels[ch_id] = {
                    "id": ch_id,
                    "title": ch["title"],
                    "logo": ch["image"],
                    "category": ch.get("category")
                }

    print(f"\n🧹 Duplicate-removed channels: {len(unique_channels)}\n")

    return list(unique_channels.values())


def generate_m3u():
    channels = load_all_channels()

    m3u = "#EXTM3U\n\n"

    for ch in channels:
        print("➡ Fetching:", ch["title"])

        stream_url = fetch_stream_url(ch["id"])

        if not stream_url:
            print("⚠ Skip:", ch["title"])
            continue

        category = ch["category"] if ch["category"] else ""

        m3u += (
            f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" '
            f'group-title="{category}",{ch["title"]}\n'
            f"{stream_url}\n\n"
        )

    with open("AynaOTT.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

    print("\n✅ AynaOTT.m3u generated!")


if __name__ == "__main__":
    generate_m3u()
