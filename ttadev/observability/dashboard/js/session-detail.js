/**
 * session-detail.js — Main panel: Provider → Model → Agent → Workflow tree + live metrics.
 *
 * Modes:
 *   id === 'all'  — aggregate all spans from all sessions (multi-agent view)
 *   id === <uuid> — filtered to a single session
 */

export class SessionDetail {
  constructor(el, app) {
    this.el = el;
    this.app = app;
    this.currentId = null;
    this.allMode = false;
    this.spans = [];
  }

  async init() {
    this._renderEmpty();
    this.app.on('sessionSelected', (id) => this._loadSession(id));
    this.app.on('spanAdded', (msg) => {
      // In allMode accept every span; in session mode accept only matching spans
      if (this.allMode || msg.session_id === this.currentId) {
        const span = { ...msg.span };
        if (this.allMode) {
          span._session_id   = msg.session_id;
          span._session_tool = msg.session_tool || 'unknown';
        }
        this.spans.push(span);
        this._render();
      }
    });
  }

  async _loadSession(id) {
    this.currentId = id;
    this.allMode   = id === 'all';

    if (this.allMode) {
      try {
        this.spans = await this.app.fetchJSON('/api/v2/spans');
        this.app.updateSessionBadge('All Sessions');
        this._render();
      } catch {
        this.el.innerHTML = `<div class="empty-state">Failed to load spans</div>`;
      }
      return;
    }

    try {
      const [, spans] = await Promise.all([
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
    const prevFilter = this.el.querySelector('.span-filter')?.value || '';
    const heading = this.allMode ? 'All Sessions' : `Session ${this.currentId.substring(0, 8)}`;

    this.el.innerHTML = `
      <div class="panel-heading">${heading}</div>
      ${this._renderMetrics(metrics)}
      <div class="provider-tree">${this._renderTree(tree)}</div>
      <div class="span-list">
        <div class="span-list-header">
          <div class="panel-heading" style="margin-bottom:0;">
            ${this.allMode ? 'Live Spans' : 'Recent Spans'} (${this.spans.length})
          </div>
          <input class="span-filter" type="search" placeholder="Filter spans…" value="${prevFilter}">
        </div>
        <div class="span-rows"></div>
      </div>
    `;

    // Wire filter
    const filterInput = this.el.querySelector('.span-filter');
    const rowsEl      = this.el.querySelector('.span-rows');
    const renderRows  = (q) => {
      const lq = q.toLowerCase();
      const visible = this.spans.slice(-200).reverse()
        .filter(s => !lq
          || s.name?.toLowerCase().includes(lq)
          || s.provider?.toLowerCase().includes(lq)
          || s.primitive_type?.toLowerCase().includes(lq)
          || s._session_tool?.toLowerCase().includes(lq));
      rowsEl.innerHTML = visible.map(s => this._renderSpanRow(s)).join('');
      rowsEl.querySelectorAll('.span-row').forEach(row => {
        row.addEventListener('click', () => {
          const span = this.spans.find(s => s.span_id === row.dataset.spanId);
          if (span) this.app.emit('spanSelected', span);
        });
      });
    };

    filterInput.addEventListener('input', e => renderRows(e.target.value));
    renderRows(prevFilter);
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
    const agentTools = new Set();

    for (const span of this.spans) {
      if (span.status === 'error') errors++;
      totalMs += span.duration_ms || 0;
      if (span.primitive_type) {
        primCounts[span.primitive_type] = (primCounts[span.primitive_type] || 0) + 1;
      }
      const hit = span.attributes?.['tta.cache.hit'];
      if (hit === true)  cacheHits++;
      if (hit === false) cacheMisses++;
      if (span._session_tool && span._session_tool !== 'unknown') agentTools.add(span._session_tool);
    }

    return { primCounts, errors, totalMs, cacheHits, cacheMisses, agentTools };
  }

  _renderMetrics({ primCounts, errors, totalMs, cacheHits, cacheMisses, agentTools }) {
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

    const agentChips = this.allMode
      ? [...agentTools].map(t => `<span class="metric-chip">🤖 ${t}</span>`).join('')
      : '';

    return `
      <div class="live-metrics">
        <span class="metric-chip">📊 Spans <span class="value">${this.spans.length}</span></span>
        ${agentChips}
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
    const isErr  = span.status === 'error';
    const icon   = isErr ? '✕' : '▸';
    const prim   = span.primitive_type
      ? `<span class="span-prim">${span.primitive_type}</span>` : '';
    const badge  = span.provider
      ? `<span class="span-provider" data-provider="${this._providerKey(span.provider)}">${this._providerShort(span.provider)}</span>` : '';
    const agentBadge = this.allMode && span._session_tool
      ? `<span class="span-agent" title="Session ${span._session_id}">${this._toolIcon(span._session_tool)}</span>` : '';
    const dur    = (span.duration_ms && span.duration_ms > 0)
      ? `${span.duration_ms.toFixed(1)}ms` : '—';
    const time   = span.started_at ? new Date(span.started_at).toLocaleTimeString() : '';

    return `
      <div class="span-row${isErr ? ' error' : ''}" data-span-id="${span.span_id}">
        <span class="span-icon ${isErr ? 'err' : ''}">${icon}</span>
        ${agentBadge}
        <span class="span-name">${span.name}</span>
        ${badge}
        ${prim}
        <span class="span-dur">${dur}</span>
        <span class="span-time">${time}</span>
      </div>
    `;
  }

  _toolIcon(tool) {
    const icons = { 'claude-code': '🤖', 'copilot': '✈️', 'cline': '🔧', 'unknown': '❓' };
    return icons[tool] || '❓';
  }

  _providerKey(provider) {
    const p = (provider || '').toLowerCase();
    if (p.includes('copilot') || p.includes('github')) return 'copilot';
    if (p.includes('anthropic'))  return 'anthropic';
    if (p.includes('openrouter')) return 'openrouter';
    if (p.includes('tta'))        return 'tta';
    return 'other';
  }

  _providerShort(provider) {
    const map = {
      'GitHub Copilot': 'GH', 'Anthropic': 'ANT',
      'OpenRouter': 'OR', 'TTA.dev': 'TTA',
    };
    return map[provider] || provider.substring(0, 3).toUpperCase();
  }
}
