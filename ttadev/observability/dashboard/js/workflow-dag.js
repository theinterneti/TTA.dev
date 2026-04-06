/**
 * workflow-dag.js — Workflow DAG visualisation panel.
 *
 * Fetches /api/v2/tracing/dag and renders a D3 force-directed graph where
 * nodes are agents and directed edges are handoffs.  Clicking a node emits
 * the shared "sessionSelected" event so the Sessions detail panel updates.
 *
 * Node status colours:
 *   idle      → var(--text-muted)  grey — agent seen but never handed off
 *   active    → var(--accent)       blue — leaf agent currently receiving work
 *   completed → var(--success)      green — agent that has handed off
 */

// eslint-disable-next-line no-unused-vars
const _esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const STATUS_COLOR = {
  idle:      '#6b7280',  // neutral grey
  active:    '#3b82f6',  // blue
  completed: '#22c55e',  // green
};

export class WorkflowDag {
  /**
   * @param {HTMLElement} container  — element that wraps the entire panel
   * @param {object}      app        — App singleton (EventEmitter + fetchJSON)
   */
  constructor(container, app) {
    this._container = container;
    this._app = app;
    this._svg = null;
    this._simulation = null;
    this._refreshTimer = null;
  }

  async init() {
    // Nothing to pre-fetch; rendering happens on tab activation.
  }

  // ------------------------------------------------------------------
  // Public activation (called by app._activateDagTab)
  // ------------------------------------------------------------------

  async activate() {
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }

    await this._renderDag();

    // Auto-refresh every 15 s while the tab is visible.
    this._refreshTimer = setInterval(async () => {
      const panel = document.getElementById('tab-dag');
      if (panel && !panel.hidden) {
        await this._renderDag();
      } else {
        clearInterval(this._refreshTimer);
        this._refreshTimer = null;
      }
    }, 15_000);
  }

  // ------------------------------------------------------------------
  // Internal rendering helpers
  // ------------------------------------------------------------------

  async _renderDag() {
    const content = document.getElementById('dag-content');
    if (!content) return;

    let data;
    try {
      data = await this._app.fetchJSON('/api/v2/tracing/dag');
    } catch (err) {
      content.innerHTML = `<div class="live-empty-state"><p>Could not load DAG.</p><small>${_esc(err.message)}</small></div>`;
      return;
    }

    const nodes = data.nodes || [];
    const edges = data.edges || [];

    if (nodes.length === 0) {
      content.innerHTML = `
        <div class="live-empty-state">
          <div class="empty-icon">🔗</div>
          <p>No agent handoffs recorded yet.</p>
          <small>Run a workflow with handoff triggers to see the DAG.</small>
        </div>`;
      return;
    }

    this._renderGraph(content, nodes, edges);
  }

  _renderGraph(container, nodes, edges) {
    // Clear previous render.
    container.innerHTML = '';

    const width  = container.clientWidth  || 800;
    const height = Math.max(container.clientHeight || 400, 400);

    // Build D3 graph structures (copies so the simulation can mutate them).
    const nodeData = nodes.map(n => ({ ...n }));
    const linkData = edges.map(e => ({
      ...e,
      source: e.source,
      target: e.target,
    }));

    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .style('background', 'var(--bg-secondary, #1e2130)');

    // Arrow marker definition.
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#6b7280');

    const g = svg.append('g');

    // Zoom + pan.
    svg.call(
      d3.zoom()
        .scaleExtent([0.2, 4])
        .on('zoom', event => g.attr('transform', event.transform))
    );

    // Links (edges).
    const link = g.append('g')
      .selectAll('line')
      .data(linkData)
      .join('line')
      .attr('stroke', '#4b5563')
      .attr('stroke-width', d => Math.min(1 + d.count, 6))
      .attr('marker-end', 'url(#arrowhead)');

    // Edge labels (reason).
    const edgeLabel = g.append('g')
      .selectAll('text')
      .data(linkData)
      .join('text')
      .attr('fill', '#9ca3af')
      .attr('font-size', 10)
      .attr('text-anchor', 'middle')
      .text(d => d.reason || '');

    // Node groups.
    const node = g.append('g')
      .selectAll('g')
      .data(nodeData)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (_event, d) => {
        if (d.session_id) this._app.emit('sessionSelected', d.session_id);
      })
      .call(
        d3.drag()
          .on('start', (event, d) => {
            if (!event.active) this._simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => {
            if (!event.active) this._simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node.append('circle')
      .attr('r', 18)
      .attr('fill', d => STATUS_COLOR[d.status] || STATUS_COLOR.idle)
      .attr('stroke', '#1e2130')
      .attr('stroke-width', 2);

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#f9fafb')
      .attr('font-size', 10)
      .attr('font-family', 'monospace')
      .text(d => (d.label || d.id).slice(0, 12));

    // Tooltip title.
    node.append('title')
      .text(d => `${d.label}\nstatus: ${d.status}\nspans: ${d.span_count}`);

    // Force simulation.
    this._simulation = d3.forceSimulation(nodeData)
      .force('link', d3.forceLink(linkData).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        edgeLabel
          .attr('x', d => (d.source.x + d.target.x) / 2)
          .attr('y', d => (d.source.y + d.target.y) / 2 - 6);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
      });

    this._svg = svg;

    // Legend.
    const legend = d3.select(container)
      .append('div')
      .style('position', 'absolute')
      .style('bottom', '8px')
      .style('right', '8px')
      .style('font-size', '11px')
      .style('color', 'var(--text-muted, #9ca3af)');

    Object.entries(STATUS_COLOR).forEach(([status, color]) => {
      legend.append('span')
        .style('margin-right', '12px')
        .html(`<span style="color:${color}">●</span> ${status}`);
    });
  }
}
