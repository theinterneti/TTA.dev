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
      <div style="font-family:monospace;font-size:.8em;color:var(--text-muted);margin-bottom:12px;">${span.span_id}</div>

      <div class="chain-block">
        <div class="panel-heading" style="font-size:.9em;">Execution Chain</div>
        ${this._chainRow('📡 Provider',   span.provider)}
        ${this._chainRow('🤖 Model',      span.model)}
        ${this._chainRow('🎭 Agent Role', span.agent_role || '(none)')}
        ${this._chainRow('🔄 Workflow',   span.workflow_id || '(direct)')}
        ${this._chainRow('⚙️ Primitive',  span.primitive_type || span.name)}
        ${this._chainRow('⏱️ Duration',   `${(span.duration_ms || 0).toFixed(2)}ms`)}
        ${this._chainRow('📊 Status',     span.status)}
      </div>

      ${Object.keys(span.attributes || {}).length > 0 ? `
        <div class="panel-heading" style="font-size:.9em;margin-top:12px;">Attributes</div>
        <table class="attrs-table">
          <thead><tr><th>Key</th><th>Value</th></tr></thead>
          <tbody>
            ${Object.entries(span.attributes).map(([k, v]) =>
              `<tr><td><code>${k}</code></td><td>${JSON.stringify(v)}</td></tr>`
            ).join('')}
          </tbody>
        </table>
      ` : ''}

      ${span.status === 'error' ? `
        <div class="error-block">
          <strong>Error</strong><br>
          ${span.attributes?.['error.message'] || span.attributes?.['exception.message'] || 'No error details'}
        </div>
      ` : ''}

      <details>
        <summary>Raw JSON</summary>
        <pre>${JSON.stringify(span, null, 2)}</pre>
      </details>
    `;

    this.el.querySelector('.close-btn')
      .addEventListener('click', () => { this.el.setAttribute('hidden', ''); });
  }

  _chainRow(label, value) {
    return `<div class="chain-row"><strong>${label}:</strong> ${value ?? '—'}</div>`;
  }
}
