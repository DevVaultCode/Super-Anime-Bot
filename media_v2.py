import requests
import re
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def ultra_extractor(target_url):
    print(f"\n🚀 Scanning Target: {target_url}")
    print("🔍 Deep scanning for hidden streams, M3U8, and encoded links...\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36'
    }
    
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        found_links = {
            "Direct Video": set(),
            "Streaming (M3U8/MPD)": set(),
            "Embedded Players": set(),
            "Encoded/Hidden": set()
        }

        # 1. RegEx se HLS (.m3u8) aur DASH (.mpd) dhoondhna (Sabse powerful tarika)
        streams = re.findall(r'(https?://[^\s"\']+\.(?:m3u8|mpd|mp4|mkv))', html_content)
        for s in streams:
            if ".m3u8" in s or ".mpd" in s:
                found_links["Streaming (M3U8/MPD)"].add(s)
            else:
                found_links["Direct Video"].add(s)

        # 2. iFrames (Players) scan karna
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                found_links["Embedded Players"].add(urljoin(target_url, src))

        # 3. Base64 Encoded links ki talaash
        # Aksar links 'aHR0c...' se shuru hote hain
        encoded_stuff = re.findall(r'(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', html_content)
        for item in encoded_stuff:
            try:
                decoded = base64.b64decode(item).decode('utf-8')
                if decoded.startswith('http'):
                    found_links["Encoded/Hidden"].add(decoded)
            except:
                continue

        # --- RESULTS DISPLAY ---
        for category, links in found_links.items():
            if links:
                print(f"🔥 --- {category.upper()} ---")
                for link in links:
                    print(f"[+] {link}")
                print()

        if not any(found_links.values()):
            print("❌ Kuch nahi mila bhai. Site zyada secure hai!")

    except Exception as e:
        print(f"⚠️ Error: {e}")

# EXECUTION
if __name__ == "__main__":
    print("\n" + "="*40)
    print("   🌐 ULTRA MEDIA EXTRACTOR V2 🌐")
    print("="*40)
    url = input("\nBhai, Movie/Series ka link yahan dalo: ").strip()
    ultra_extractor(url)
