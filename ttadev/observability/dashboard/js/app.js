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

    // Init all components (registers event listeners) before any auto-selection
    await this.sessionDetail.init();
    await this.spanDetail.init();
    await this.cgcGraph.init();
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
    }
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
        return;
      }
      emptyState && (emptyState.hidden = true);

      const now = Date.now();
      runs.forEach(run => {
        const task = taskMap[run.task_id] || {};
        const agentRole = run.agent_role || '—';
        const taskId = run.task_id || '—';
        const status = run.status || '—';

        const startedMs = run.started_at ? new Date(run.started_at).getTime() : now;
        const elapsedSec = Math.floor((now - startedMs) / 1000);
        const elapsed = elapsedSec < 60
          ? `${elapsedSec}s`
          : `${Math.floor(elapsedSec / 60)}m ${elapsedSec % 60}s`;

        let ttlCell = '—';
        if (run.lease_expires_at) {
          const expiresMs = new Date(run.lease_expires_at).getTime();
          const ttlSec = Math.max(0, Math.floor((expiresMs - now) / 1000));
          ttlCell = ttlSec > 0 ? `${ttlSec}s` : 'expired';
        }

        const tr = document.createElement('tr');
        tr.dataset.runId = run.id;
        tr.innerHTML = `
          <td>${this._esc(agentRole)}</td>
          <td><code>${this._esc(taskId)}</code></td>
          <td><span class="run-status run-status--${this._esc(status)}">${this._esc(status)}</span></td>
          <td>${elapsed}</td>
          <td class="fleet-ttl">${ttlCell}</td>
        `;
        tbody.appendChild(tr);
      });

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
      tbody.innerHTML = `<tr><td colspan="5" class="live-empty-state">Could not load fleet data: ${err.message}</td></tr>`;
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
