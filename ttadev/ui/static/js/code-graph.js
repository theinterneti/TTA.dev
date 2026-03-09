// Code Graph Visualization using D3.js force-directed graph
class CodeGraph {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = 600;
        this.svg = null;
        this.simulation = null;
        this.currentView = 'architecture';
    }

    async loadGraph(viewType = 'architecture') {
        this.currentView = viewType;
        try {
            const response = await fetch(`/api/codegraph/${viewType}`);
            const data = await response.json();
            this.renderGraph(data);
        } catch (error) {
            console.error('Failed to load code graph:', error);
            this.showError('Failed to load code graph');
        }
    }

    renderGraph(graphData) {
        // Clear existing
        this.container.html('');

        if (!graphData.nodes || graphData.nodes.length === 0) {
            this.container.append('p').text('No graph data available');
            return;
        }

        // Prepare data for D3
        const nodes = graphData.nodes.map((n, i) => ({
            ...n,
            id: i,
            x: this.width / 2 + (Math.random() - 0.5) * 100,
            y: this.height / 2 + (Math.random() - 0.5) * 100
        }));

        const links = [];
        nodes.forEach(node => {
            if (node.dependencies) {
                node.dependencies.forEach(dep => {
                    const target = nodes.find(n => n.name === dep);
                    if (target) {
                        links.push({ source: node.id, target: target.id });
                    }
                });
            }
        });

        // Create SVG
        this.svg = this.container.append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', [0, 0, this.width, this.height]);

        // Add zoom behavior
        const g = this.svg.append('g');
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });
        this.svg.call(zoom);

        // Create force simulation
        this.simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(50));

        // Draw edges
        const link = g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrowhead)');

        // Add arrowhead marker
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999');

        // Draw nodes
        const node = g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .enter().append('g')
            .call(d3.drag()
                .on('start', (event, d) => this.dragstarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragended(event, d)));

        node.append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        // Add labels
        node.append('text')
            .text(d => d.name)
            .attr('font-size', 12)
            .attr('dx', d => this.getNodeRadius(d) + 5)
            .attr('dy', 4)
            .attr('fill', '#333');

        // Add tooltips
        node.append('title')
            .text(d => `${d.name}\nType: ${d.type}\n${d.description || ''}`);

        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => nodes[d.source.index || d.source].x)
                .attr('y1', d => nodes[d.source.index || d.source].y)
                .attr('x2', d => nodes[d.target.index || d.target].x)
                .attr('y2', d => nodes[d.target.index || d.target].y);

            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // Store zoom object for reset
        this.zoom = zoom;
        this.zoomIdentity = d3.zoomIdentity;
    }

    getNodeRadius(node) {
        const sizeMap = {
            'base': 15,
            'primitive': 12,
            'recovery': 12,
            'composition': 12,
            'workflow': 14,
            'agent': 16,
            'package': 18,
            'external': 10,
            'internal': 14
        };
        return sizeMap[node.type] || 10;
    }

    getNodeColor(node) {
        const colorMap = {
            'base': '#9C27B0',
            'primitive': '#4CAF50',
            'recovery': '#FF5722',
            'composition': '#2196F3',
            'workflow': '#00BCD4',
            'agent': '#FF9800',
            'package': '#3F51B5',
            'external': '#9E9E9E',
            'internal': '#607D8B'
        };
        return colorMap[node.type] || '#999';
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

    resetZoom() {
        if (this.svg && this.zoom) {
            this.svg.transition().duration(750).call(
                this.zoom.transform,
                this.zoomIdentity
            );
        }
    }

    showError(message) {
        this.container.html(`<p class="error">${message}</p>`);
    }
}

// Export for use in dashboard
window.CodeGraph = CodeGraph;
