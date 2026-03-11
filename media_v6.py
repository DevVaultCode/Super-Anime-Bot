import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def decoder_logic(text):
    # JavaScript ke andar chhupi hui streaming files dhoondhna
    streams = re.findall(r'["\'](https?://[^"\']+\.(?:m3u8|mp4|mpd)[^"\']*)["\']', text)
    # Aise links jo specific 'file' ya 'sources' tag mein hote hain
    more_streams = re.findall(r'(?:file|source|src|url)["\']?\s*[:=]\s*["\'](https?://[^"\']+)["\']', text)
    return set(streams + more_streams)

def hunter_v6(url, depth=0):
    if depth > 5: return
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': url
    }

    try:
        prefix = "  " * depth
        print(f"{prefix}⚡ DECODER Scanning: {url}")
        
        res = requests.get(url, headers=headers, timeout=12)
        content = res.text
        
        # Asli links ki talaash
        found = decoder_logic(content)
        if found:
            print(f"\n{prefix}💎 [ULTIMATE STREAMS FOUND] 💎")
            for s in found:
                if "m3u8" in s or "mp4" in s:
                    print(f"{prefix}✅ {s}")
            print()

        # Players aur scripts ki list nikalna
        soup = BeautifulSoup(content, 'html.parser')
        targets = []
        
        # Iframes
        for f in soup.find_all('iframe'):
            if f.get('src'): targets.append(urljoin(url, f.get('src')))
        
        # Script tags (Inke andar aksar API endpoints hote hain)
        for s in soup.find_all('script'):
            if s.get('src'): 
                src = s.get('src')
                # Sirf vahi scripts jo player se related hain
                if any(x in src.lower() for x in ['player', 'core', 'bundle', 'cdn', 'video']):
                    targets.append(urljoin(url, src))

        for t in set(targets):
            if "google" not in t and "ads" not in t:
                hunter_v6(t, depth + 1)

    except:
        pass

print("\n" + "🌀"*15)
print("  MEDIA HUNTER V6: DECODER")
print("  (Deep JS Link Extraction)")
print("🌀"*15)

target = input("\nBhai, vahi ToonStream wala link dalo: ").strip()
hunter_v6(target)
