/**
 * WebFly Main Application
 */

class WebFlyApp {
    constructor() {
        this.currentSection = 'scanner';
        this.scanResults = [];
        this.nodes = { nodes: [], links: [] };
        this.vulnerabilities = [];
        this.ws = null;
        this.currentScanId = null;
        
        this.init();
    }
    
    init() {
        this.setupNavigation();
        this.setupWebSocket();
        this.setupEventListeners();
    }
    
    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });
    }
    
    switchSection(section) {
        // Update nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.section === section);
        });
        
        // Update section
        document.querySelectorAll('.section').forEach(sec => {
            sec.classList.toggle('active', sec.id === section);
        });
        
        this.currentSection = section;
        
        // Trigger section-specific logic
        if (section === 'graph' && this.nodes.nodes.length > 0) {
            window.graphVisualizer?.render(this.nodes);
        }
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
        
        this.ws.onopen = () => {
            console.log('WebFly WebSocket connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting...');
            setTimeout(() => this.setupWebSocket(), 3000);
        };
    }
    
    handleWebSocketMessage(data) {
        switch(data.type) {
            case 'scan_progress':
                this.handleScanProgress(data.data);
                break;
            case 'scan_complete':
                this.handleScanComplete(data.data);
                break;
            case 'crawl_complete':
                this.handleCrawlComplete(data.data);
                break;
            case 'vuln_scan_complete':
                this.handleVulnScanComplete(data.data);
                break;
            case 'exploit_complete':
                this.handleExploitComplete(data.data);
                break;
            case 'scan_error':
                this.handleScanError(data.error);
                break;
        }
    }
    
    handleScanProgress(result) {
        this.scanResults.push(result);
        this.updateLiveStats();
        this.addResultToTable(result);
    }
    
    handleScanComplete(data) {
        document.getElementById('start-scan').disabled = false;
        document.getElementById('stop-scan').disabled = true;
        
        this.nodes = data.nodes;
        this.updateStats(data.stats);
        
        // Switch to graph view
        setTimeout(() => this.switchSection('graph'), 500);
    }
    
    handleCrawlComplete(data) {
        console.log('Crawl complete:', data);
    }
    
    handleVulnScanComplete(data) {
        this.vulnerabilities = data.vulnerabilities;
        this.renderVulnerabilities();
    }
    
    handleExploitComplete(data) {
        console.log('Exploitation complete:', data);
    }
    
    handleScanError(error) {
        console.error('Scan error:', error);
        alert(`Scan error: ${error}`);
        document.getElementById('start-scan').disabled = false;
        document.getElementById('stop-scan').disabled = true;
    }
    
    setupEventListeners() {
        // Start scan
        document.getElementById('start-scan').addEventListener('click', () => this.startScan());
        
        // Stop scan
        document.getElementById('stop-scan').addEventListener('click', () => this.stopScan());
        
        // Graph controls
        document.getElementById('reset-graph')?.addEventListener('click', () => {
            window.graphVisualizer?.reset();
        });
        
        document.getElementById('toggle-labels')?.addEventListener('click', () => {
            window.graphVisualizer?.toggleLabels();
        });
        
        // Export buttons
        document.getElementById('export-json')?.addEventListener('click', () => this.exportResults('json'));
        document.getElementById('export-csv')?.addEventListener('click', () => this.exportResults('csv'));
        document.getElementById('export-html')?.addEventListener('click', () => this.exportResults('html'));
        
        // Report generation
        document.getElementById('generate-report')?.addEventListener('click', () => this.generateReport());
        
        // Filters
        document.getElementById('filter-url')?.addEventListener('input', (e) => this.filterResults());
        document.getElementById('filter-status')?.addEventListener('change', () => this.filterResults());
        document.getElementById('filter-type')?.addEventListener('change', () => this.filterResults());
    }
    
    async startScan() {
        const target = document.getElementById('target-url').value;
        if (!target) {
            alert('Please enter a target URL');
            return;
        }
        
        const config = {
            target: target,
            threads: parseInt(document.getElementById('threads').value) || 50,
            timeout: parseInt(document.getElementById('timeout').value) || 10,
            max_depth: parseInt(document.getElementById('max-depth').value) || 3,
            extensions: document.getElementById('extensions').value || null,
            status_filter: document.getElementById('status-codes').value,
            recursive: document.getElementById('recursive').checked,
            follow_redirects: document.getElementById('follow-redirects').checked,
            enable_crawler: document.getElementById('crawl-enabled').checked,
            enable_vuln_scan: document.getElementById('vuln-scan-enabled').checked,
            enable_exploit: document.getElementById('exploit-enabled').checked
        };
        
        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            this.currentScanId = data.scan_id;
            
            // UI updates
            document.getElementById('start-scan').disabled = true;
            document.getElementById('stop-scan').disabled = false;
            document.getElementById('live-stats').style.display = 'grid';
            document.getElementById('live-results').style.display = 'block';
            document.getElementById('results-tbody').innerHTML = '';
            this.scanResults = [];
            
        } catch (error) {
            console.error('Failed to start scan:', error);
            alert('Failed to start scan. Check console for details.');
        }
    }
    
    async stopScan() {
        if (!this.currentScanId) return;
        
        try {
            await fetch(`/api/scan/${this.currentScanId}/stop`, { method: 'POST' });
            document.getElementById('start-scan').disabled = false;
            document.getElementById('stop-scan').disabled = true;
        } catch (error) {
            console.error('Failed to stop scan:', error);
        }
    }
    
    updateLiveStats() {
        const tested = this.scanResults.length;
        const found = this.scanResults.filter(r => r.status !== 0).length;
        const errors = this.scanResults.filter(r => r.error).length;
        
        document.getElementById('stat-tested').textContent = tested;
        document.getElementById('stat-found').textContent = found;
        document.getElementById('stat-errors').textContent = errors;
    }
    
    addResultToTable(result) {
        const tbody = document.getElementById('results-tbody');
        const row = document.createElement('tr');
        
        const statusClass = `status-${result.status}`;
        const typeTag = result.is_interesting ? '<span class="tag tag-interesting">!</span>' : 
                       result.is_directory ? '<span class="tag tag-directory">DIR</span>' : '';
        
        row.innerHTML = `
            <td class="${statusClass}">${result.status}</td>
            <td>${result.url}</td>
            <td>${result.size}</td>
            <td>${result.title || '-'}</td>
            <td>${typeTag}</td>
            <td>${result.response_time?.toFixed(3) || '-'}s</td>
        `;
        
        tbody.insertBefore(row, tbody.firstChild);
        
        // Keep only last 100 rows for performance
        while (tbody.children.length > 100) {
            tbody.removeChild(tbody.lastChild);
        }
    }
    
    updateStats(stats) {
        document.getElementById('stat-tested').textContent = stats.tested;
        document.getElementById('stat-found').textContent = stats.found;
        document.getElementById('stat-errors').textContent = stats.errors;
        document.getElementById('progress-fill').style.width = '100%';
    }
    
    renderVulnerabilities() {
        const container = document.getElementById('vuln-list');
        
        if (this.vulnerabilities.length === 0) {
            container.innerHTML = '<p class="empty-state">No vulnerabilities found.</p>';
            return;
        }
        
        container.innerHTML = this.vulnerabilities.map(vuln => `
            <div class="vuln-card ${vuln.confidence}">
                <div class="vuln-header">
                    <span class="vuln-type">${vuln.type}</span>
                    <span class="vuln-confidence ${vuln.confidence}">${vuln.confidence.toUpperCase()}</span>
                </div>
                <div class="vuln-url">${vuln.url}</div>
                <div class="vuln-evidence">${vuln.evidence}</div>
                ${vuln.payload ? `<div style="margin-top: 8px; font-size: 0.85em; color: var(--text-muted);">Payload: ${vuln.payload}</div>` : ''}
            </div>
        `).join('');
    }
    
    filterResults() {
        const urlFilter = document.getElementById('filter-url').value.toLowerCase();
        const statusFilter = document.getElementById('filter-status').value;
        const typeFilter = document.getElementById('filter-type').value;
        
        const filtered = this.scanResults.filter(r => {
            const matchUrl = !urlFilter || r.url.toLowerCase().includes(urlFilter);
            const matchStatus = !statusFilter || r.status.toString() === statusFilter;
            const matchType = !typeFilter || 
                (typeFilter === 'directory' && r.is_directory) ||
                (typeFilter === 'interesting' && r.is_interesting) ||
                (typeFilter === 'file' && !r.is_directory && !r.is_interesting);
            
            return matchUrl && matchStatus && matchType;
        });
        
        this.renderResultsTable(filtered);
    }
    
    renderResultsTable(results) {
        const container = document.getElementById('results-full');
        
        if (results.length === 0) {
            container.innerHTML = '<p class="empty-state">No results match the filters.</p>';
            return;
        }
        
        container.innerHTML = `
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>URL</th>
                        <th>Size</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Response Time</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.map(r => `
                        <tr>
                            <td class="status-${r.status}">${r.status}</td>
                            <td>${r.url}</td>
                            <td>${r.size}</td>
                            <td>${r.title || '-'}</td>
                            <td>${r.is_directory ? 'DIR' : r.is_interesting ? '!' : 'FILE'}</td>
                            <td>${r.response_time?.toFixed(3) || '-'}s</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    async exportResults(format) {
        if (!this.currentScanId) {
            alert('No scan to export');
            return;
        }
        
        try {
            const response = await fetch(`/api/report/${this.currentScanId}?format=${format}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `webfly_report.${format}`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export failed');
        }
    }
    
    async generateReport() {
        if (!this.currentScanId) {
            alert('No scan to generate report from');
            return;
        }
        
        const format = document.getElementById('report-format').value;
        await this.exportResults(format);
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.webflyApp = new WebFlyApp();
});
