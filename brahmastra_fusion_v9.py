#!/usr/bin/env python3
"""
🔱 BRAHMASTRA ULTIMATE FUSION v9.0 🔱
Complete Integration of All Features + CloudScraper Bypass + Async Support
The Absolute Ultimate Media & Link Extractor with Everything Combined
"""

import requests
import re
import json
import csv
import socket
import time
import asyncio
import aiohttp
import logging
import os
import gzip
import threading
import sys
from datetime import datetime
from colorama import Fore, Style, init
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sqlite3

# Try to import cloudscraper for Cloudflare bypass
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    print(f"{Fore.YELLOW}[!] Install cloudscraper: pip install cloudscraper")

init(autoreset=True)
console = Console()

# =========================
# CONFIGURATION & LOGGING
# =========================
CONFIG = {
    "timeout": 15,
    "max_workers": 35,
    "max_retries": 3,
    "max_depth": 6,
    "verify_ssl": False,
    "use_proxies": False,
    "enable_async": True,
    "enable_cloudflare_bypass": True,
    "enable_hls_decrypt": True,
    "enable_db_export": True,
    "detect_quality": True,
    "cdn_analysis": True,
    "subtitle_extraction": True
}

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=log_dir / f"brahmastra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create reports directory
reports_dir = Path("reports")
reports_dir.mkdir(exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# =========================
# GLOBAL STORAGE
# =========================
class BrahmastraStorage:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.found_streams: Dict[str, List] = {
            "m3u8_streams": [],
            "mp4_direct": [],
            "mpd_dash": [],
            "api_endpoints": [],
            "embedded_players": [],
            "subtitles": [],
            "hls_keys": [],
            "all_links": []
        }
        self.domains: Set[str] = set()
        self.verified_links: List[Dict] = []
        self.cdn_analysis: Dict[str, Dict] = {}
        self.redirect_chain: List[str] = []
        self.cookies: Dict = {}
        self.server_info: Dict = {}

storage = BrahmastraStorage()

# =========================
# SESSION BUILDERS
# =========================
def create_standard_session() -> requests.Session:
    """Create standard requests session with retries."""
    session = requests.Session()
    retry_strategy = Retry(
        total=CONFIG["max_retries"],
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def create_cloudflare_session():
    """Create Cloudflare bypass session using cloudscraper."""
    if HAS_CLOUDSCRAPER and CONFIG["enable_cloudflare_bypass"]:
        try:
            return cloudscraper.create_scraper()
        except:
            pass
    return create_standard_session()

def get_headers(referer: str = None) -> Dict:
    """Get advanced headers."""
    headers = {
        "User-Agent": USER_AGENTS[int(time.time()) % len(USER_AGENTS)],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    if referer:
        headers["Referer"] = referer
    return headers

# =========================
# DNS LOOKUP
# =========================
def dns_info(url: str) -> Dict:
    """Get DNS information."""
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        ip = socket.gethostbyname(domain)
        storage.domains.add(domain)
        
        info = {
            "domain": domain,
            "ip": ip,
            "resolved": True
        }
        
        print(f"{Fore.MAGENTA}[DNS] {domain} -> {ip}")
        logger.info(f"DNS: {domain} -> {ip}")
        
        return info
    except Exception as e:
        logger.debug(f"DNS lookup failed: {e}")
        return {"domain": url, "resolved": False}

# =========================
# EXTRACTION ENGINES
# =========================
def extract_media(text: str) -> List[str]:
    """Extract media URLs with multiple patterns."""
    patterns = [
        r'https?://[^\s"\']+\.m3u8[^\s"\']*',
        r'https?://[^\s"\']+\.mp4[^\s"\']*',
        r'https?://[^\s"\']+\.mpd[^\s"\']*',
        r'https?://[^\s"\']+\.ts[^\s"\']*',
        r'https?://[^\s"\']+\.mkv[^\s"\']*',
        r'https?://[^\s"\']+\.webm[^\s"\']*',
        r'blob:https?://[^\s"\']*',
        r'https?://[^\s"\']+/api/[^\s"\']*',
        r'https?://[^\s"\']+/stream[^\s"\']*',
        r'https?://[^\s"\']+/video[^\s"\']*',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            decoded = unquote(m)
            if decoded not in found and len(decoded) > 10:
                found.append(decoded)
    
    return found

def extract_json_objects(text: str) -> List[Dict]:
    """Extract JSON objects."""
    json_objects = []
    patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
        r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, (dict, list)):
                    json_objects.append({
                        "type": type(parsed).__name__,
                        "size": len(str(parsed)),
                        "preview": str(parsed)[:150]
                    })
            except:
                pass
    
    return json_objects

def extract_api_endpoints(text: str) -> List[str]:
    """Extract API endpoints."""
    patterns = [
        r'(https?://[^\s"\']+/api/[^\s"\']*)',
        r'(https?://[^\s"\']+/v\d+/[^\s"\']*)',
        r'(https?://[^\s"\']+/graphql[^\s"\']*)',
        r'(https?://[^\s"\']+/rest/[^\s"\']*)',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)
    
    return list(set(found))

def extract_subtitles(html: str, base_url: str) -> List[Dict]:
    """Extract subtitle files."""
    subtitles = []
    soup = BeautifulSoup(html, 'html.parser')
    
    for track in soup.find_all('track'):
        if track.get('src'):
            subtitles.append({
                "url": urljoin(base_url, track.get('src')),
                "language": track.get('srclang', 'unknown'),
                "kind": track.get('kind', 'subtitles')
            })
    
    # Regex patterns
    patterns = [
        r'(https?://[^\s"\']+\.(?:vtt|srt|ass|ssa)[^\s"\']*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            subtitles.append({
                "url": match,
                "language": "auto-detected",
                "kind": "subtitles"
            })
    
    return list({s["url"]: s for s in subtitles}.values())

def extract_iframes(html: str, base_url: str) -> List[str]:
    """Extract iframe sources."""
    iframes = []
    soup = BeautifulSoup(html, 'html.parser')
    
    for iframe in soup.find_all('iframe'):
        if iframe.get('src'):
            full_src = urljoin(base_url, iframe.get('src'))
            iframes.append(full_src)
    
    return iframes

# =========================
# VERIFICATION
# =========================
def verify_link(session, link: str, headers: Dict) -> Optional[Dict]:
    """Verify link accessibility."""
    try:
        response = session.head(
            link,
            headers=headers,
            timeout=CONFIG["timeout"],
            allow_redirects=True,
            verify=CONFIG["verify_ssl"]
        )
        
        return {
            "url": link,
            "status": response.status_code,
            "type": response.headers.get("Content-Type", "Unknown"),
            "accessible": response.status_code < 400,
            "server": response.headers.get("Server", "Unknown"),
            "size": response.headers.get("Content-Length", "Unknown")
        }
    except:
        return None

# =========================
# ASYNC SCANNER
# =========================
async def async_scan_url(session: aiohttp.ClientSession, url: str, headers: Dict) -> List[str]:
    """Async URL scanning."""
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=CONFIG["timeout"]), ssl=False) as response:
            if response.status == 200:
                text = await response.text()
                return extract_media(text)
    except:
        pass
    return []

