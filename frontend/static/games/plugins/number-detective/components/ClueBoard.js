/**
 * ClueBoard Component
 * Renders the detective mystery clues with checkable progress.
 */
export class ClueBoard {
  constructor(clues = []) {
    this.clues = clues;
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-clue-board';

    this.container.innerHTML = `
      <div class="tm-clue-board-header">
        <span class="tm-clue-badge">🔍 Detective Case Clues</span>
      </div>
      <ul class="tm-clue-list">
        ${this.clues.map((clue, idx) => `
          <li class="tm-clue-item" data-clue-index="${idx}">
            <span class="tm-clue-marker">Clue #${idx + 1}</span>
            <span class="tm-clue-text">${this.escapeHtml(clue)}</span>
          </li>
        `).join('')}
      </ul>
    `;

    parentElement.appendChild(this.container);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
