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
    this.ownership = [];
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
        const [spans, ownershipPayload] = await Promise.all([
          this.app.fetchJSON('/api/v2/spans'),
          this.app.fetchJSON('/api/v2/control/ownership').catch(() => ({ active: [] })),
        ]);
        this.spans = spans;
        this.ownership = ownershipPayload.active || [];
        this.app.updateSessionBadge('All Sessions');
        this._render();
      } catch {
        this.el.innerHTML = `<div class="empty-state">Failed to load spans</div>`;
      }
      return;
    }

    try {
      const [, spans, ownershipPayload] = await Promise.all([
        this.app.fetchJSON(`/api/v2/sessions/${id}`),
        this.app.fetchJSON(`/api/v2/sessions/${id}/spans`),
        this.app.fetchJSON(`/api/v2/sessions/${id}/ownership`).catch(() => ({ active: [] })),
      ]);
      this.spans = spans;
      this.ownership = ownershipPayload.active || [];
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
      ${this._renderWorkflowOwnership()}
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

  _renderWorkflowOwnership() {
    const workflowRecords = this.ownership.filter(record => record.workflow);
    const title = this.allMode ? 'Active Workflow Ownership' : 'Workflow Ownership';

    if (workflowRecords.length === 0) {
      return `
        <div class="workflow-ownership-panel">
          <div class="panel-heading workflow-heading">${title}</div>
          <div class="workflow-empty-state">No tracked workflow ownership is active for this view.</div>
        </div>
      `;
    }

    return `
      <div class="workflow-ownership-panel">
        <div class="panel-heading workflow-heading">${title}</div>
        <div class="workflow-ownership-list">
          ${workflowRecords.map(record => this._renderWorkflowOwnershipCard(record)).join('')}
        </div>
      </div>
    `;
  }

  _renderWorkflowOwnershipCard(record) {
    const workflow = record.workflow;
    const task = record.task || {};
    const run = record.run || {};
    const session = record.session || null;
    const currentStep = workflow.current_step;
    const recentSteps = workflow.recent_steps || [];

    return `
      <div class="workflow-ownership-card">
        <div class="workflow-card-header">
          <div>
            <div class="workflow-title">${this._escapeHtml(workflow.workflow_name)}</div>
            <div class="workflow-goal">${this._escapeHtml(workflow.workflow_goal || '-')}</div>
          </div>
          <span class="workflow-status workflow-status-${this._escapeAttr(workflow.workflow_status)}">
            ${this._escapeHtml(workflow.workflow_status)}
          </span>
        </div>
        <div class="workflow-meta-row">
          <span class="workflow-meta-chip">Task ${this._escapeHtml(task.id || '-')}</span>
          <span class="workflow-meta-chip">Run ${this._escapeHtml(run.id || '-')}</span>
          ${session ? `<span class="workflow-meta-chip">Session ${this._escapeHtml(session.id.substring(0, 8))}</span>` : ''}
        </div>
        <div class="workflow-current-step">
          <div class="workflow-section-label">Current step</div>
          ${
            currentStep
              ? `
                <div class="workflow-step-row">
                  <strong>${currentStep.step_number}. ${this._escapeHtml(currentStep.agent_name)}</strong>
                  <span>${this._escapeHtml(currentStep.status)}</span>
                  <span>${this._escapeHtml(currentStep.gate_decision || 'no-gate-decision')}</span>
                </div>
                <div class="workflow-step-summary">
                  ${this._escapeHtml(currentStep.last_result_summary || 'No result summary yet.')}
                </div>
              `
              : `<div class="workflow-step-summary">Workflow tracking exists, but no active step is set yet.</div>`
          }
        </div>
        <div class="workflow-recent-steps">
          <div class="workflow-section-label">Recent steps</div>
          ${
            recentSteps.length
              ? recentSteps
                  .map(
                    step => `
                      <div class="workflow-step-row workflow-step-row-compact">
                        <strong>${step.step_number}. ${this._escapeHtml(step.agent_name)}</strong>
                        <span>${this._escapeHtml(step.status)}</span>
                        <span>${this._escapeHtml(step.gate_decision || '—')}</span>
                      </div>
                    `
                  )
                  .join('')
              : '<div class="workflow-step-summary">No completed or transitioned steps yet.</div>'
          }
        </div>
      </div>
    `;
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
    const dur    = (span.duration_ms && span.duration_ms > 0)
      ? `${span.duration_ms.toFixed(1)}ms` : '—';
    const time   = span.started_at ? new Date(span.started_at).toLocaleTimeString() : '';

    // Build row via DOM to avoid XSS — span fields are untrusted server data
    const row = document.createElement('div');
    row.className = `span-row${isErr ? ' error' : ''}`;
    row.dataset.spanId = span.span_id;

    const iconEl = document.createElement('span');
    iconEl.className = `span-icon${isErr ? ' err' : ''}`;
    iconEl.textContent = icon;
    row.appendChild(iconEl);

    if (this.allMode && span._session_tool) {
      const agentEl = document.createElement('span');
      agentEl.className = 'span-agent';
      agentEl.title = `Session ${span._session_id}`;
      agentEl.textContent = this._toolIcon(span._session_tool);
      row.appendChild(agentEl);
    }

    const nameEl = document.createElement('span');
    nameEl.className = 'span-name';
    nameEl.textContent = span.name;
    row.appendChild(nameEl);

    if (span.provider) {
      const badgeEl = document.createElement('span');
      badgeEl.className = 'span-provider';
      badgeEl.dataset.provider = this._providerKey(span.provider);
      badgeEl.textContent = this._providerShort(span.provider);
      row.appendChild(badgeEl);
    }

    if (span.primitive_type) {
      const primEl = document.createElement('span');
      primEl.className = 'span-prim';
      primEl.textContent = span.primitive_type;
      row.appendChild(primEl);
    }

    const durEl = document.createElement('span');
    durEl.className = 'span-dur';
    durEl.textContent = dur;
    row.appendChild(durEl);

    const timeEl = document.createElement('span');
    timeEl.className = 'span-time';
    timeEl.textContent = time;
    row.appendChild(timeEl);

    return row.outerHTML;
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

  _escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  _escapeAttr(value) {
    return String(value).replace(/[^a-zA-Z0-9_-]/g, '-');
  }
}