# =========================
# RECURSIVE SCANNER
# =========================
def scan_recursive(url: str, session, headers: Dict, depth: int = 0):
    """Recursively scan URL and embedded players."""
    
    if depth > CONFIG["max_depth"] or url in storage.visited_urls:
        return
    
    storage.visited_urls.add(url)
    indent = "  " * depth
    
    try:
        print(f"{indent}{Fore.CYAN}[{depth}] 🔍 {url[:70]}")
        
        response = session.get(url, headers=headers, timeout=CONFIG["timeout"], verify=CONFIG["verify_ssl"])
        
        if response.status_code != 200:
            return
        
        html = response.text
        
        # Extract media
        media = extract_media(html)
        storage.found_streams["m3u8_streams"].extend([m for m in media if ".m3u8" in m])
        storage.found_streams["mp4_direct"].extend([m for m in media if ".mp4" in m])
        storage.found_streams["all_links"].extend(media)
        
        if media:
            print(f"{indent}{Fore.GREEN}[✓] Found {len(media)} media items")
        
        # Extract APIs
        apis = extract_api_endpoints(html)
        storage.found_streams["api_endpoints"].extend(apis)
        
        # Extract subtitles
        subs = extract_subtitles(html, url)
        storage.found_streams["subtitles"].extend(subs)
        
        # Extract and scan iframes
        iframes = extract_iframes(html, url)
        for iframe in iframes[:3]:  # Limit to 3 to avoid infinite loops
            if "ads" not in iframe.lower() and "google" not in iframe.lower():
                scan_recursive(iframe, session, headers, depth + 1)
    
    except Exception as e:
        logger.debug(f"Error scanning {url}: {e}")

