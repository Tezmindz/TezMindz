/**
 * ShapeCanvas Component
 * Renders 2D geometric shapes (polygons, rectangles, triangles) with dimension annotations
 */
export class ShapeCanvas {
  constructor(shapeData = {}) {
    this.shapeData = shapeData;
  }

  render(parentElement) {
    const wrap = document.createElement('div');
    wrap.className = 'tm-geometry-stage';

    const type = (this.shapeData.type || 'RECTANGLE').toUpperCase();
    const dims = this.shapeData.dimensions || { width: 14, height: 9 };
    const measurements = this.shapeData.measurements || [];

    let svgInner = '';
    if (type === 'RECTANGLE') {
      svgInner = `
        <rect x="50" y="40" width="180" height="110" fill="#eff6ff" stroke="#3b82f6" stroke-width="3" rx="6"/>
        <text x="140" y="30" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e40af">Width: ${dims.width || 14} cm</text>
        <text x="35" y="100" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e40af" transform="rotate(-90 35 100)">Height: ${dims.height || 9} cm</text>
      `;
    } else if (type === 'TRIANGLE') {
      svgInner = `
        <polygon points="140,30 50,160 230,160" fill="#fef3c7" stroke="#d97706" stroke-width="3"/>
        <text x="140" y="180" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309">Base: ${dims.base || 12} cm</text>
      `;
    } else {
      svgInner = `
        <polygon points="140,25 210,65 210,145 140,185 70,145 70,65" fill="#f0fdf4" stroke="#16a34a" stroke-width="3"/>
        <text x="140" y="110" text-anchor="middle" font-size="13" font-weight="bold" fill="#15803d">Regular Hexagon</text>
      `;
    }

    const labelsHtml = measurements.map(m => `<span class="tm-measurement-pill">${this.escapeHtml(m)}</span>`).join('');

    wrap.innerHTML = `
      <svg viewBox="0 0 280 200" width="240" height="170" class="tm-geometry-svg">
        ${svgInner}
      </svg>
      <div class="tm-measurements-row">
        ${labelsHtml}
      </div>
    `;

    parentElement.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
