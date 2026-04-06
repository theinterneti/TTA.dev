/**
 * app.js — Main controller
 * Owns: WebSocket connection, EventEmitter, header rendering, tab switching,
 * and the live agent activity panel.
 * Other modules import the `app` singleton for the event bus and shared state.
 */

import { SessionTree } from './session-tree.js';
import { SessionDetail } from './session-detail.js';
import { SpanDetail } from './span-detail.js';
import { CgcGraph } from './cgc-graph.js';
import { WorkflowDag } from './workflow-dag.js';

// ---------------------------------------------------------------------------
// EventEmitter (lightweight, no external deps)
// ---------------------------------------------------------------------------
class EventEmitter {
  constructor() { this._handlers = {}; }
  on(event, fn) {
    (this._handlers[event] = this._handlers[event] || []).push(fn);
    return this;
  }
  off(event, fn) {
    if (this._handlers[event]) {
      this._handlers[event] = this._handlers[event].filter(h => h !== fn);
    }
  }
  emit(event, data) {
    (this._handlers[event] || []).forEach(fn => { try { fn(data); } catch (e) { console.error(e); } });
  }
}

// ---------------------------------------------------------------------------
// App singleton
// ---------------------------------------------------------------------------
class App extends EventEmitter {
  constructor() {
    super();
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnect = 5;
    this.health = null;
    this.selectedSessionId = null;
    // Live agent panel state: agent_key (provider:model) → {card el, startedAt, timer}
    this._agentCards = new Map();
  }

  async init() {
    this._renderHeader('connecting');
    this.health = await this._fetchHealth();
    this._renderHeader(this.health ? 'ready' : 'ready');

    // Wire sub-components
    this.sessionTree   = new SessionTree(document.getElementById('session-tree'),   this);
    this.sessionDetail = new SessionDetail(document.getElementById('session-detail'), this);
    this.spanDetail    = new SpanDetail(document.getElementById('span-detail'),      this);
    this.cgcGraph      = new CgcGraph(document.getElementById('cgc-graph-section'),  this);
    this.workflowDag   = new WorkflowDag(document.getElementById('dag-content'),      this);

    // Init all components (registers event listeners) before any auto-selection
    await this.sessionDetail.init();
    await this.spanDetail.init();
    await this.cgcGraph.init();
    await this.workflowDag.init();
    await this.sessionTree.init();  // last: its auto-select fires after all listeners are ready

    this._initTabs();
    this._connectWebSocket();
  }