# =========================
# RICH TABLE OUTPUT
# =========================
def print_results_table(verified_links: List[Dict]):
    """Print results in rich table format."""
    table = Table(title="🎬 Verified Media Links")
    table.add_column("Type", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Content-Type", style="magenta")
    
    for link in verified_links[:20]:
        url = link["url"]
        status = "✓" if link["accessible"] else "✗"
        
        if ".m3u8" in url:
            link_type = "[M3U8]"
            color = "yellow"
        elif ".mp4" in url:
            link_type = "[MP4]"
            color = "green"
        elif ".mpd" in url:
            link_type = "[DASH]"
            color = "cyan"
        else:
            link_type = "[URL]"
            color = "blue"
        
        table.add_row(
            link_type,
            url[:60] + "..." if len(url) > 60 else url,
            status,
            link["type"]
        )
    
    console.print(table)

# =========================
# CSV EXPORT
# =========================
def export_csv(filename: str, data: List[Dict]):
    """Export results to CSV."""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if not data:
                return
            
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"{Fore.GREEN}[✓] CSV exported: {filename}")
    except Exception as e:
        print(f"{Fore.RED}[!] CSV export failed: {e}")

# =========================
# DATABASE EXPORT
# =========================
def export_database(db_file: str, verified_links: List[Dict], target_url: str):
    """Export to SQLite database."""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                status INTEGER,
                type TEXT,
                accessible BOOLEAN,
                server TEXT,
                source_url TEXT,
                extracted_at TIMESTAMP
            )
        ''')
        
        for link in verified_links:
            cursor.execute('''
                INSERT OR IGNORE INTO media 
                (url, status, type, accessible, server, source_url, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                link["url"],
                link["status"],
                link["type"],
                link["accessible"],
                link["server"],
                target_url,
                datetime.now()
            ))
        
        conn.commit()
        conn.close()
        print(f"{Fore.GREEN}[✓] Database exported: {db_file}")
    except Exception as e:
        print(f"{Fore.RED}[!] DB export failed: {e}")

# =========================
# MAIN TRACKER FUNCTION
# =========================
def track_url(target_url: str):
    """Main tracking function - Combined everything."""
    
    print(f"\n{Fore.CYAN}{'='*100}")
    print(f"{Fore.CYAN}🔱 BRAHMASTRA ULTIMATE FUSION v9.0")
    print(f"{Fore.CYAN}{'='*100}\n")
    
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Normalize URL
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url
    
    print(f"{Fore.YELLOW}[>] Target: {target_url}\n")
    
    # DNS Lookup
    dns_info(target_url)
    
    # Create session (with Cloudflare bypass if available)
    print(f"{Fore.CYAN}[*] Creating session...")
    session = create_cloudflare_session()
    headers = get_headers(target_url)
    
    try:
        # Initial fetch
        print(f"{Fore.CYAN}[*] Fetching page...")
        response = session.get(
            target_url,
            headers=headers,
            allow_redirects=True,
            timeout=CONFIG["timeout"],
            verify=CONFIG["verify_ssl"]
        )
        
        # Redirect chain
        print(f"\n{Fore.MAGENTA}[+] Redirect Chain:")
        storage.redirect_chain.append(response.url)
        if response.history:
            for i, r in enumerate(response.history, 1):
                print(f"    {i}. {r.status_code} -> {r.url}")
                storage.redirect_chain.append(r.url)
        else:
            print(f"    No redirects")
        
        # Server info
        print(f"\n{Fore.BLUE}[+] Server Info:")
        storage.server_info = {
            "final_url": response.url,
            "status": response.status_code,
            "server": response.headers.get("Server", "Unknown"),
            "cdn": response.headers.get("CF-Cache-Status", "No CDN"),
            "content_type": response.headers.get("Content-Type", "Unknown"),
            "content_length": len(response.text)
        }
        print(f"    Status: {response.status_code}")
        print(f"    Server: {storage.server_info['server']}")
        print(f"    CDN: {storage.server_info['cdn']}")
        print(f"    Size: {storage.server_info['content_length']} bytes")
        
        # Cookies
        if session.cookies:
            print(f"\n{Fore.YELLOW}[+] Cookies: {len(session.cookies)}")
            for cookie in session.cookies:
                print(f"    {cookie.name} = {cookie.value[:50]}...")
                storage.cookies[cookie.name] = cookie.value
        
        # Deep scan
        print(f"\n{Fore.CYAN}[*] Starting deep recursive scan...")
        scan_recursive(target_url, session, headers)
        
        # Verify links
        print(f"\n{Fore.CYAN}[*] Verifying {len(storage.found_streams['all_links'])} links...")
        
        with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            futures = []
            for link in storage.found_streams["all_links"][:100]:
                futures.append(executor.submit(verify_link, session, link, headers))
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Verifying", colour="green"):
                result = future.result()
                if result and result["accessible"]:
                    storage.verified_links.append(result)
        
        elapsed = time.time() - start_time
        
        # Summary
        print(f"\n{Fore.GREEN}{'='*100}")
        print(f"{Fore.GREEN}📊 EXTRACTION SUMMARY")
        print(f"{Fore.GREEN}{'='*100}\n")
        
        print(f"{Fore.CYAN}📈 Results:")
        print(f"   {Fore.YELLOW}M3U8 Streams: {len(storage.found_streams['m3u8_streams'])}")
        print(f"   {Fore.GREEN}MP4 Direct: {len(storage.found_streams['mp4_direct'])}")
        print(f"   {Fore.BLUE}API Endpoints: {len(storage.found_streams['api_endpoints'])}")
        print(f"   {Fore.MAGENTA}Subtitles: {len(storage.found_streams['subtitles'])}")
        print(f"   {Fore.GREEN}✓ Verified: {len(storage.verified_links)}")
        print(f"   {Fore.YELLOW}⏱ Time: {elapsed:.2f}s\n")
        
        # Display results
        if storage.verified_links:
            print_results_table(storage.verified_links)
        
        # Save results
        print(f"\n{Fore.CYAN}[*] Saving results...")
        
        domain = urlparse(target_url).netloc.replace("www.", "")
        
        # JSON
        json_file = reports_dir / f"brahmastra_{domain}_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": storage.server_info,
                "redirect_chain": storage.redirect_chain,
                "cookies": storage.cookies,
                "results": {
                    "m3u8": storage.found_streams['m3u8_streams'],
                    "mp4": storage.found_streams['mp4_direct'],
                    "apis": storage.found_streams['api_endpoints'],
                    "subtitles": storage.found_streams['subtitles'],
                    "verified": storage.verified_links
                }
            }, f, indent=2, default=str)
        print(f"{Fore.GREEN}[✓] JSON: {json_file}")
        
        # TXT
        txt_file = reports_dir / f"brahmastra_{domain}_{timestamp}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"BRAHMASTRA REPORT\n")
            f.write(f"Target: {target_url}\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Time: {elapsed:.2f}s\n\n")
            
            f.write(f"VERIFIED MEDIA ({len(storage.verified_links)}):\n")
            for link in storage.verified_links:
                f.write(f"{link['url']}\n")
        
        print(f"{Fore.GREEN}[✓] TXT: {txt_file}")
        
        # CSV
        csv_file = reports_dir / f"brahmastra_{domain}_{timestamp}.csv"
        export_csv(str(csv_file), storage.verified_links)
        
        # Database
        db_file = reports_dir / f"brahmastra_{domain}_{timestamp}.db"
        export_database(str(db_file), storage.verified_links, target_url)
        
        logger.info(f"Extraction complete: {len(storage.verified_links)} verified links in {elapsed:.2f}s")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Interrupted by user")
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        session.close()

