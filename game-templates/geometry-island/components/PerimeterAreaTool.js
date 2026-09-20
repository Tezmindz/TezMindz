/**
 * PerimeterAreaTool Component
 * Interactive boundary highlighter and formula summary.
 */
export class PerimeterAreaTool {
  constructor(sides = [], unit = 'cm') {
    this.sides = sides;
    this.unit = unit;
  }

  render(container) {
    const box = document.createElement('div');
    box.className = 'tm-perimeter-tool';

    const sum = this.sides.reduce((acc, s) => acc + Number(s || 0), 0);

    box.innerHTML = `
      <div class="tm-tool-header">📏 Boundary Walk Calculation:</div>
      <div class="tm-sides-row">
        ${this.sides.map((s, idx) => `
          <span class="tm-side-chip">Side ${idx + 1}: ${s} ${this.unit}</span>
        `).join('')}
      </div>
      ${sum > 0 ? `<div class="tm-sum-line">Total Boundary Perimeter = ${sum} ${this.unit}</div>` : ''}
    `;

    container.appendChild(box);
  }
}
