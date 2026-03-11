/**
 * app.js — Main controller
 * Owns: WebSocket connection, EventEmitter, header rendering.
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

    this._connectWebSocket();
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

// Bootstrap
const app = new App();
document.addEventListener('DOMContentLoaded', () => app.init());
export { app };
