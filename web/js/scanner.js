/**
 * WebFly Scanner Controls
 */

class ScannerController {
    constructor() {
        this.isScanning = false;
        this.scanId = null;
    }
    
    async startScan(config) {
        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            this.scanId = data.scan_id;
            this.isScanning = true;
            
            return data;
        } catch (error) {
            console.error('Start scan failed:', error);
            throw error;
        }
    }
    
    async stopScan() {
        if (!this.scanId) return;
        
        try {
            await fetch(`/api/scan/${this.scanId}/stop`, { method: 'POST' });
            this.isScanning = false;
        } catch (error) {
            console.error('Stop scan failed:', error);
        }
    }
    
    async getScanStatus(scanId) {
        try {
            const response = await fetch(`/api/scan/${scanId}`);
            return await response.json();
        } catch (error) {
            console.error('Get status failed:', error);
            return null;
        }
    }
}
