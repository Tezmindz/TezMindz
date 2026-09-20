/**
 * DivisibilityScanner Component
 * Interactive clue checker for multi-digit conditions and divisibility rules.
 */
export class DivisibilityScanner {
  constructor(clues = [], candidates = []) {
    this.clues = clues;
    this.candidates = candidates;
  }

  render(container) {
    if (!this.clues || this.clues.length === 0) return;

    const wrap = document.createElement('div');
    wrap.className = 'tm-scanner-card';
    wrap.innerHTML = `
      <div class="tm-scanner-title">👑 Royal Clue Scrolls</div>
      <div class="tm-scanner-list">
        ${this.clues.map((clue, idx) => `
          <div class="tm-scanner-item">
            <span class="tm-scanner-badge">Clue ${idx + 1}</span>
            <span class="tm-scanner-text">${this.escapeHtml(clue)}</span>
          </div>
        `).join('')}
      </div>
    `;
    container.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
