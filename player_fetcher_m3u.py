import os
import requests
import json

# Stream API Base URL
STREAM_API = (
    "https://web.aynaott.com/api/player/streams?"
    "language=en&operator_id=1fb1b4c7-dbd9-469e-88a2-c207dc195869"
    "&device_id=582CC788D250CFADCA1B694D868288A7"
    "&density=1.25&client=browser&platform=web&os=windows&media_id="
)

# Browser Headers (required)
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
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    "x-user-id": "78be6644-0a65-48ec-81a4-089ac65a2619"
}


def fetch_stream_url(media_id):
    """Fetch stream URL → save JSON → return stream URL"""
    HEADERS = BASE_HEADERS.copy()
    HEADERS["authorization"] = f"Bearer {os.getenv('AYNA_TOKEN')}"

    url = STREAM_API + media_id
    print(f"\n📡 Fetching stream for: {media_id}")

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("❌ Stream API Error:", r.text)
        return None

    try:
        data = r.json()
    except:
        print("❌ JSON Decode Failed")
        return None

    # Save raw JSON
    os.makedirs("streams", exist_ok=True)
    with open(f"streams/{media_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # Extract stream URL
    try:
        stream_url = data["content"][0]["src"]["url"]
        print("✔ Stream URL:", stream_url)
        return stream_url
    except:
        print("❌ Stream URL Not Found")
        return None


def generate_m3u(channel_list):
    """Generate M3U using media_id + name + logo"""
    print("\n🎬 Generating playlist.m3u ...")

    m3u = "#EXTM3U\n\n"

    for ch in channel_list:
        media_id = ch["id"]
        title = ch["title"]
        logo = ch["logo"]

        stream_url = fetch_stream_url(media_id)

        if not stream_url:
            print(f"⚠️ No stream for {title}")
            continue

        m3u += (
            f'#EXTINF:-1 tvg-id="{media_id}" tvg-logo="{logo}" '
            f'group-title="Live",{title}\n{stream_url}\n\n'
        )

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

    print("✅ playlist.m3u created successfully!")


if __name__ == "__main__":
    # Example channel list
    channel_list = [
        {
            "id": "9046949b-9847-4b5d-96c1-e82b0734444b",
            "title": "ATN Bangla",
            "logo": "https://s3.aynaott.com/storage/85e20cee815e7ee532133ad7ae4ac571"
        }
    ]

    generate_m3u(channel_list)