# =========================
# MENU SYSTEM
# =========================
def banner():
    """Display banner."""
    console.print(Panel.fit(
        "[bold cyan]🔱 BRAHMASTRA ULTIMATE FUSION v9.0 🔱[/bold cyan]\n"
        "[green]Complete Media Extractor + CloudScraper Bypass[/green]\n"
        "[yellow]Features: M3U8 • MP4 • APIs • Subtitles • Async • DB Export[/yellow]",
        border_style="cyan"
    ))

def menu_loop():
    """Main menu loop."""
    while True:
        try:
            banner()
            
            print(f"\n{Fore.CYAN}[1]{Fore.RESET} Scan Single URL")
            print(f"{Fore.YELLOW}[2]{Fore.RESET} Scan Multiple URLs")
            print(f"{Fore.RED}[3]{Fore.RESET} Exit\n")
            
            choice = input(f"{Fore.CYAN}Select Option: {Fore.WHITE}").strip()
            
            if choice == "1":
                url = input(f"{Fore.YELLOW}Enter URL: {Fore.WHITE}").strip()
                if url:
                    track_url(url)
                    input(f"\n{Fore.CYAN}Press Enter to continue...")
            
            elif choice == "2":
                url_file = input(f"{Fore.YELLOW}Enter URL file path: {Fore.WHITE}").strip()
                if os.path.exists(url_file):
                    with open(url_file, 'r') as f:
                        urls = [line.strip() for line in f if line.strip()]
                    
                    for url in urls:
                        print(f"\n{Fore.CYAN}Processing: {url}")
                        track_url(url)
                        time.sleep(2)
                else:
                    print(f"{Fore.RED}[!] File not found")
            
            elif choice == "3":
                print(f"{Fore.GREEN}Goodbye!")
                sys.exit(0)
        
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}[!] Interrupted")
            sys.exit(0)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    menu_loop()
