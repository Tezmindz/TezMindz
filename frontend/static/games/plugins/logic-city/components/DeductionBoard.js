/**
 * DeductionBoard Component
 * Displays logical reasoning statements, progressive hypothesis checks, and deduction grid.
 */
export class DeductionBoard {
  constructor(clues = [], onClueCheck = null) {
    this.clues = clues;
    this.onClueCheck = onClueCheck;
  }

  render(container) {
    if (!this.clues || this.clues.length === 0) return;

    const board = document.createElement('div');
    board.className = 'tm-deduction-board';
    board.innerHTML = `
      <div class="tm-deduction-header">
        <span>🕵️ Logical Clue Board</span>
      </div>
      <ul class="tm-clues-list">
        ${this.clues.map((c, i) => `
          <li class="tm-clue-item" data-clue-index="${i}">
            <span class="tm-clue-num">${i + 1}</span>
            <span class="tm-clue-text">${this.escapeHtml(c)}</span>
          </li>
        `).join('')}
      </ul>
    `;
    container.appendChild(board);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