  // ------------------------------------------------------------------
  // Tab switching
  // ------------------------------------------------------------------
  _initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => this._switchTab(btn.dataset.tab));
    });
  }

  _switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      const active = btn.dataset.tab === tabName;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', String(active));
    });
    document.querySelectorAll('.tab-panel').forEach(panel => {
      const show = panel.id === `tab-${tabName}`;
      panel.hidden = !show;
    });
    if (tabName === 'live') {
      this._activateLiveTab();
    } else if (tabName === 'fleet') {
      this._activateFleetTab();
    } else if (tabName === 'cost') {
      this._activateCostTab();
    } else if (tabName === 'dag') {
      this._activateDagTab();
    }
  }

  // ------------------------------------------------------------------
  // Workflow DAG panel
  // ------------------------------------------------------------------
  async _activateDagTab() {
    if (this.workflowDag) await this.workflowDag.activate();
  }

  // ------------------------------------------------------------------
  // Live agent panel
  // ------------------------------------------------------------------
  async _activateLiveTab() {
    const grid = document.getElementById('live-agents-grid');
    if (!grid) return;
    try {
      const data = await this.fetchJSON('/api/v2/agents/active');
      const agents = data.agents || [];
      // Clear stale cards and rebuild from current API state
      this._agentCards.forEach(({ timer }) => { if (timer) clearTimeout(timer); });
      this._agentCards.clear();
      grid.innerHTML = '';
      if (agents.length === 0) {
        this._renderLiveEmptyState(grid);
      } else {
        agents.forEach(agent => this._upsertAgentCard(agent));
      }
    } catch (err) {
      grid.innerHTML = `<div class="live-empty-state"><p>Could not load active agents.</p><small>${err.message}</small></div>`;
    }
  }

  _renderLiveEmptyState(grid) {
    grid.innerHTML = `
      <div class="live-empty-state" style="grid-column:1/-1">
        <div class="empty-icon">🤖</div>
        <p>No active agents.</p>
        <small>Start a workflow to see live activity.</small>
      </div>`;
  }

  /** Build an agent key matching the server's provider:model format. */
  _agentKey(agent) {
    return `${agent.provider || 'unknown'}:${agent.model || 'unknown'}`;
  }

  _upsertAgentCard(agent) {
    const grid = document.getElementById('live-agents-grid');
    if (!grid) return;

    const key = this._agentKey(agent);
    const existing = this._agentCards.get(key);
    const startedAt = existing ? existing.startedAt : (agent.started_at ? new Date(agent.started_at) : new Date());
    const role = agent.agent_role || agent.model || 'unknown';

    const card = existing ? existing.card : document.createElement('div');
    card.className = 'agent-card';
    card.dataset.agentKey = key;
    card.innerHTML = `
      <div class="agent-card-header">
        <span class="agent-card-dot"></span>
        <span class="agent-role">${_esc(role)}</span>
      </div>
      <div class="agent-card-body">
        <span class="label">Provider</span><span class="value">${_esc(agent.provider || 'unknown')}</span>
        <span class="label">Model</span><span class="value">${_esc(agent.model || 'unknown')}</span>
        <span class="label">Spans</span><span class="value span-count">${agent.span_count ?? 0}</span>
        <span class="label">Task</span><span class="value task-desc">${_esc(agent.task || agent.action_type || '—')}</span>
      </div>
      <div class="agent-duration" data-started="${startedAt.toISOString()}">⏱ —</div>`;

    if (!existing) {
      // Remove empty state if present
      const empty = grid.querySelector('.live-empty-state');
      if (empty) empty.remove();
      grid.prepend(card);
    }

    const durationEl = card.querySelector('.agent-duration');
    const tick = () => {
      const secs = Math.floor((Date.now() - startedAt.getTime()) / 1000);
      const m = Math.floor(secs / 60);
      const s = secs % 60;
      durationEl.textContent = `⏱ ${m > 0 ? m + 'm ' : ''}${s}s`;
    };
    tick();
    const interval = setInterval(tick, 1000);
    this._agentCards.set(key, { card, startedAt, interval });
  }

  _updateAgentCard(event) {
    const key = this._agentKey(event);
    const entry = this._agentCards.get(key);
    if (!entry) {
      // Seen for the first time on this tab — create card
      this._upsertAgentCard({
        agent_role: event.agent_role,
        provider: event.provider,
        model: event.model,
        span_count: event.span_count || 0,
        task: event.action_type,
      });
      return;
    }
    const { card } = entry;
    const spanCountEl = card.querySelector('.span-count');
    if (spanCountEl && event.span_count != null) spanCountEl.textContent = event.span_count;
    const taskEl = card.querySelector('.task-desc');
    if (taskEl && event.action_type) taskEl.textContent = event.action_type;
  }

  _removeAgentCard(event) {
    const key = this._agentKey(event);
    const entry = this._agentCards.get(key);
    if (!entry) return;
    const { card, interval } = entry;
    clearInterval(interval);
    card.classList.add('fading');
    setTimeout(() => {
      card.remove();
      this._agentCards.delete(key);
      const grid = document.getElementById('live-agents-grid');
      if (grid && grid.children.length === 0) this._renderLiveEmptyState(grid);
    }, 5000);
  }

  // ------------------------------------------------------------------
  // Cost / Quality panel
  // ------------------------------------------------------------------
  async _activateCostTab() {
    const container = document.getElementById('cost-content');
    if (!container) return;

    // Cancel any existing refresh timer when re-entering the tab.
    if (this._costRefreshTimer) {
      clearInterval(this._costRefreshTimer);
      this._costRefreshTimer = null;
    }

    const render = async () => {
      // Only refresh while the Cost tab is still visible.
      if (document.getElementById('tab-cost')?.hidden) {
        clearInterval(this._costRefreshTimer);
        this._costRefreshTimer = null;
        return;
      }
      try {
        const [costData, scoresData] = await Promise.all([
          this.fetchJSON('/api/v2/langfuse/session/cost'),
          this.fetchJSON('/api/v2/langfuse/scores'),
        ]);
        container.innerHTML = this._renderCostPanel(costData, scoresData);
      } catch (err) {
        container.innerHTML = `<div class="live-empty-state"><p>Could not load cost data.</p><small>${err.message}</small></div>`;
      }
    };

    await render();
    this._costRefreshTimer = setInterval(render, 30_000);
  }

  _renderCostPanel(costData, scoresData) {
    if (!costData.available) {
      const reason = costData.reason || 'Langfuse not configured';
      return `
        <div class="cost-unconfigured">
          <div class="empty-icon">🔑</div>
          <h3>Configure Langfuse</h3>
          <p>${_esc(reason)}</p>
          <div class="cost-env-instructions">
            <p>Set the following environment variables to enable cost tracking:</p>
            <pre>LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # optional</pre>
          </div>
        </div>`;
    }

    const inputTok  = (costData.total_input_tokens  ?? 0).toLocaleString();
    const outputTok = (costData.total_output_tokens ?? 0).toLocaleString();
    const totalTok  = (costData.total_tokens        ?? 0).toLocaleString();
    const costUsd   = (costData.estimated_cost_usd  ?? 0).toFixed(6);
    const topModels = costData.top_models || [];

    const modelRows = topModels.length
      ? topModels.map(m => `
          <tr>
            <td>${_esc(m.model)}</td>
            <td>${(m.input_tokens ?? 0).toLocaleString()}</td>
            <td>${(m.output_tokens ?? 0).toLocaleString()}</td>
            <td>$${(m.cost_usd ?? 0).toFixed(6)}</td>
          </tr>`).join('')
      : '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No data</td></tr>';

    const scores = scoresData?.available ? (scoresData.scores || []) : [];
    const scoreRows = scores.length
      ? scores.map(s => `
          <tr>
            <td>${_esc(s.name ?? '—')}</td>
            <td>${_esc(String(s.value ?? '—'))}</td>
            <td>${_esc(s.traceId ?? '—')}</td>
          </tr>`).join('')
      : '<tr><td colspan="3" style="text-align:center;color:var(--text-muted)">No scores</td></tr>';

    return `
      <div class="cost-stats-grid">
        <div class="cost-stat-card">
          <div class="cost-stat-value">${inputTok}</div>
          <div class="cost-stat-label">Input tokens</div>
        </div>
        <div class="cost-stat-card">
          <div class="cost-stat-value">${outputTok}</div>
          <div class="cost-stat-label">Output tokens</div>
        </div>
        <div class="cost-stat-card">
          <div class="cost-stat-value">${totalTok}</div>
          <div class="cost-stat-label">Total tokens</div>
        </div>
        <div class="cost-stat-card cost-stat-card--accent">
          <div class="cost-stat-value">$${costUsd}</div>
          <div class="cost-stat-label">Estimated cost (USD)</div>
        </div>
      </div>

      <h4 class="cost-section-title">Top models by cost</h4>
      <table class="cost-table">
        <thead><tr><th>Model</th><th>Input tokens</th><th>Output tokens</th><th>Est. cost</th></tr></thead>
        <tbody>${modelRows}</tbody>
      </table>

      <h4 class="cost-section-title">Recent quality scores</h4>
      <table class="cost-table">
        <thead><tr><th>Name</th><th>Value</th><th>Trace ID</th></tr></thead>
        <tbody>${scoreRows}</tbody>
      </table>
      <p class="cost-refresh-note">Auto-refreshes every 30 s</p>`;
  }

  // ------------------------------------------------------------------
  // Fleet status panel
  // ------------------------------------------------------------------
  async _activateFleetTab() {
    const tbody = document.getElementById('fleet-runs-body');
    const emptyState = document.getElementById('fleet-empty-state');
    if (!tbody) return;
    try {
      const [runsData, tasksData, locksData] = await Promise.all([
        this.fetchJSON('/api/v2/control/runs'),
        this.fetchJSON('/api/v2/control/tasks'),
        this.fetchJSON('/api/v2/control/locks'),
      ]);
      const runs = runsData.runs || [];
      const tasks = tasksData.tasks || [];
      const locks = locksData.locks || [];

      // Build lookup maps
      const taskMap = Object.fromEntries(tasks.map(t => [t.id, t]));
      const locksByRun = {};
      locks.forEach(lk => {
        if (!locksByRun[lk.run_id]) locksByRun[lk.run_id] = [];
        locksByRun[lk.run_id].push(lk);
      });

      tbody.innerHTML = '';
      if (runs.length === 0) {
        emptyState && (emptyState.hidden = false);
      } else {
        emptyState && (emptyState.hidden = true);
      }

      const now = Date.now();
      runs.forEach(run => {
        const agentRole = run.agent_role || '—';
        const taskId = run.task_id || '—';
        const status = run.status || '—';

        const startedMs = run.started_at ? new Date(run.started_at).getTime() : now;
        const elapsedSec = Math.floor((now - startedMs) / 1000);
        const elapsed = elapsedSec < 60
          ? `${elapsedSec}s`
          : `${Math.floor(elapsedSec / 60)}m ${elapsedSec % 60}s`;

        let ttlCell = '—';
        let ttlClass = '';
        if (run.lease_expires_at) {
          const expiresMs = new Date(run.lease_expires_at).getTime();
          const acquiredMs = run.lease_acquired_at ? new Date(run.lease_acquired_at).getTime() : (now - 60000);
          const totalMs = expiresMs - acquiredMs;
          const remainingMs = expiresMs - now;
          const ttlSec = Math.max(0, Math.floor(remainingMs / 1000));
          if (ttlSec === 0) {
            ttlCell = 'expired';
            ttlClass = 'lease-expiry-critical';
          } else {
            ttlCell = `${ttlSec}s`;
            const ratio = totalMs > 0 ? remainingMs / totalMs : 1;
            if (ratio < 0.1) ttlClass = 'lease-expiry-critical';
            else if (ratio < 0.2) ttlClass = 'lease-expiry-warn';
          }
        }

        const releaseBtn = status === 'active'
          ? `<button class="fleet-action-btn release" data-run-id="${this._esc(run.id)}">⏹ Force Release</button>`
          : '';

        const tr = document.createElement('tr');
        tr.dataset.runId = run.id;
        tr.innerHTML = `
          <td>${this._esc(agentRole)}</td>
          <td><code>${this._esc(taskId)}</code></td>
          <td><span class="run-status run-status--${this._esc(status)}">${this._esc(status)}</span></td>
          <td>${elapsed}</td>
          <td class="fleet-ttl ${ttlClass}">${ttlCell}</td>
          <td>${releaseBtn}</td>
        `;
        tbody.appendChild(tr);
      });

      // Wire up Force Release buttons
      tbody.querySelectorAll('.fleet-action-btn.release').forEach(btn => {
        btn.addEventListener('click', () => this._releaseRun(btn.dataset.runId));
      });

      // Render pending gates panel
      const gatesSection = document.getElementById('fleet-gates-section');
      const gatesTbody = document.getElementById('fleet-gates-body');
      if (gatesSection && gatesTbody) {
        const pendingGates = [];
        tasks.forEach(task => {
          const gates = task.gates || [];
          gates.forEach(gate => {
            if (gate.status === 'pending') {
              pendingGates.push({ task, gate });
            }
          });
        });
        gatesSection.hidden = pendingGates.length === 0;
        gatesTbody.innerHTML = '';
        pendingGates.forEach(({ task, gate }) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><code>${this._esc(task.id)}</code></td>
            <td>${this._esc(gate.id)}</td>
            <td>${this._esc(gate.gate_type || gate.type || '—')}</td>
            <td>
              <button class="fleet-action-btn approve"
                      data-task-id="${this._esc(task.id)}"
                      data-gate-id="${this._esc(gate.id)}">✔ Approve</button>
              <button class="fleet-action-btn reject"
                      data-task-id="${this._esc(task.id)}"
                      data-gate-id="${this._esc(gate.id)}">✖ Reject</button>
            </td>
          `;
          gatesTbody.appendChild(tr);
        });
        gatesTbody.querySelectorAll('.fleet-action-btn.approve').forEach(btn => {
          btn.addEventListener('click', () => this._approveGate(btn.dataset.taskId, btn.dataset.gateId));
        });
        gatesTbody.querySelectorAll('.fleet-action-btn.reject').forEach(btn => {
          btn.addEventListener('click', () => this._rejectGate(btn.dataset.taskId, btn.dataset.gateId));
        });
      }

      // Auto-refresh TTL countdown every 5s
      if (this._fleetRefreshTimer) clearInterval(this._fleetRefreshTimer);
      this._fleetRefreshTimer = setInterval(() => {
        if (document.getElementById('tab-fleet') && !document.getElementById('tab-fleet').hidden) {
          this._activateFleetTab();
        } else {
          clearInterval(this._fleetRefreshTimer);
        }
      }, 5000);
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="live-empty-state">Could not load fleet data: ${err.message}</td></tr>`;
    }
  }

  // ------------------------------------------------------------------
  // Toast notifications
  // ------------------------------------------------------------------
  _showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 450);
    }, duration);
  }

  // ------------------------------------------------------------------
  // Fleet management actions
  // ------------------------------------------------------------------
  async _approveGate(taskId, gateId) {
    try {
      const resp = await fetch(`/api/v2/control/gates/${encodeURIComponent(taskId)}/${encodeURIComponent(gateId)}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decided_by: 'dashboard', summary: 'Approved via dashboard' }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        this._showToast(`Approve failed: ${body.error || resp.statusText}`, 'error');
        return;
      }
      this._showToast('Gate approved ✓', 'success');
      this._activateFleetTab();
    } catch (err) {
      this._showToast(`Approve error: ${err.message}`, 'error');
    }
  }

  async _rejectGate(taskId, gateId) {
    try {
      const resp = await fetch(`/api/v2/control/gates/${encodeURIComponent(taskId)}/${encodeURIComponent(gateId)}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decided_by: 'dashboard', summary: 'Rejected via dashboard' }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        this._showToast(`Reject failed: ${body.error || resp.statusText}`, 'error');
        return;
      }
      this._showToast('Gate rejected', 'info');
      this._activateFleetTab();
    } catch (err) {
      this._showToast(`Reject error: ${err.message}`, 'error');
    }
  }

  async _releaseRun(runId) {
    if (!confirm(`Force-release run ${runId}? This will reset the task to pending.`)) return;
    try {
      const resp = await fetch(`/api/v2/control/runs/${encodeURIComponent(runId)}/release`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Force-released via dashboard' }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        this._showToast(`Release failed: ${body.error || resp.statusText}`, 'error');
        return;
      }
      this._showToast('Run released ✓', 'success');
      this._activateFleetTab();
    } catch (err) {
      this._showToast(`Release error: ${err.message}`, 'error');
    }
  }

  _esc(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[c]);
  }

  // ------------------------------------------------------------------
  // WebSocket
  // ------------------------------------------------------------------
  _connectWebSocket() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(`${proto}//${location.host}/ws`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this._setWsStatus('connected');
      this.emit('connected');
    };

    this.ws.onclose = () => {
      this._setWsStatus('disconnected');
      this.emit('disconnected');
      if (this.reconnectAttempts < this.maxReconnect) {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 16000);
        this.reconnectAttempts++;
        setTimeout(() => this._connectWebSocket(), delay);
      }
    };

    this.ws.onerror = () => this._setWsStatus('disconnected');

    this.ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      switch (msg.type) {
        case 'span_added':    this.emit('spanAdded',      msg); break;
        case 'session_start': this.emit('sessionStarted', msg.session); break;
        case 'session_end':   this.emit('sessionEnded',   msg.session_id); break;
        case 'metrics':       this.emit('metrics',        msg.metrics); break;
        // Live agent events
        case 'agent-start':
          this._upsertAgentCard({
            agent_role: msg.agent_role,
            provider: msg.provider,
            model: msg.model,
            span_count: msg.span_count || 0,
            started_at: msg.started_at,
            task: msg.task,
          });
          break;
        case 'agent-step':
          this._updateAgentCard(msg);
          break;
        case 'agent-end':
          this._removeAgentCard(msg);
          break;
      }
    };
  }

  // ------------------------------------------------------------------
  // Header
  // ------------------------------------------------------------------
  _renderHeader(wsState) {
    const el = document.getElementById('app-header');
    el.innerHTML = `
      <h1>🔭 TTA.dev Observability</h1>
      <div class="header-meta">
        <span id="ws-badge" class="ws-badge ${wsState}">
          ${wsState === 'connected' ? '● Connected' : wsState === 'connecting' ? '◌ Connecting' : '○ Disconnected'}
        </span>
        <span id="session-badge" class="session-badge"></span>
      </div>
    `;
  }

  _setWsStatus(state) {
    const badge = document.getElementById('ws-badge');
    if (!badge) return;
    badge.className = `ws-badge ${state}`;
    badge.textContent = state === 'connected' ? '● Connected'
                      : state === 'connecting' ? '◌ Connecting'
                      : '○ Disconnected';
  }

  updateSessionBadge(label) {
    const el = document.getElementById('session-badge');
    if (el) el.textContent = label;
  }

  // ------------------------------------------------------------------
  // API helpers
  // ------------------------------------------------------------------
  async _fetchHealth() {
    try {
      const r = await fetch('/api/v2/health');
      const data = await r.json();
      if (!data.cgc_available) this.emit('cgcUnavailable');
      return data;
    } catch { return null; }
  }

  async fetchJSON(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function _esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Bootstrap
const app = new App();
document.addEventListener('DOMContentLoaded', () => app.init());
export { app };
