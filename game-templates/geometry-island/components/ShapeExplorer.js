/**
 * ShapeExplorer Component
 * Renders SVG geometric shapes (rectangles, triangles, regular polygons, grids) dynamically from data.
 */
export class ShapeExplorer {
  constructor(shapeData = {}) {
    this.shapeData = Object.assign({
      type: 'RECTANGLE',
      width: 12,
      height: 8,
      unit: 'cm',
      sides: []
    }, shapeData);
  }

  render(container) {
    const wrap = document.createElement('div');
    wrap.className = 'tm-shape-explorer';

    const type = (this.shapeData.type || 'RECTANGLE').toUpperCase();
    const w = this.shapeData.width || 14;
    const h = this.shapeData.height || 8;
    const unit = this.shapeData.unit || 'cm';

    let svgContent = '';

    if (type === 'RECTANGLE' || type === 'SQUARE') {
      svgContent = `
        <svg viewBox="0 0 240 160" width="100%" height="150" class="tm-geo-svg">
          <rect x="40" y="30" width="160" height="90" rx="4" fill="#ecfdf5" stroke="#10b981" stroke-width="3" />
          <!-- Top Label -->
          <text x="120" y="22" text-anchor="middle" font-size="12" font-weight="700" fill="#047857">${w} ${unit}</text>
          <!-- Bottom Label -->
          <text x="120" y="136" text-anchor="middle" font-size="12" font-weight="700" fill="#047857">${w} ${unit}</text>
          <!-- Left Label -->
          <text x="30" y="80" text-anchor="end" font-size="12" font-weight="700" fill="#047857">${h} ${unit}</text>
          <!-- Right Label -->
          <text x="210" y="80" text-anchor="start" font-size="12" font-weight="700" fill="#047857">${h} ${unit}</text>
        </svg>
      `;
    } else if (type === 'TRIANGLE') {
      svgContent = `
        <svg viewBox="0 0 240 160" width="100%" height="150" class="tm-geo-svg">
          <polygon points="120,25 40,130 200,130" fill="#ecfdf5" stroke="#10b981" stroke-width="3" />
          <text x="120" y="146" text-anchor="middle" font-size="12" font-weight="700" fill="#047857">Base = ${w} ${unit}</text>
        </svg>
      `;
    } else {
      svgContent = `
        <svg viewBox="0 0 240 160" width="100%" height="150" class="tm-geo-svg">
          <rect x="50" y="30" width="140" height="90" fill="#ecfdf5" stroke="#10b981" stroke-width="2" />
          <text x="120" y="80" text-anchor="middle" font-size="13" font-weight="700" fill="#047857">Composite Polygon</text>
        </svg>
      `;
    }

    wrap.innerHTML = `
      <div class="tm-svg-box">${svgContent}</div>
      <div class="tm-shape-meta">
        <span class="tm-meta-badge">Shape: ${type}</span>
        <span class="tm-meta-badge">Dimensions: ${w} × ${h} ${unit}</span>
      </div>
    `;

    container.appendChild(wrap);
  }
}
