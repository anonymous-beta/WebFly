<p align="center">
  <img src="logo.png" alt="WebFly Logo" width="400">
</p>

<h1 align="center">WebFly</h1>

<p align="center">
  <b>Aggressive Web Reconnaissance & Exploitation Framework</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/version-1.0.0-red.svg" alt="Version">
</p>

<p align="center">
  <i>Created by <b>Anonymous-beta</b> & <b>Victor410fer</b></i>
</p>

---

## Features

- **Aggressive Directory Brute-forcing** — High-performance async scanning with customizable wordlists
- **Interactive Node Graph** — Visualize target structure with D3.js force-directed graphs
- **Smart Crawler** — Intelligent web crawling with JavaScript analysis and API endpoint discovery
- **Vulnerability Scanner** — Built-in detection for SQLi, XSS, LFI, RCE, SSRF, Open Redirect
- **Exploitation Framework** — Automated exploitation of discovered vulnerabilities
- **Beautiful Web GUI** — Professional dark-themed interface with real-time updates via WebSocket
- **Blazing Fast** — Async architecture with configurable thread pools
- **Multiple Report Formats** — Export to HTML, JSON, CSV, TXT
- **Fully Configurable** — Custom headers, cookies, proxies, extensions, status codes

---

## Installation

```bash
# Clone the repository
git clone https://github.com/anonymous-beta/WebFly.git
cd WebFly

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

---

## Quick Start

### CLI Mode

```bash
# Basic scan
webfly -u https://target.com

# Aggressive scan with all features
webfly -u https://target.com -t 100 --crawl --vuln-scan --exploit

# Custom wordlist and extensions
webfly -u https://target.com -w /path/to/wordlist.txt -e .php,.html,.bak

# Recursive scanning
webfly -u https://target.com -r --max-depth 5

# Generate HTML report
webfly -u https://target.com -o report --format html
```

### Web GUI Mode

```bash
# Start the server
webfly --server --host 0.0.0.0 --port 8080

# Open in browser
# http://localhost:8080
```

---

## Web GUI

The WebFly GUI provides an intuitive interface for:

- **Target Configuration** — Set URL, threads, timeout, extensions
- **Live Scanning** — Real-time results with WebSocket updates
- **Node Graph Visualization** — Interactive D3.js force-directed graph
  - Drag nodes to rearrange
  - Zoom and pan
  - Click nodes for details
  - Color-coded by type (Root, Directory, File, Interesting, Protected, Redirect, Error)
- **Results Table** — Sortable, filterable results
- **Vulnerability Dashboard** — View and exploit discovered vulnerabilities
- **Report Generation** — One-click export to multiple formats

---

## CLI Options

```
Target Options:
  -u, --url          Target URL
  -l, --url-list     File containing target URLs

Scan Options:
  -w, --wordlist     Path to wordlist file
  -t, --threads      Number of threads (default: 50)
  --timeout          Request timeout in seconds (default: 10)
  -e, --extensions   File extensions (comma-separated)
  -x, --exclude-extensions  Exclude extensions
  -m, --method       HTTP method (GET/POST/HEAD)
  -r, --recursive    Enable recursive scanning
  --max-depth        Maximum recursion depth (default: 3)
  --status-codes     Status codes to report
  --hide-length      Hide results with this content length
  --match-length     Only show results with this content length
  --no-redirects     Do not follow redirects
  --verify-ssl       Verify SSL certificates

Request Options:
  -H, --header       Custom header ("Name: Value")
  --cookie           Cookie string
  --proxy            Proxy URL
  --user-agent       Custom User-Agent

Features:
  --crawl            Enable smart crawling
  --vuln-scan        Enable vulnerability scanning
  --exploit          Enable exploitation

Output Options:
  -o, --output       Output file
  --format           Output format (txt/html/json/csv/all)
  --no-color         Disable colored output
  -q, --quiet        Quiet mode
  -v, --verbose      Verbose output

Server Mode:
  --server           Start Web GUI server
  --host             Server host (default: 0.0.0.0)
  --port             Server port (default: 8080)
```

---

## Vulnerability Detection

WebFly detects:

| Vulnerability | Confidence | Method |
|--------------|------------|--------|
| SQL Injection | High / Medium | Error-based, Time-based |
| XSS (Reflected) | High | Payload reflection |
| Local File Inclusion | High / Medium | File content detection |
| Remote Code Execution | High | Command output detection |
| SSRF | High / Medium | Internal service access |
| Open Redirect | High | Location header analysis |

---

## Project Structure

```
WebFly/
├── webfly/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── scanner.py          # Core async scanner engine
│   ├── exploiter.py        # Built-in exploitation modules
│   ├── crawler.py          # Smart crawler with link extraction
│   ├── reporter.py         # Report generation (HTML/JSON/CSV/TXT)
│   ├── utils.py            # Helper utilities
│   └── server.py           # FastAPI backend + WebSocket
├── web/
│   ├── index.html          # Main GUI
│   ├── css/
│   │   └── style.css       # Dark theme styles
│   └── js/
│       ├── app.js          # Main application logic
│       ├── graph.js        # D3.js node visualization
│       ├── scanner.js      # Scanner controls
│       └── exploiter.js    # Exploitation controls
├── wordlists/
│   ├── common.txt          # Default directory wordlist
│   └── backup.txt          # Backup file extensions
├── config/
│   └── default.yaml        # Default configuration
├── requirements.txt
├── setup.py
├── README.md
└── logo.png                # WebFly Logo
```

---

## Node Graph Colors

| Color | Type | Description |
|-------|------|-------------|
| Red | Root | Target root |
| Green | Directory | Discovered directory |
| Blue | File | Regular file |
| Orange | Interesting | Sensitive / config file |
| Yellow | Protected | 401 / 403 response |
| Purple | Redirect | 301 / 302 response |
| Dark Red | Error | 500+ response |

---

## Performance

| Threads | Requests / sec |
|---------|---------------|
| 50 | ~500 |
| 100 | ~1000 |
| 200 | ~1800 |

Performance varies based on target response time and network conditions.

---

## Disclaimer

**WebFly is intended for authorized security testing and research purposes only.** Always obtain proper authorization before scanning any target you do not own. The authors assume no liability for misuse or damage caused by this tool.

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

---

## License

MIT License — see LICENSE file for details.

---

## Credits

**Anonymous-beta** & **Victor410fer**

Built with love for the security community.

---

<p align="center">
  <i>"Reconnaissance is the foundation of all successful operations."</i>
</p>
