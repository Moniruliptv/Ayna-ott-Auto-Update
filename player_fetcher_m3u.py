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

    data = r.json()

    try:
        return data["content"][0]["src"]["url"]
    except:
        return None



def load_channels_from_datajson():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    channels = []

    for cat in data["content"]["data"]:
        if "items" not in cat:
            continue

        for ch in cat["items"]["data"]:
            channels.append({
                "id": ch["id"],
                "title": ch["title"],
                "logo": ch["image"]
            })

    return channels



def generate_m3u():
    channels = load_channels_from_datajson()

    print(f"🔎 Total channels found: {len(channels)}")

    m3u = "#EXTM3U\n\n"

    os.makedirs("streams", exist_ok=True)

    for ch in channels:
        print("➡ Fetching:", ch["title"])

        stream_url = fetch_stream_url(ch["id"])

        if not stream_url:
            print("⚠ Skip:", ch["title"])
            continue

        m3u += (
            f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" '
            f'group-title="Live",{ch["title"]}\n'
            f"{stream_url}\n\n"
        )

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

    print("✅ playlist.m3u generated!")


if __name__ == "__main__":
    generate_m3u()
