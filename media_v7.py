import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def brahmastra_scan(url, original_url, depth=0):
    if depth > 5: return
    
    # Powerful Headers jo block nahi hone denge
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': original_url,
        'Origin': 'https://as-cdn21.top',
        'Accept': '*/*'
    }

    try:
        indent = "  " * depth
        print(f"{indent}🔱 BRAHMASTRA Scanning: {url}")
        
        # Session ka use kar rahe hain cookies maintain karne ke liye
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=12)
        content = res.text
        
        # 🎯 MEGA REGEX: Har tarah ke stream links ke liye
        patterns = [
            r'["\'](https?://[^"\']+\.(?:m3u8|mp4|mpd)[^"\']*)["\']',
            r'file\s*:\s*["\']([^"\']+)["\']',
            r'url\s*:\s*["\']([^"\']+)["\']',
            r'src\s*:\s*["\']([^"\']+)["\']',
            r'["\'](https?://[^\s"\']+\/playlist\.m3u8[^\s"\']*)["\']'
        ]
        
        found_any = False
        for p in patterns:
            matches = re.findall(p, content)
            for s in set(matches):
                if "http" in s and not s.endswith(('.js', '.css', '.png')):
                    print(f"\n{indent}🌟 [SUCCESS] ASLI LINK MIL GAYA! 🌟")
                    print(f"{indent}👉 {s}")
                    print(f"{indent}💡 Tip: VLC Player mein chalao.\n")
                    found_any = True

        # Agli links dhoondhna (Iframes aur Scripts)
        soup = BeautifulSoup(content, 'html.parser')
        next_targets = []
        
        for f in soup.find_all(['iframe', 'script']):
            src = f.get('src')
            if src:
                full_src = urljoin(url, src)
                if any(x in full_src.lower() for x in ['player', 'video', 'stream', 'assets', 'scripts.php']):
                    next_targets.append(full_src)

        for t in set(next_targets):
            if t != url:
                brahmastra_scan(t, url, depth + 1)

    except:
        pass

print("\n" + "⚡"*15)
print("  MEDIA HUNTER V7: BRAHMASTRA")
print("  (Ultimate Stream Cracker)")
print("⚡"*15)

target = input("\nBhai, Tokyo Ghoul wala link dalo: ").strip()
brahmastra_scan(target, target)
