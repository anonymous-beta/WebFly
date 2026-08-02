"""
WebFly CLI
"""

import argparse
import asyncio
import sys
from pathlib import Path

from colorama import init, Fore, Style

from . import __version__
from .scanner import Scanner
from .crawler import Crawler
from .exploiter import VulnScanner
from .reporter import Reporter
from .utils import load_wordlist, is_valid_url
from .server import app
import uvicorn

init(autoreset=True)


def banner():
    print(f"""
{Fore.RED}
██╗    ██╗███████╗██████╗ ███████╗██╗  ██╗   ██╗
██║    ██║██╔════╝██╔══██╗██╔════╝██║  ╚██╗ ██╔╝
██║ █╗ ██║█████╗  ██████╔╝█████╗  ██║   ╚████╔╝ 
██║███╗██║██╔══╝  ██╔══██╗██╔══╝  ██║    ╚██╔╝  
╚███╔███╔╝███████╗██████╔╝██║     ███████╗██║   
 ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═╝     ╚══════╝╚═╝   
{Style.RESET_ALL}
  WebFly v{__version__} — Aggressive Web Recon Framework
  Created by Anonymous-beta & Victor410fer
""")


def main():
    parser = argparse.ArgumentParser(description="WebFly — Aggressive Web Reconnaissance Framework")
    parser.add_argument("-u", "--url", help="Target URL")
    parser.add_argument("-l", "--url-list", help="File with target URLs")
    parser.add_argument("-w", "--wordlist", help="Wordlist path")
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("-e", "--extensions", help="Comma-separated extensions")
    parser.add_argument("-r", "--recursive", action="store_true")
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--status-codes", default="200,204,301,302,307,401,403,405,500")
    parser.add_argument("--crawl", action="store_true")
    parser.add_argument("--vuln-scan", action="store_true")
    parser.add_argument("--exploit", action="store_true")
    parser.add_argument("-o", "--output", help="Output file prefix")
    parser.add_argument("--format", default="txt", choices=["txt", "json", "csv", "html", "all"])
    parser.add_argument("--server", action="store_true", help="Start Web GUI")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.server:
        banner()
        print(f"[*] Starting WebFly GUI on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        return

    if not args.url and not args.url_list:
        banner()
        parser.print_help()
        sys.exit(1)

    if not args.quiet:
        banner()

    targets = []
    if args.url:
        targets.append(args.url)
    if args.url_list:
        targets.extend(Path(args.url_list).read_text().splitlines())

    wordlist_path = args.wordlist or str(Path(__file__).parent.parent / "wordlists" / "common.txt")
    wordlist = load_wordlist(wordlist_path)
    if not wordlist:
        wordlist = ["admin", "login", "dashboard", "api", "config", "backup", "test", "dev", "uploads", "assets"]

    extensions = [""]
    if args.extensions:
        extensions = [e.strip() if e.startswith(".") else f".{e.strip()}" for e in args.extensions.split(",")]
        extensions.append("")

    status_codes = [int(s) for s in args.status_codes.split(",") if s.strip().isdigit()]

    async def run():
        all_results = []
        all_vulns = []

        for target in targets:
            target = target.strip()
            if not is_valid_url(target):
                print(f"{Fore.RED}[!] Invalid URL: {target}")
                continue

            print(f"{Fore.CYAN}[*] Scanning {target}")

            def on_result(r):
                if not args.quiet:
                    color = Fore.GREEN if r.status in (200, 204) else Fore.YELLOW
                    print(f"{color}[{r.status}] {r.url} ({r.size} bytes)")

            scanner = Scanner(
                target=target,
                wordlist=wordlist,
                threads=args.threads,
                timeout=args.timeout,
                extensions=extensions,
                status_codes=status_codes,
                recursive=args.recursive,
                max_depth=args.max_depth,
                on_result=on_result,
            )
            results = await scanner.run()
            all_results.extend([r.to_dict() for r in results])

            if args.crawl:
                print(f"{Fore.CYAN}[*] Crawling...")
                crawler = Crawler(target, max_depth=args.max_depth)
                crawl_data = await crawler.run()
                print(f"[+] Crawled {crawl_data['pages_crawled']} pages")

            if args.vuln_scan or args.exploit:
                print(f"{Fore.CYAN}[*] Vulnerability scanning...")
                urls = [r.url for r in results if r.status == 200]
                vs = VulnScanner()
                vulns = await vs.scan_urls(urls)
                all_vulns.extend(vulns)
                for v in vulns:
                    print(f"{Fore.RED}[VULN] {v['type']} → {v['url']}")

        if args.output:
            reporter = Reporter(all_results, all_vulns, targets[0] if targets else "")
            reporter.save(args.output, args.format)
            print(f"{Fore.GREEN}[+] Report saved to {args.output}.*")

    asyncio.run(run())


if __name__ == "__main__":
    main()
