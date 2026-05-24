import requests
import sys
import re
import json
import base64
from colorama import Fore, init
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

init(autoreset=True)

# =========================
# GLOBAL STORAGE
# =========================
visited_urls = set()

# =========================
# MEDIA EXTRACTION ENGINE
# =========================
def extract_media(text):

    patterns = [

        r'https?://[^\s"\']+\.m3u8',
        r'https?://[^\s"\']+\.mp4',
        r'https?://[^\s"\']+\.mpd',
        r'https?://[^\s"\']+/master\.m3u8',
        r'https?://[^\s"\']+\.ts',
        r'https?://[^\s"\']+\.mkv',
        r'https?://[^\s"\']+\.webm',
        r'https?://[^\s"\']+\.mp3',
        r'https?://[^\s"\']+/playlist.*?\.m3u8',
        r'blob:https?://[^\s"\']+',

        # Hidden API patterns
        r'https?://[^\s"\']+/api/[^\s"\']+',
        r'https?://[^\s"\']+/v\d+/[^\s"\']+',

        # Encoded URLs
        r'https?%3A%2F%2F[^\s"\']+'
    ]

    found = []

    for pattern in patterns:

        matches = re.findall(pattern, text)

        for m in matches:

            decoded = unquote(m)

            found.append(decoded)

    return list(set(found))


# =========================
# SAVE TXT
# =========================
def save_results(data):

    try:

        with open("found_media.txt", "w", encoding="utf-8") as f:

            for item in data:
                f.write(item + "\n")

        print(f"\n{Fore.GREEN}[+] TXT saved")

    except Exception as e:

        print(f"{Fore.RED}[!] TXT save failed: {e}")


# =========================
# SAVE JSON
# =========================
def save_json(data):

    try:

        with open("found_media.json", "w", encoding="utf-8") as f:

            json.dump(data, f, indent=4)

        print(f"{Fore.GREEN}[+] JSON saved")

    except Exception as e:

        print(f"{Fore.RED}[!] JSON save failed: {e}")


# =========================
# VERIFY STREAM
# =========================
def verify_link(session, link, headers):

    try:

        r = session.head(link, headers=headers, timeout=10)

        return {
            "url": link,
            "status": r.status_code,
            "type": r.headers.get("Content-Type", "Unknown")
        }

    except:
        return None


# =========================
# SCAN URL
# =========================
def scan_url(session, url, headers):

    if url in visited_urls:
        return []

    visited_urls.add(url)

    try:

        r = session.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        links = extract_media(r.text)

        # JS Scan
        for script in soup.find_all("script"):

            script_text = str(script)

            links.extend(extract_media(script_text))

        # Video Scan
        for tag in soup.find_all(["video", "source"]):

            src = tag.get("src")

            if src:
                links.append(urljoin(url, src))

        return links

    except:
        return []


