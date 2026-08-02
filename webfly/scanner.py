"""
WebFly Core Async Scanner
"""

import asyncio
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Callable, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

from .utils import load_wordlist, generate_id, random_user_agent


@dataclass
class ScanResult:
    url: str
    status: int = 0
    size: int = 0
    title: str = ""
    response_time: float = 0.0
    is_directory: bool = False
    is_interesting: bool = False
    redirect: str = ""
    error: str = ""
    content_type: str = ""

    def to_dict(self):
        return asdict(self)


class Scanner:
    INTERESTING_KEYWORDS = [
        "admin", "backup", "config", "db", "sql", "secret", "key", "password",
        "login", "dashboard", "api", "debug", "test", "staging", "dev",
        ".env", ".git", "phpinfo", "wp-admin", "actuator", "swagger"
    ]

    def __init__(
        self,
        target: str,
        wordlist: List[str] = None,
        threads: int = 50,
        timeout: int = 10,
        extensions: List[str] = None,
        status_codes: List[int] = None,
        recursive: bool = False,
        max_depth: int = 3,
        follow_redirects: bool = True,
        verify_ssl: bool = False,
        headers: Dict[str, str] = None,
        proxy: str = None,
        on_result: Callable = None,
    ):
        self.target = target.rstrip("/") + "/"
        self.wordlist = wordlist or []
        self.threads = max(1, threads)
        self.timeout = timeout
        self.extensions = extensions or [""]
        self.status_codes = status_codes or [200, 204, 301, 302, 307, 401, 403, 405, 500]
        self.recursive = recursive
        self.max_depth = max_depth
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.headers = headers or {}
        self.proxy = proxy
        self.on_result = on_result

        self.results: List[ScanResult] = []
        self.found_dirs: Set[str] = set()
        self.tested: Set[str] = set()
        self._stop = False
        self.stats = {"tested": 0, "found": 0, "errors": 0}

    def stop(self):
        self._stop = True

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> ScanResult:
        start = time.time()
        result = ScanResult(url=url)
        try:
            async with session.get(
                url,
                allow_redirects=self.follow_redirects,
                proxy=self.proxy,
                ssl=self.verify_ssl if self.verify_ssl else False,
            ) as resp:
                body = await resp.read()
                result.status = resp.status
                result.size = len(body)
                result.response_time = time.time() - start
                result.content_type = resp.headers.get("Content-Type", "")
                result.redirect = str(resp.url) if str(resp.url) != url else ""

                # crude title extraction
                try:
                    text = body.decode("utf-8", errors="ignore")
                    if "<title>" in text.lower():
                        start_t = text.lower().find("<title>") + 7
                        end_t = text.lower().find("</title>", start_t)
                        if end_t > start_t:
                            result.title = text[start_t:end_t].strip()[:120]
                except Exception:
                    pass

                # heuristics
                if url.endswith("/") or "text/html" in result.content_type:
                    result.is_directory = True
                lower = url.lower()
                if any(k in lower for k in self.INTERESTING_KEYWORDS):
                    result.is_interesting = True

        except Exception as e:
            result.error = str(e)[:200]
            self.stats["errors"] += 1

        return result

    async def _worker(self, session: aiohttp.ClientSession, queue: asyncio.Queue):
        while not self._stop:
            try:
                url, depth = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if queue.empty():
                    break
                continue

            if url in self.tested:
                queue.task_done()
                continue

            self.tested.add(url)
            result = await self._fetch(session, url)
            self.stats["tested"] += 1

            if result.status in self.status_codes and not result.error:
                self.results.append(result)
                self.stats["found"] += 1
                if self.on_result:
                    self.on_result(result)

                if self.recursive and depth < self.max_depth and result.is_directory:
                    base = result.url if result.url.endswith("/") else result.url + "/"
                    if base not in self.found_dirs:
                        self.found_dirs.add(base)
                        for word in self.wordlist:
                            for ext in self.extensions:
                                path = word + ext
                                new_url = urljoin(base, path)
                                if new_url not in self.tested:
                                    await queue.put((new_url, depth + 1))

            queue.task_done()

    async def run(self) -> List[ScanResult]:
        self._stop = False
        queue: asyncio.Queue = asyncio.Queue()

        # seed
        for word in self.wordlist:
            for ext in self.extensions:
                path = word + ext
                url = urljoin(self.target, path)
                await queue.put((url, 0))

        timeout = ClientTimeout(total=self.timeout)
        connector = TCPConnector(limit=self.threads, ssl=False)

        headers = {"User-Agent": random_user_agent()}
        headers.update(self.headers)

        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector, headers=headers
        ) as session:
            workers = [
                asyncio.create_task(self._worker(session, queue))
                for _ in range(self.threads)
            ]
            await queue.join()
            self._stop = True
            await asyncio.gather(*workers, return_exceptions=True)

        return self.results

    def get_nodes(self) -> Dict:
        """Build simple node/link structure for the graph."""
        nodes = [{"id": "root", "url": self.target, "type": "root", "status": 200}]
        links = []
        seen = {"root"}

        for r in self.results:
            nid = generate_id(r.url)
            if nid in seen:
                continue
            seen.add(nid)

            ntype = "directory" if r.is_directory else "file"
            if r.is_interesting:
                ntype = "interesting"
            elif r.status in (401, 403):
                ntype = "protected"
            elif r.status in (301, 302, 307):
                ntype = "redirect"
            elif r.status >= 500:
                ntype = "error"

            nodes.append({
                "id": nid,
                "url": r.url,
                "type": ntype,
                "status": r.status,
                "size": r.size,
                "title": r.title,
            })
            links.append({"source": "root", "target": nid})

        return {"nodes": nodes, "links": links}
