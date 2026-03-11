import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def titan_scanner(url, depth=0):
    if depth > 4: return # Deep scanning limit
    
    # Asli Browser jaisa dikhne ke liye headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://google.com/',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        prefix = "  " * depth
        print(f"{prefix}🛡️ TITAN Scanning [{depth}]: {url}")
        
        # Session use kar rahe hain taaki Cookies save rahein
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        # Agar redirect hua hai toh naya URL print karo
        if res.url != url:
            print(f"{prefix}➡️ Redirected to: {res.url}")
        
        content = res.text
        
        # 1. Sabse Powerful Regex (m3u8, mp4, streams)
        stream_patterns = [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'https?://[^\s"\']+\.mp4[^\s"\']*',
            r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'file:\s*["\']([^"\']+)["\']',
            r'source:\s*["\']([^"\']+)["\']'
        ]
        
        found_streams = []
        for p in stream_patterns:
            matches = re.findall(p, content)
            found_streams.extend(matches)

        if found_streams:
            print(f"\n{prefix}🔥 [TITAN FOUND STREAMS] 🔥")
            for s in set(found_streams):
                if "http" in s:
                    print(f"{prefix}✅ {s}")
            print()

        # 2. Iframe & Hidden Player Extraction
        soup = BeautifulSoup(content, 'html.parser')
        players = []
        
        # Iframes
        for iframe in soup.find_all('iframe'):
            if iframe.get('src'): players.append(urljoin(res.url, iframe.get('src')))
        
        # Hidden Scripts (Jo direct link contain karte hain)
        scripts = re.findall(r'src=["\']([^"\']+)["\']', content)
        for s in scripts:
            if "player" in s.lower() or "video" in s.lower() or "embed" in s.lower():
                players.append(urljoin(res.url, s))

        # 3. Recursive Scan
        for p in set(players):
            if "ads" not in p.lower() and "google" not in p.lower():
                titan_scanner(p, depth + 1)

    except Exception as e:
        print(f"{prefix}⚠️ Error: {str(e)[:50]}")

print("\n" + "🔱"*15)
print("  MEDIA HUNTER V5: TITAN")
print("  (The Ultimate Bypasser)")
print("🔱"*15)

target = input("\nBhai, link yahan dalo: ").strip()
titan_scanner(target)
