/**
 * cgc-graph.js — D3 force-directed code graph with live overlay.
 * Migrated from ttadev/ui/static/js/code-graph.js and extended.
 */

export class CgcGraph {
  constructor(el, app) {
    this.el = el;
    this.app = app;
    this.currentView = 'architecture';
    this.liveOverlay = false;
    this.svg = null;
    this.simulation = null;
    this._activeNodes = new Set();  // primitive names active in live overlay
    this._available = true;
  }

  async init() {
    this._renderShell();
    this.app.on('cgcUnavailable', () => this._loadGraph(this.currentView));
    this.app.on('spanAdded', (msg) => {
      if (this.liveOverlay && msg.span?.primitive_type) {
        this._pulseNode(msg.span.primitive_type);
      }
    });
    this.app.on('cgcNodeSelected', (node) => {
      if (node?.name) this.app.emit('cgcFilterByNode', node.name);
    });
    // Load default view after a short delay (let server settle)
    setTimeout(() => this._loadGraph('architecture'), 800);
  }

  _renderShell() {
    this.el.innerHTML = `
      <div class="graph-toolbar">
        <h3>🕸️ Codebase Graph (CGC)</h3>
        <button class="graph-btn active" data-view="architecture">Architecture</button>
        <button class="graph-btn" data-view="dependencies">Dependencies</button>
        <button class="graph-btn" data-view="primitives">Primitives</button>
        <button class="graph-btn" data-view="agents">Agents</button>
        <label class="live-toggle">
          <input type="checkbox" id="live-toggle-cb"> Live overlay
        </label>
      </div>
      <div id="cgc-canvas"></div>
    `;

    this.el.querySelectorAll('.graph-btn[data-view]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.el.querySelectorAll('.graph-btn[data-view]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this._loadGraph(btn.dataset.view);
      });
    });

    document.getElementById('live-toggle-cb').addEventListener('change', (e) => {
      this.liveOverlay = e.target.checked;
    });
  }

  async _loadGraph(viewType) {
    this.currentView = viewType;
    const canvas = document.getElementById('cgc-canvas');
    canvas.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);">Loading ${viewType}…</div>`;

    try {
      const data = await this.app.fetchJSON(`/api/v2/cgc/${viewType}`);
      if (data.source === 'spans') {
        // Span-derived fallback — still render the graph but show a notice
        this._renderGraph(canvas, data);
        this._showFallbackNotice(canvas);
      } else {
        this._renderGraph(canvas, data);
      }
    } catch {
      canvas.innerHTML = `<div class="cgc-unavailable"><span>Failed to load graph</span></div>`;
    }
  }

  _showFallbackNotice(canvas) {
    const notice = document.createElement('div');
    notice.style.cssText = 'position:absolute;top:8px;right:8px;font-size:.75em;color:var(--text-muted);background:var(--bg-card);padding:4px 8px;border-radius:4px;border:1px solid var(--border);';
    notice.textContent = '⚡ Live span data (CGC offline)';
    canvas.style.position = 'relative';
    canvas.appendChild(notice);
  }

  _showUnavailable() {
    this._available = false;
    const canvas = document.getElementById('cgc-canvas');
    if (canvas) {
      canvas.innerHTML = `
        <div class="cgc-unavailable">
          <span>CGC not available</span>
          <span style="font-size:.85em;">Start the CGC MCP server to enable code graph:</span>
          <code>uv run cgc mcp start</code>
        </div>
      `;
    }
  }

  _renderGraph(canvas, graphData) {
    canvas.innerHTML = '';
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || graphData.links || [];

    if (nodes.length === 0) {
      canvas.innerHTML = `<div class="cgc-unavailable"><span>No graph data for this view</span></div>`;
      return;
    }

    const W = canvas.getBoundingClientRect().width || 800;
    const H = 500;

    const nodeData = nodes.map((n, i) => ({
      ...n,
      _id: i,
      x: W / 2 + (Math.random() - 0.5) * 200,
      y: H / 2 + (Math.random() - 0.5) * 200,
    }));

    const nodeIndex = new Map(nodeData.map(n => [n.name || n.id || String(n._id), n]));

    const linkData = edges.map(e => ({
      source: typeof e.source === 'number' ? nodeData[e.source] : nodeIndex.get(e.source) || nodeData[0],
      target: typeof e.target === 'number' ? nodeData[e.target] : nodeIndex.get(e.target) || nodeData[0],
    })).filter(l => l.source && l.target);

    const svg = d3.select(canvas).append('svg')
      .attr('width', W).attr('height', H)
      .attr('viewBox', [0, 0, W, H]);

    this.svg = svg;

    // Zoom
    const g = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.1, 4]).on('zoom', ev => g.attr('transform', ev.transform)));

    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrow').attr('viewBox', '-0 -5 10 10')
      .attr('refX', 22).attr('refY', 0).attr('orient', 'auto')
      .attr('markerWidth', 6).attr('markerHeight', 6)
      .append('path').attr('d', 'M 0,-5 L 10,0 L 0,5').attr('fill', '#555');

    // Links
    const link = g.append('g').selectAll('line').data(linkData)
      .join('line')
      .attr('stroke', '#444').attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrow)');

    // Nodes
    const node = g.append('g').selectAll('g').data(nodeData)
      .join('g')
      .attr('class', d => `cgc-node ${d.type || ''}`)
      .attr('data-name', d => d.name || '')
      .call(d3.drag()
        .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
        .on('end',   (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      )
      .on('click', (ev, d) => { this.app.emit('cgcNodeSelected', d); });

    node.append('circle')
      .attr('r', 14)
      .attr('fill', d => this._nodeColor(d))
      .attr('stroke', '#222').attr('stroke-width', 1.5);

    // Label: short name inside circle, full name below
    node.append('text')
      .attr('text-anchor', 'middle').attr('dy', '0.35em')
      .attr('font-size', '8px').attr('fill', '#fff').attr('pointer-events', 'none')
      .text(d => this._shortLabel(d.name || ''));

    node.append('text')
      .attr('text-anchor', 'middle').attr('dy', '26px')
      .attr('font-size', '9px').attr('fill', 'var(--text-muted)').attr('pointer-events', 'none')
      .text(d => (d.name || '').length > 18 ? (d.name || '').substring(0, 16) + '…' : (d.name || ''));

    // Tooltip
    node.append('title').text(d => d.name || '');

    // Simulation
    const sim = d3.forceSimulation(nodeData)
      .force('link', d3.forceLink(linkData).id(d => d._id).distance(120))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collide', d3.forceCollide(20));

    this.simulation = sim;

    sim.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  _nodeColor(d) {
    const type = (d.type || '').toLowerCase();
    const name = (d.name || '').toLowerCase();
    if (type === 'primitive' || name.includes('primitive')) return '#764ba2';
    if (type === 'agent')     return '#667eea';
    if (type === 'provider')  return '#10b981';
    if (type === 'model')     return '#3d7a8a';
    if (name.includes('workflow'))  return '#10b981';
    return '#3d4563';
  }

  _shortLabel(name) {
    // Use abbreviations for known long names
    const abbrevs = {
      'SequentialPrimitive': 'Seq',
      'CircuitBreakerPrimitive': 'CB',
      'LambdaPrimitive': 'λ',
      'RetryPrimitive': 'Retry',
      'CachePrimitive': 'Cache',
      'TimeoutPrimitive': 'T/O',
      'FallbackPrimitive': 'Fall',
      'ParallelPrimitive': 'Par',
      'GitHub Copilot': 'GH✈',
      'Anthropic': 'ANT',
      'OpenRouter': 'OR',
    };
    if (abbrevs[name]) return abbrevs[name];
    return name.length > 6 ? name.substring(0, 5) + '…' : name;
  }

  _pulseNode(primitiveName) {
    if (!this.svg) return;
    const node = this.svg.selectAll('.cgc-node')
      .filter(d => (d.name || '') === primitiveName);

    if (node.empty()) return;

    node.select('circle')
      .transition().duration(200)
        .attr('fill', '#10b981').attr('r', 20)
      .transition().duration(800)
        .attr('fill', d => this._nodeColor(d)).attr('r', 14);
  }
}
