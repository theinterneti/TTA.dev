/**
 * session-tree.js — Sessions sidebar component.
 * Renders "All Sessions" at top, then project groups (collapsible),
 * then ungrouped sessions, newest-first.
 */

export class SessionTree {
  constructor(el, app) {
    this.el = el;
    this.app = app;
    this.sessions = [];
    this.projects = [];
  }

  async init() {
    await this._load();
    this.app.on('sessionStarted', (session) => this._prependSession(session));
    this.app.on('sessionEnded',   (id)      => this._markEnded(id));
  }

  async _load() {
    try {
      [this.sessions, this.projects] = await Promise.all([
        this.app.fetchJSON('/api/v2/sessions'),
        this.app.fetchJSON('/api/v2/projects').catch(() => []),
      ]);
      this._render();
      // Default to "All Sessions" — shows everything across all agents
      this._select('all');
    } catch {
      this.el.innerHTML = `<div class="empty-state" style="padding:20px;font-size:.85em;">Could not load sessions</div>`;
    }
  }

  _render() {
    this.el.innerHTML = `<div class="sidebar-heading">Sessions</div>`;

    // "All Sessions" virtual entry — always first
    this.el.appendChild(this._makeAllItem());

    if (this.sessions.length === 0) {
      this.el.innerHTML += `<div style="padding:12px 16px;font-size:.85em;color:var(--text-muted)">No sessions yet</div>`;
      return;
    }

    // Build project lookup map: id → project
    const projectMap = new Map(this.projects.map(p => [p.id, p]));

    // Partition sessions: grouped vs ungrouped
    const grouped = new Map(); // project_id → session[]
    const ungrouped = [];
    for (const s of this.sessions) {
      if (s.project_id && projectMap.has(s.project_id)) {
        if (!grouped.has(s.project_id)) grouped.set(s.project_id, []);
        grouped.get(s.project_id).push(s);
      } else {
        ungrouped.push(s);
      }
    }

    // Render project groups
    for (const [projId, sessions] of grouped) {
      const proj = projectMap.get(projId);
      this.el.appendChild(this._makeProjectGroup(proj, sessions));
    }

    // Render ungrouped sessions
    ungrouped.forEach(s => this.el.appendChild(this._makeItem(s)));
  }

  _makeProjectGroup(proj, sessions) {
    const group = document.createElement('div');
    group.className = 'session-project-group';
    group.dataset.projectId = proj.id;

    const header = document.createElement('div');
    header.className = 'session-project-header';
    header.innerHTML = `
      <span class="project-toggle">▾</span>
      <span class="project-icon">🗂</span>
      <span class="project-name">${this._escapeHtml(proj.name)}</span>
      <span class="project-count">${sessions.length}</span>
    `;

    const body = document.createElement('div');
    body.className = 'session-project-body';
    sessions.forEach(s => body.appendChild(this._makeItem(s)));

    // Toggle collapse on header click
    header.addEventListener('click', () => {
      const collapsed = body.classList.toggle('collapsed');
      header.querySelector('.project-toggle').textContent = collapsed ? '▸' : '▾';
    });

    group.appendChild(header);
    group.appendChild(body);
    return group;
  }

  _makeAllItem() {
    const div = document.createElement('div');
    div.className = 'session-item session-all';
    div.dataset.id = 'all';
    div.innerHTML = `
      <span class="session-dot" style="background:var(--accent);box-shadow:0 0 6px var(--accent)"></span>
      <div class="session-info">
        <div class="session-tool">🌐 All Sessions</div>
        <div class="session-meta">${this.sessions.length} session${this.sessions.length !== 1 ? 's' : ''}</div>
      </div>
    `;
    div.addEventListener('click', () => this._select('all'));
    return div;
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
    // Update the "all" item's session count
    const allItem = this.el.querySelector('[data-id="all"] .session-meta');
    if (allItem) allItem.textContent = `${this.sessions.length} sessions`;
    // Insert new session item after the "all" item (before any project groups)
    const allEl = this.el.querySelector('[data-id="all"]');
    const item = this._makeItem(session);
    if (allEl?.nextSibling) {
      this.el.insertBefore(item, allEl.nextSibling);
    } else {
      this.el.appendChild(item);
    }
    // Don't auto-switch away from current selection
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

  _escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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
