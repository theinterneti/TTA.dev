/**
 * span-detail.js — Slide-in detail panel for a single span.
 */

export class SpanDetail {
  constructor(el, app) {
    this.el = el;
    this.app = app;
  }

  init() {
    this.app.on('spanSelected', (span) => this._show(span));
    return Promise.resolve();
  }

  _show(span) {
    this.el.removeAttribute('hidden');
    this.el.innerHTML = `
      <button class="close-btn" aria-label="Close">&times;</button>
      <div class="panel-heading">Span Detail</div>
      <div style="font-family:monospace;font-size:.8em;color:var(--text-muted);margin-bottom:12px;"></div>

      <div class="chain-block">
        <div class="panel-heading" style="font-size:.9em;">Execution Chain</div>
        ${this._chainRow('📡 Provider',   span.provider)}
        ${this._chainRow('🤖 Model',      span.model)}
        ${span.agent_role ? this._chainRow('🎭 Agent Role', span.agent_role) : ''}
        ${span.workflow_id ? this._chainRow('🔄 Workflow', span.workflow_id) : ''}
        ${span.primitive_type ? this._chainRow('⚙️ Primitive', span.primitive_type) : ''}
        ${this._chainRow('⏱️ Duration', span.duration_ms > 0 ? `${span.duration_ms.toFixed(2)}ms` : '—')}
        ${this._chainRow('📊 Status',     span.status)}
      </div>

      ${Object.keys(span.attributes || {}).length > 0 ? `
        <div class="panel-heading" style="font-size:.9em;margin-top:12px;">Attributes</div>
        <table class="attrs-table">
          <thead><tr><th>Key</th><th>Value</th></tr></thead>
          <tbody id="span-attrs-body"></tbody>
        </table>
      ` : ''}

      <div id="span-error-block" style="display:none;"></div>

      <details>
        <summary>Raw JSON</summary>
        <pre id="span-raw-json"></pre>
      </details>
    `;

    // Set span_id safely via textContent (no XSS risk)
    this.el.querySelector('div[style*="monospace"]').textContent = span.span_id;

    // Populate attributes table safely
    const tbody = this.el.querySelector('#span-attrs-body');
    if (tbody) {
      for (const [k, v] of Object.entries(span.attributes || {})) {
        const tr = document.createElement('tr');
        const tdKey = document.createElement('td');
        const code = document.createElement('code');
        code.textContent = k;
        tdKey.appendChild(code);
        const tdVal = document.createElement('td');
        tdVal.textContent = JSON.stringify(v);
        tr.appendChild(tdKey);
        tr.appendChild(tdVal);
        tbody.appendChild(tr);
      }
    }

    // Error block
    if (span.status === 'error') {
      const errBlock = this.el.querySelector('#span-error-block');
      errBlock.style.display = '';
      errBlock.className = 'error-block';
      const msg = span.attributes?.['error.message']
        || span.attributes?.['exception.message']
        || 'No error details';
      const strong = document.createElement('strong');
      strong.textContent = 'Error';
      errBlock.appendChild(strong);
      errBlock.appendChild(document.createTextNode(': ' + msg));
    }

    // Raw JSON — safe: pre-escaped by JSON.stringify, set via textContent
    const pre = this.el.querySelector('#span-raw-json');
    if (pre) pre.textContent = JSON.stringify(span, null, 2);

    this.el.querySelector('.close-btn')
      .addEventListener('click', () => { this.el.setAttribute('hidden', ''); });
  }

  _chainRow(label, value) {
    const div = document.createElement('div');
    div.className = 'chain-row';
    div.innerHTML = `<strong>${label}:</strong> `;
    div.appendChild(document.createTextNode(value ?? '—'));
    return div.outerHTML;
  }
}
