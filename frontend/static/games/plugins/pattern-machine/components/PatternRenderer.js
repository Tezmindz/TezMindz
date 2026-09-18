/**
 * PatternRenderer Component
 * Renders the conveyor sequence with animated gears or tiles.
 */
export class PatternRenderer {
  constructor(sequence = [], missingIndex = -1) {
    this.sequence = sequence;
    this.missingIndex = missingIndex;
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-conveyor-belt';

    const tilesHtml = this.sequence.map((item, idx) => {
      const isMissing = idx === this.missingIndex || item === '?';
      return `
        <div class="tm-pattern-node ${isMissing ? 'tm-node-missing' : ''}" data-index="${idx}">
          <span class="tm-node-index">#${idx + 1}</span>
          <span class="tm-node-content">${isMissing ? '?' : this.escapeHtml(item)}</span>
        </div>
      `;
    }).join('<div class="tm-pattern-connector">→</div>');

    this.container.innerHTML = `
      <div class="tm-belt-track">
        ${tilesHtml}
      </div>
    `;

    parentElement.appendChild(this.container);
  }

  fillMissingSlot(value, isCorrect) {
    const missingNode = this.container.querySelector('.tm-node-missing');
    if (!missingNode) return;

    const contentSpan = missingNode.querySelector('.tm-node-content');
    if (contentSpan) {
      contentSpan.textContent = value;
    }

    if (isCorrect) {
      missingNode.classList.add('tm-node-filled-correct');
    } else {
      missingNode.classList.add('tm-node-filled-wrong');
    }
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
