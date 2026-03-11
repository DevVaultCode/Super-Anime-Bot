import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def phantom_scanner(url, depth=0):
    if depth > 3: # Zyada andar tak na ghuse
        return
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
        'Referer': url
    }

    try:
        print(f"{'  ' * depth}🔍 Scanning [{depth}]: {url}")
        res = requests.get(url, headers=headers, timeout=10)
        content = res.text
        
        # 1. HLS/DASH/MP4 Direct Patterns
        patterns = [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'https?://[^\s"\']+\.mp4[^\s"\']*',
            r'file["\']\s*:\s*["\'](https?://[^"\']+)["\']',
            r'sources\s*:\s*\[\s*\{\s*file\s*:\s*["\'](https?://[^"\']+)["\']'
        ]
        
        found = []
        for p in patterns:
            found.extend(re.findall(p, content))

        if found:
            print(f"{'  ' * depth}🔥 --- FOUND POTENTIAL STREAMS ---")
            for s in set(found):
                print(f"{'  ' * depth}[✔] {s}")
            return True

        # 2. Iframe Extraction
        soup = BeautifulSoup(content, 'html.parser')
        iframes = [urljoin(url, i.get('src')) for i in soup.find_all('iframe') if i.get('src')]
        
        # 3. JavaScript Hidden Redirects
        js_redirects = re.findall(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', content)
        iframes.extend([urljoin(url, r) for r in js_redirects])

        for player in set(iframes):
            if "ads" not in player.lower(): # Ads ko skip karne ke liye
                phantom_scanner(player, depth + 1)

    except Exception as e:
        pass

print("\n" + "👻"*15)
print("  MEDIA HUNTER V4: PHANTOM")
print("  (Deep JavaScript Analysis)")
print("👻"*15)

target = input("\nBhai, link dalo: ").strip()
phantom_scanner(target)
