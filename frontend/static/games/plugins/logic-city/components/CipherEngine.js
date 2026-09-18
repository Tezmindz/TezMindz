/**
 * CipherEngine Component
 * Renders data-driven sequence items, highlight states, and cipher clues.
 */
export class CipherEngine {
  constructor(sequence = [], missingIndex = -1, rules = []) {
    this.sequence = sequence;
    this.missingIndex = missingIndex;
    this.rules = rules;
  }

  render(container) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tm-cipher-wrapper';

    // 1. Sequence Row
    const row = document.createElement('div');
    row.className = 'tm-cipher-row';

    this.sequence.forEach((item, index) => {
      const cell = document.createElement('div');
      cell.className = 'tm-cipher-cell';

      if (index === this.missingIndex) {
        cell.classList.add('tm-cell-missing');
        cell.innerHTML = `
          <span class="tm-cell-label">Term ${index + 1}</span>
          <span class="tm-cell-value">?</span>
        `;
      } else {
        cell.innerHTML = `
          <span class="tm-cell-label">Term ${index + 1}</span>
          <span class="tm-cell-value">${this.escapeHtml(item)}</span>
        `;
      }

      row.appendChild(cell);

      if (index < this.sequence.length - 1) {
        const arrow = document.createElement('div');
        arrow.className = 'tm-cipher-arrow';
        arrow.innerHTML = '➔';
        row.appendChild(arrow);
      }
    });

    wrapper.appendChild(row);

    // 2. Cipher Transformation Rules if provided
    if (this.rules && this.rules.length > 0) {
      const rulesCard = document.createElement('div');
      rulesCard.className = 'tm-cipher-rules';
      rulesCard.innerHTML = `
        <div class="tm-rules-title">🔑 Observed Transformation Mechanics:</div>
        <div class="tm-rules-grid">
          ${this.rules.map(r => `
            <div class="tm-rule-chip">
              <strong>${this.escapeHtml(r.source || 'Pattern')}:</strong>
              <span>${this.escapeHtml(r.target || '')}</span>
            </div>
          `).join('')}
        </div>
      `;
      wrapper.appendChild(rulesCard);
    }

    container.appendChild(wrapper);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
