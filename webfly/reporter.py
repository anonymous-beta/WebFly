"""
WebFly Report Generator
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from .utils import sanitize_filename


class Reporter:
    def __init__(self, results: List[Dict], vulnerabilities: List[Dict] = None, target: str = ""):
        self.results = results
        self.vulnerabilities = vulnerabilities or []
        self.target = target
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def to_json(self, path: str = None) -> str:
        data = {
            "target": self.target,
            "generated": self.timestamp,
            "results": self.results,
            "vulnerabilities": self.vulnerabilities,
        }
        content = json.dumps(data, indent=2)
        if path:
            Path(path).write_text(content, encoding="utf-8")
        return content

    def to_csv(self, path: str) -> None:
        if not self.results:
            return
        keys = self.results[0].keys()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.results)

    def to_txt(self, path: str) -> None:
        lines = [
            f"WebFly Report - {self.target}",
            f"Generated: {self.timestamp}",
            "=" * 60,
            "",
        ]
        for r in self.results:
            lines.append(f"[{r.get('status')}] {r.get('url')}  ({r.get('size')} bytes)")
        if self.vulnerabilities:
            lines.append("\n--- Vulnerabilities ---")
            for v in self.vulnerabilities:
                lines.append(f"[{v.get('confidence').upper()}] {v.get('type')} → {v.get('url')}")
                lines.append(f"    Evidence: {v.get('evidence')}")
        Path(path).write_text("\n".join(lines), encoding="utf-8")

    def to_html(self, path: str) -> None:
        rows = "".join(
            f"<tr><td>{r.get('status')}</td><td>{r.get('url')}</td>"
            f"<td>{r.get('size')}</td><td>{r.get('title', '')}</td></tr>"
            for r in self.results
        )
        vulns = "".join(
            f"<div class='vuln'><b>{v.get('type')}</b> ({v.get('confidence')})<br>"
            f"{v.get('url')}<br><small>{v.get('evidence')}</small></div>"
            for v in self.vulnerabilities
        )
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>WebFly Report</title>
<style>
body{{font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}}
table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #30363d;padding:8px}}
th{{background:#161b22}} .vuln{{background:#21262d;margin:8px 0;padding:10px;border-radius:6px}}
</style></head><body>
<h1>WebFly Report</h1>
<p>Target: {self.target}<br>Generated: {self.timestamp}</p>
<h2>Results ({len(self.results)})</h2>
<table><tr><th>Status</th><th>URL</th><th>Size</th><th>Title</th></tr>
{rows}</table>
<h2>Vulnerabilities ({len(self.vulnerabilities)})</h2>
{vulns or '<p>None found</p>'}
</body></html>"""
        Path(path).write_text(html, encoding="utf-8")

    def save(self, output: str, fmt: str = "json"):
        base = sanitize_filename(output)
        os.makedirs(os.path.dirname(base) or ".", exist_ok=True)
        if fmt == "json" or fmt == "all":
            self.to_json(f"{base}.json")
        if fmt == "csv" or fmt == "all":
            self.to_csv(f"{base}.csv")
        if fmt == "txt" or fmt == "all":
            self.to_txt(f"{base}.txt")
        if fmt == "html" or fmt == "all":
            self.to_html(f"{base}.html")
