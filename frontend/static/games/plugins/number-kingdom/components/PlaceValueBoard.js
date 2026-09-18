/**
 * PlaceValueBoard Component
 * Visualizes Thousands, Hundreds, Tens, Ones blocks and expanded form.
 */
export class PlaceValueBoard {
  constructor(digits = {}) {
    this.digits = Object.assign({
      thousands: 0,
      hundreds: 0,
      tens: 0,
      ones: 0
    }, digits);
  }

  render(container) {
    const board = document.createElement('div');
    board.className = 'tm-pv-board';

    const cols = [
      { key: 'thousands', label: 'Thousands (1000)', val: this.digits.thousands, color: '#f59e0b' },
      { key: 'hundreds', label: 'Hundreds (100)', val: this.digits.hundreds, color: '#3b82f6' },
      { key: 'tens', label: 'Tens (10)', val: this.digits.tens, color: '#10b981' },
      { key: 'ones', label: 'Ones (1)', val: this.digits.ones, color: '#ec4899' }
    ];

    board.innerHTML = `
      <div class="tm-pv-grid">
        ${cols.map(c => `
          <div class="tm-pv-col" style="border-top: 3px solid ${c.color}">
            <div class="tm-pv-label">${c.label}</div>
            <div class="tm-pv-digit">${c.val !== undefined ? c.val : '-'}</div>
            <div class="tm-pv-value">${c.val ? (c.val * (c.key === 'thousands' ? 1000 : c.key === 'hundreds' ? 100 : c.key === 'tens' ? 10 : 1)) : 0}</div>
          </div>
        `).join('')}
      </div>
    `;

    container.appendChild(board);
  }
}