# =========================
# MAIN TRACKER
# =========================
def track_url(target_url):

    print(f"\n{Fore.CYAN}[*] SUPER SONIC TRACE STARTED")
    print(f"{Fore.YELLOW}{target_url}")

    session = requests.Session()

    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {

        "User-Agent": "Mozilla/5.0",
        "Referer": target_url,
        "Origin": urlparse(target_url).netloc,
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:

        response = session.get(
            target_url,
            headers=headers,
            allow_redirects=True,
            timeout=20
        )

        # =========================
        # REDIRECT CHAIN
        # =========================
        print(f"\n{Fore.MAGENTA}[+] Redirect Chain:")

        if response.history:

            for i, r in enumerate(response.history):

                print(f" {i+1}. {r.status_code} -> {r.url}")

        else:

            print(" No redirects found")

        # =========================
        # BASIC INFO
        # =========================
        print(f"\n{Fore.GREEN}[+] Final URL:")
        print(response.url)

        print(f"\n{Fore.BLUE}[+] Status:")
        print(response.status_code)

        print(f"\n{Fore.CYAN}[+] Server:")
        print(response.headers.get("Server", "Unknown"))

        print(f"\n{Fore.CYAN}[+] CDN:")
        print(response.headers.get("CF-Cache-Status", "No CDN"))

        print(f"\n{Fore.CYAN}[+] Content-Type:")
        print(response.headers.get("Content-Type", "Unknown"))

        print(f"\n{Fore.CYAN}[+] Response Size:")
        print(f"{len(response.text)} bytes")

        # =========================
        # ROBOTS + SITEMAP
        # =========================
        robots = urljoin(target_url, "/robots.txt")
        sitemap = urljoin(target_url, "/sitemap.xml")

        print(f"\n{Fore.YELLOW}[+] Robots:")
        print(robots)

        print(f"\n{Fore.YELLOW}[+] Sitemap:")
        print(sitemap)

        # =========================
        # COOKIE SCAN
        # =========================
        print(f"\n{Fore.YELLOW}[+] Cookies:")

        if session.cookies:

            for cookie in session.cookies:

                print(f" {cookie.name} = {cookie.value}")

        else:

            print(" No cookies")

        # =========================
        # MAIN HTML SCAN
        # =========================
        print(f"\n{Fore.YELLOW}[*] Turbo scanning...")

        soup = BeautifulSoup(response.text, "html.parser")

        all_links = []

        all_links.extend(extract_media(response.text))

        # =========================
        # IFRAME SCAN
        # =========================
        iframe_urls = []

        for iframe in soup.find_all("iframe"):

            src = iframe.get("src")

            if src:

                full = urljoin(target_url, src)

                iframe_urls.append(full)

                print(f"{Fore.MAGENTA}[IFRAME] {full}")

        # =========================
        # MULTI THREAD SCAN
        # =========================
        with ThreadPoolExecutor(max_workers=10) as executor:

            futures = []

            for url in iframe_urls:

                futures.append(
                    executor.submit(
                        scan_url,
                        session,
                        url,
                        headers
                    )
                )

            for f in futures:

                result = f.result()

                all_links.extend(result)

        # =========================
        # VERIFY LINKS
        # =========================
        final_links = list(set(all_links))

        verified = []

        print(f"\n{Fore.YELLOW}[*] Verifying links...")

        with ThreadPoolExecutor(max_workers=20) as executor:

            futures = []

            for link in final_links:

                futures.append(
                    executor.submit(
                        verify_link,
                        session,
                        link,
                        headers
                    )
                )

            for f in futures:

                r = f.result()

                if r:
                    verified.append(r)

        # =========================
        # OUTPUT
        # =========================
        if verified:

            print(f"\n{Fore.GREEN}[!] VERIFIED MEDIA LINKS:\n")

            for item in verified:

                url = item["url"]

                if ".m3u8" in url:

                    print(f"{Fore.YELLOW}[M3U8] {url}")

                elif ".mp4" in url:

                    print(f"{Fore.GREEN}[MP4]  {url}")

                else:

                    print(f"{Fore.CYAN}[LINK] {url}")

                print(f"      STATUS: {item['status']}")
                print(f"      TYPE  : {item['type']}\n")

            save_results([x["url"] for x in verified])

            save_json(verified)

        else:

            print(f"{Fore.RED}[!] No media found")

    except KeyboardInterrupt:

        print(f"\n{Fore.RED}[!] Interrupted")

    except Exception as e:

        print(f"{Fore.RED}[!] Error: {e}")


# =========================
# MAIN
# =========================
def main():

    print(f"""{Fore.GREEN}

================================================
        SUPER SONIC URL TRACE TOOL
================================================

""")

    url = input("Paste URL: ").strip()

    if not url.startswith("http"):

        print(f"{Fore.RED}[!] Invalid URL")

        sys.exit()

    track_url(url)


if __name__ == "__main__":
    main()
