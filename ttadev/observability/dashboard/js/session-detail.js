/**
 * session-detail.js — Main panel: Provider → Model → Agent → Workflow tree + live metrics.
 */

export class SessionDetail {
  constructor(el, app) {
    this.el = el;
    this.app = app;
    this.currentId = null;
    this.spans = [];
  }

  async init() {
    this._renderEmpty();
    this.app.on('sessionSelected', (id) => this._loadSession(id));
    this.app.on('spanAdded', (msg) => {
      if (msg.session_id === this.currentId) {
        this.spans.push(msg.span);
        this._render();
      }
    });
  }

  async _loadSession(id) {
    this.currentId = id;
    try {
      const [session, spans] = await Promise.all([
        this.app.fetchJSON(`/api/v2/sessions/${id}`),
        this.app.fetchJSON(`/api/v2/sessions/${id}/spans`),
      ]);
      this.spans = spans;
      this.app.updateSessionBadge(`Session ${id.substring(0, 8)}`);
      this._render();
    } catch {
      this.el.innerHTML = `<div class="empty-state">Failed to load session</div>`;
    }
  }

  _render() {
    if (!this.currentId) { this._renderEmpty(); return; }

    const tree    = this._buildTree();
    const metrics = this._buildMetrics();

    this.el.innerHTML = `
      <div class="panel-heading">Session ${this.currentId.substring(0, 8)}</div>
      ${this._renderMetrics(metrics)}
      <div class="provider-tree">${this._renderTree(tree)}</div>
      <div class="span-list">
        <div class="panel-heading" style="margin-top:20px;">Recent Spans (${this.spans.length})</div>
        ${this.spans.slice(-50).reverse().map(s => this._renderSpanRow(s)).join('')}
      </div>
    `;

    // Wire span row clicks
    this.el.querySelectorAll('.span-row').forEach(row => {
      row.addEventListener('click', () => {
        const spanId = row.dataset.spanId;
        const span = this.spans.find(s => s.span_id === spanId);
        if (span) this.app.emit('spanSelected', span);
      });
    });
  }

  _renderEmpty() {
    this.el.innerHTML = `<div class="empty-state">Select a session to view details</div>`;
  }

  _buildTree() {
    // provider → model → agent_role → count
    const tree = {};
    for (const span of this.spans) {
      const p = span.provider || 'unknown';
      const m = span.model    || 'unknown';
      const r = span.agent_role || '(direct)';
      if (!tree[p]) tree[p] = {};
      if (!tree[p][m]) tree[p][m] = {};
      tree[p][m][r] = (tree[p][m][r] || 0) + 1;
    }
    return tree;
  }

  _buildMetrics() {
    const primCounts = {};
    let errors = 0;
    let totalMs = 0;
    let cacheHits = 0, cacheMisses = 0;

    for (const span of this.spans) {
      if (span.status === 'error') errors++;
      totalMs += span.duration_ms || 0;
      if (span.primitive_type) {
        primCounts[span.primitive_type] = (primCounts[span.primitive_type] || 0) + 1;
      }
      const hit = span.attributes?.['tta.cache.hit'];
      if (hit === true)  cacheHits++;
      if (hit === false) cacheMisses++;
    }

    return { primCounts, errors, totalMs, cacheHits, cacheMisses };
  }

  _renderMetrics({ primCounts, errors, totalMs, cacheHits, cacheMisses }) {
    const prims = Object.entries(primCounts)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => `<span class="metric-chip">⚙️ ${name} <span class="value">×${count}</span></span>`)
      .join('');

    const cacheTotal = cacheHits + cacheMisses;
    const cacheChip = cacheTotal > 0
      ? `<span class="metric-chip">💾 Cache hit <span class="value">${Math.round(cacheHits / cacheTotal * 100)}%</span></span>`
      : '';

    const errChip = errors > 0
      ? `<span class="metric-chip" style="color:var(--error)">❌ Errors <span class="value" style="color:var(--error)">${errors}</span></span>`
      : '';

    return `
      <div class="live-metrics">
        <span class="metric-chip">📊 Spans <span class="value">${this.spans.length}</span></span>
        ${prims}
        ${cacheChip}
        ${errChip}
      </div>
    `;
  }

  _renderTree(tree) {
    return Object.entries(tree).map(([provider, models]) => `
      <div class="provider-group">
        <div class="provider-label">📡 ${provider}</div>
        ${Object.entries(models).map(([model, roles]) => `
          <div class="model-group">
            <div class="model-label">
              <span>🤖 ${model}</span>
              <span class="badge badge-muted">${Object.values(roles).reduce((a,b)=>a+b,0)} calls</span>
            </div>
            ${Object.entries(roles).map(([role, count]) => `
              <div class="role-group">
                <div class="role-label">
                  <span>🎭 ${role}</span>
                  <span class="badge badge-accent">${count}</span>
                </div>
              </div>
            `).join('')}
          </div>
        `).join('')}
      </div>
    `).join('');
  }

  _renderSpanRow(span) {
    const ok   = span.status !== 'error';
    const icon = ok ? '✅' : '❌';
    const prim = span.primitive_type ? `<span class="span-prim">${span.primitive_type}</span>` : '';
    const time = span.started_at ? new Date(span.started_at).toLocaleTimeString() : '';

    return `
      <div class="span-row ${ok ? '' : 'error'}" data-span-id="${span.span_id}">
        <span>${icon}</span>
        <span class="span-name">${span.name}</span>
        ${prim}
        <span class="span-dur">${(span.duration_ms || 0).toFixed(1)}ms</span>
        <span class="span-time">${time}</span>
      </div>
    `;
  }
}
