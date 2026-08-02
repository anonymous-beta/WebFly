"""
WebFly FastAPI Server + WebSocket
"""

import asyncio
import uuid
from typing import Dict, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .scanner import Scanner
from .crawler import Crawler
from .exploiter import VulnScanner
from .reporter import Reporter
from .utils import load_wordlist, is_valid_url

app = FastAPI(title="WebFly", version="1.0.0")

WEB_DIR = Path(__file__).parent.parent / "web"
WORDLIST_PATH = Path(__file__).parent.parent / "wordlists" / "common.txt"

# Active scans
active_scans: Dict[str, dict] = {}
connected_clients: List[WebSocket] = []


class ScanConfig(BaseModel):
    target: str
    threads: int = 50
    timeout: int = 10
    max_depth: int = 3
    extensions: str = None
    status_filter: str = "200,204,301,302,307,401,403,405,500"
    recursive: bool = True
    follow_redirects: bool = True
    enable_crawler: bool = False
    enable_vuln_scan: bool = False
    enable_exploit: bool = False


async def broadcast(data: dict):
    for ws in connected_clients[:]:
        try:
            await ws.send_json(data)
        except Exception:
            if ws in connected_clients:
                connected_clients.remove(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)


@app.post("/api/scan")
async def start_scan(config: ScanConfig):
    if not is_valid_url(config.target):
        raise HTTPException(400, "Invalid target URL")

    scan_id = str(uuid.uuid4())[:8]
    wordlist = load_wordlist(str(WORDLIST_PATH))
    if not wordlist:
        wordlist = ["admin", "login", "dashboard", "api", "config", "backup", "test", "dev"]

    extensions = [""]
    if config.extensions:
        extensions = [e.strip() if e.startswith(".") else f".{e.strip()}" for e in config.extensions.split(",")]
        extensions.append("")

    status_codes = [int(s) for s in config.status_filter.split(",") if s.strip().isdigit()]

    async def run_scan():
        def on_result(result):
            asyncio.create_task(broadcast({
                "type": "scan_progress",
                "data": result.to_dict()
            }))

        scanner = Scanner(
            target=config.target,
            wordlist=wordlist,
            threads=config.threads,
            timeout=config.timeout,
            extensions=extensions,
            status_codes=status_codes,
            recursive=config.recursive,
            max_depth=config.max_depth,
            follow_redirects=config.follow_redirects,
            on_result=on_result,
        )
        active_scans[scan_id] = {"scanner": scanner, "status": "running"}

        results = await scanner.run()
        nodes = scanner.get_nodes()

        vulns = []
        if config.enable_vuln_scan or config.enable_exploit:
            urls = [r.url for r in results if r.status == 200]
            vs = VulnScanner(timeout=config.timeout)
            vulns = await vs.scan_urls(urls)
            await broadcast({"type": "vuln_scan_complete", "data": {"vulnerabilities": vulns}})

        active_scans[scan_id]["status"] = "completed"
        active_scans[scan_id]["results"] = [r.to_dict() for r in results]
        active_scans[scan_id]["nodes"] = nodes
        active_scans[scan_id]["vulnerabilities"] = vulns

        await broadcast({
            "type": "scan_complete",
            "data": {
                "scan_id": scan_id,
                "nodes": nodes,
                "stats": scanner.stats,
                "vulnerabilities": vulns,
            }
        })

    asyncio.create_task(run_scan())
    return {"scan_id": scan_id, "status": "started"}


@app.post("/api/scan/{scan_id}/stop")
async def stop_scan(scan_id: str):
    if scan_id in active_scans:
        active_scans[scan_id]["scanner"].stop()
        active_scans[scan_id]["status"] = "stopped"
        return {"status": "stopped"}
    raise HTTPException(404, "Scan not found")


@app.get("/api/report/{scan_id}")
async def get_report(scan_id: str, format: str = "json"):
    if scan_id not in active_scans or "results" not in active_scans[scan_id]:
        raise HTTPException(404, "Report not ready")

    data = active_scans[scan_id]
    reporter = Reporter(
        results=data["results"],
        vulnerabilities=data.get("vulnerabilities", []),
        target=data.get("target", ""),
    )

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp:
        if format == "json":
            Path(tmp.name).write_text(reporter.to_json())
        elif format == "csv":
            reporter.to_csv(tmp.name)
        elif format == "html":
            reporter.to_html(tmp.name)
        else:
            reporter.to_txt(tmp.name)
        return FileResponse(tmp.name, filename=f"webfly_report.{format}")


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>WebFly frontend not found</h1>")


if (WEB_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")
if (WEB_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(WEB_DIR / "js")), name="js")
