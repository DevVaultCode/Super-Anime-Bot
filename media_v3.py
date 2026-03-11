import requests
import re
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def deep_hunt(target_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
        'Referer': target_url
    }
    
    try:
        print(f"\n🔍 Scanning: {target_url}")
        res = requests.get(target_url, headers=headers, timeout=15)
        html = res.text
        
        # 1. Direct Stream dhoondhna (.m3u8 ya .mp4)
        streams = re.findall(r'(https?://[^\s"\']+\.(?:m3u8|mp4|mpd))', html)
        
        # 2. Hidden JavaScript Variables mein stream dhoondhna
        js_streams = re.findall(r'file["\']\s*:\s*["\'](https?://[^"\']+)["\']', html)
        
        all_streams = set(streams + js_streams)
        
        if all_streams:
            print("🔥 --- FOUND DIRECT STREAMS ---")
            for s in all_streams:
                print(f"[✔] {s}")
            return True
        
        # 3. Agar kuch nahi mila, toh Iframes (Players) check karo
        soup = BeautifulSoup(html, 'html.parser')
        iframes = [urljoin(target_url, i.get('src')) for i in soup.find_all('iframe') if i.get('src')]
        
        if iframes:
            print(f"📦 Found {len(iframes)} Players. Deep diving into them...")
            for player in iframes:
                # Recursive call: Player ke andar jaao
                deep_hunt(player)
            return True
            
        return False

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return False

print("\n" + "="*45)
print("   🚀 MEDIA HUNTER V3: DEEP RECURSIVE 🚀")
print("="*45)
url = input("\nBhai, Movie/Series link dalo: ").strip()
if not deep_hunt(url):
    print("\n❌ Asli stream nahi mili. Shayad site protected hai!")
