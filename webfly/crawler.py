"""
WebFly Smart Crawler
"""

import asyncio
import re
from typing import List, Set, Dict
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from .utils import random_user_agent


class Crawler:
    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 3,
        same_domain: bool = True,
        timeout: int = 10,
        verify_ssl: bool = False,
    ):
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.same_domain = same_domain
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.visited: Set[str] = set()
        self.found_urls: List[str] = []
        self.api_endpoints: List[str] = []
        self.forms: List[Dict] = []
        self._domain = urlparse(start_url).netloc

    def _is_same_domain(self, url: str) -> bool:
        return urlparse(url).netloc == self._domain

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        try:
            async with session.get(url, ssl=self.verify_ssl if self.verify_ssl else False) as resp:
                if "text/html" in resp.headers.get("Content-Type", ""):
                    return await resp.text(errors="ignore")
        except Exception:
            pass
        return ""

    def _extract(self, base: str, html: str):
        soup = BeautifulSoup(html, "lxml")
        links = set()

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            full = urljoin(base, href)
            if full.startswith("http"):
                links.add(full.split("#")[0])

        for tag in soup.find_all(["script", "link", "img"], src=True):
            src = tag.get("src") or tag.get("href")
            if src:
                full = urljoin(base, src)
                if full.startswith("http"):
                    links.add(full.split("#")[0])

        # crude API discovery
        for match in re.findall(r'["\'](/api/[^"\']+)["\']', html):
            full = urljoin(base, match)
            self.api_endpoints.append(full)

        for form in soup.find_all("form"):
            action = form.get("action") or base
            method = (form.get("method") or "GET").upper()
            inputs = [
                {"name": i.get("name"), "type": i.get("type", "text")}
                for i in form.find_all("input") if i.get("name")
            ]
            self.forms.append({
                "action": urljoin(base, action),
                "method": method,
                "inputs": inputs,
            })

        return links

    async def run(self) -> Dict:
        queue = asyncio.Queue()
        await queue.put((self.start_url, 0))

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        headers = {"User-Agent": random_user_agent()}

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            while not queue.empty() and len(self.visited) < self.max_pages:
                url, depth = await queue.get()
                if url in self.visited or depth > self.max_depth:
                    continue
                if self.same_domain and not self._is_same_domain(url):
                    continue

                self.visited.add(url)
                self.found_urls.append(url)

                html = await self._fetch(session, url)
                if not html:
                    continue

                links = self._extract(url, html)
                for link in links:
                    if link not in self.visited:
                        await queue.put((link, depth + 1))

        return {
            "urls": self.found_urls,
            "api_endpoints": list(set(self.api_endpoints)),
            "forms": self.forms,
            "pages_crawled": len(self.visited),
      }
