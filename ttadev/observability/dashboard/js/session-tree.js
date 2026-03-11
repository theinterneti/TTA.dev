/**
 * session-tree.js — Sessions sidebar component.
 * Renders the list of sessions newest-first with live indicator.
 */

export class SessionTree {
  constructor(el, app) {
    this.el = el;
    this.app = app;
    this.sessions = [];
  }

  async init() {
    await this._load();
    this.app.on('sessionStarted', (session) => this._prependSession(session));
    this.app.on('sessionEnded',   (id)      => this._markEnded(id));
  }

  async _load() {
    try {
      this.sessions = await this.app.fetchJSON('/api/v2/sessions');
      this._render();
      // Auto-select the most recent (first) session
      if (this.sessions.length > 0) {
        this._select(this.sessions[0].id);
      }
    } catch (e) {
      this.el.innerHTML = `<div class="empty-state" style="padding:20px;font-size:.85em;">Could not load sessions</div>`;
    }
  }

  _render() {
    this.el.innerHTML = `<div class="sidebar-heading">Sessions</div>`;
    if (this.sessions.length === 0) {
      this.el.innerHTML += `<div style="padding:12px 16px;font-size:.85em;color:var(--text-muted)">No sessions yet</div>`;
      return;
    }
    this.sessions.forEach(s => this.el.appendChild(this._makeItem(s)));
  }

  _makeItem(session) {
    const isLive = !session.ended_at;
    const tool   = session.agent_tool || 'unknown';
    const ago    = this._relativeTime(session.started_at);
    const dur    = this._duration(session.started_at, session.ended_at);

    const div = document.createElement('div');
    div.className = 'session-item';
    div.dataset.id = session.id;
    div.innerHTML = `
      <span class="session-dot ${isLive ? 'live' : ''}"></span>
      <div class="session-info">
        <div class="session-tool">${this._toolIcon(tool)} ${tool}</div>
        <div class="session-meta">${ago} · ${dur}</div>
      </div>
    `;
    div.addEventListener('click', () => this._select(session.id));
    return div;
  }

  _select(id) {
    this.el.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    const item = this.el.querySelector(`[data-id="${id}"]`);
    if (item) item.classList.add('active');
    this.app.selectedSessionId = id;
    this.app.emit('sessionSelected', id);
  }

  _prependSession(session) {
    this.sessions.unshift(session);
    const item = this._makeItem(session);
    const heading = this.el.querySelector('.sidebar-heading');
    if (heading) {
      this.el.insertBefore(item, heading.nextSibling);
    } else {
      this.el.prepend(item);
    }
    this._select(session.id);
  }

  _markEnded(id) {
    const item = this.el.querySelector(`[data-id="${id}"]`);
    if (item) {
      item.querySelector('.session-dot')?.classList.remove('live');
      const session = this.sessions.find(s => s.id === id);
      if (session) session.ended_at = new Date().toISOString();
    }
  }

  _toolIcon(tool) {
    const icons = { 'claude-code': '🤖', 'copilot': '✈️', 'cline': '🔧', 'unknown': '❓' };
    return icons[tool] || '❓';
  }

  _relativeTime(iso) {
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  }

  _duration(start, end) {
    const ms = (end ? new Date(end) : new Date()).getTime() - new Date(start).getTime();
    const m = Math.floor(ms / 60000);
    if (m < 1) return '<1m';
    if (m < 60) return `${m}m`;
    return `${Math.floor(m / 60)}h ${m % 60}m`;
  }
}
