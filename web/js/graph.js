/**
 * WebFly Node Graph Visualization
 * Interactive D3.js force-directed graph
 */

class GraphVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.width = this.container.clientWidth;
        this.height = 600;
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.showLabels = true;
        this.selectedNode = null;
        
        this.colors = {
            root: '#e94560',
            directory: '#4ecca3',
            file: '#3498db',
            interesting: '#ff6b6b',
            protected: '#f4d03f',
            redirect: '#9b59b6',
            error: '#e74c3c'
        };
        
        this.init();
    }
    
    init() {
        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', [0, 0, this.width, this.height]);
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
        
        // Main group for zoomable content
        this.g = this.svg.append('g');
        
        // Add arrow markers for links
        this.svg.append('defs').selectAll('marker')
            .data(['end'])
            .enter().append('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#0f3460');
        
        // Resize observer
        new ResizeObserver(() => {
            this.width = this.container.clientWidth;
            this.height = this.container.clientHeight || 600;
            this.svg.attr('width', this.width).attr('height', this.height);
            if (this.simulation) {
                this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
                this.simulation.alpha(0.3).restart();
            }
        }).observe(this.container);
    }
    
    render(data) {
        this.nodes = data.nodes || [];
        this.links = data.links || [];
        
        // Clear previous
        this.g.selectAll('*').remove();
        
        // Create simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30))
            .force('x', d3.forceX(this.width / 2).strength(0.05))
            .force('y', d3.forceY(this.height / 2).strength(0.05));
        
        // Draw links
        const link = this.g.append('g')
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', '#0f3460')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 1.5)
            .attr('marker-end', 'url(#arrow)');
        
        // Draw nodes
        const node = this.g.append('g')
            .selectAll('g')
            .data(this.nodes)
            .join('g')
            .call(d3.drag()
                .on('start', (event, d) => this.dragstarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragended(event, d)))
            .on('click', (event, d) => this.handleNodeClick(d))
            .on('mouseover', (event, d) => this.handleNodeHover(d, true))
            .on('mouseout', (event, d) => this.handleNodeHover(d, false));
        
        // Node circles
        node.append('circle')
            .attr('r', d => d.type === 'root' ? 20 : d.type === 'directory' ? 12 : 8)
            .attr('fill', d => this.colors[d.type] || this.colors.file)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .attr('class', 'node-circle')
            .style('cursor', 'pointer')
            .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))');
        
        // Node labels
        node.append('text')
            .text(d => this.showLabels ? this.getNodeLabel(d) : '')
            .attr('x', d => d.type === 'root' ? 25 : 15)
            .attr('y', 4)
            .attr('font-size', d => d.type === 'root' ? '14px' : '11px')
            .attr('font-weight', d => d.type === 'root' ? 'bold' : 'normal')
            .attr('fill', '#e0e0e0')
            .attr('pointer-events', 'none')
            .style('text-shadow', '0 1px 3px rgba(0,0,0,0.8)');
        
        // Pulse animation for interesting nodes
        node.filter(d => d.type === 'interesting' || d.type === 'root')
            .append('circle')
            .attr('r', d => d.type === 'root' ? 20 : 12)
            .attr('fill', 'none')
            .attr('stroke', d => this.colors[d.type])
            .attr('stroke-width', 2)
            .attr('opacity', 0.6)
            .append('animate')
            .attr('attributeName', 'r')
            .attr('from', d => d.type === 'root' ? 20 : 12)
            .attr('to', d => d.type === 'root' ? 30 : 20)
            .attr('dur', '1.5s')
            .attr('repeatCount', 'indefinite');
        
        // Update positions on tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    }
    
    getNodeLabel(node) {
        if (node.type === 'root') return 'ROOT';
        const url = new URL(node.url);
        const path = url.pathname;
        const parts = path.split('/').filter(p => p);
        return parts[parts.length - 1] || path || url.hostname;
    }
    
    handleNodeClick(node) {
        this.selectedNode = node;
        
        // Show details
        const details = document.getElementById('node-details');
        const content = document.getElementById('detail-content');
        
        details.style.display = 'block';
        content.innerHTML = `
            <p><strong>URL:</strong> ${node.url}</p>
            <p><strong>Status:</strong> <span class="status-${node.status}">${node.status}</span></p>
            <p><strong>Type:</strong> ${node.type}</p>
            <p><strong>Size:</strong> ${node.size} bytes</p>
            ${node.title ? `<p><strong>Title:</strong> ${node.title}</p>` : ''}
            ${node.technology?.length ? `<p><strong>Tech:</strong> ${node.technology.join(', ')}</p>` : ''}
        `;
        
        // Highlight connected nodes
        this.g.selectAll('.node-circle')
            .transition()
            .duration(200)
            .attr('opacity', d => {
                const isConnected = this.links.some(l => 
                    (l.source.id === node.id && l.target.id === d.id) ||
                    (l.target.id === node.id && l.source.id === d.id)
                );
                return d.id === node.id || isConnected ? 1 : 0.2;
            });
    }
    
    handleNodeHover(node, isHovering) {
        if (!isHovering && this.selectedNode) return;
        
        d3.select(event.currentTarget).select('circle')
            .transition()
            .duration(200)
            .attr('r', d => {
                const base = d.type === 'root' ? 20 : d.type === 'directory' ? 12 : 8;
                return isHovering ? base * 1.3 : base;
            });
    }
    
    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    reset() {
        this.svg.transition().duration(750).call(
            d3.zoom().transform,
            d3.zoomIdentity
        );
        this.g.selectAll('.node-circle').attr('opacity', 1);
        this.selectedNode = null;
        document.getElementById('node-details').style.display = 'none';
    }
    
    toggleLabels() {
        this.showLabels = !this.showLabels;
        this.g.selectAll('text')
            .transition()
            .duration(300)
            .style('opacity', this.showLabels ? 1 : 0);
    }
}

// Initialize graph visualizer
document.addEventListener('DOMContentLoaded', () => {
    window.graphVisualizer = new GraphVisualizer('graph-container');
});
