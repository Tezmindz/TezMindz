/**
 * FractionCircle Component
 * Generates an SVG circle partitioned into equal slices with shaded portions
 */
export class FractionCircle {
  constructor(numerator = 1, denominator = 4, sliceColor = '#ec4899') {
    this.numerator = numerator;
    this.denominator = denominator;
    this.sliceColor = sliceColor;
  }

  render(parentElement) {
    const wrap = document.createElement('div');
    wrap.className = 'tm-fraction-display';

    const radius = 80;
    const cx = 100;
    const cy = 100;
    const total = Math.max(1, this.denominator);
    const shaded = Math.min(total, Math.max(0, this.numerator));

    let paths = '';
    const sliceAngle = (2 * Math.PI) / total;

    for (let i = 0; i < total; i++) {
      const startAngle = i * sliceAngle - Math.PI / 2;
      const endAngle = (i + 1) * sliceAngle - Math.PI / 2;
      const x1 = cx + radius * Math.cos(startAngle);
      const y1 = cy + radius * Math.sin(startAngle);
      const x2 = cx + radius * Math.cos(endAngle);
      const y2 = cy + radius * Math.sin(endAngle);
      const largeArc = sliceAngle > Math.PI ? 1 : 0;

      const pathData = total === 1 
        ? `<circle cx="${cx}" cy="${cy}" r="${radius}" fill="${shaded >= 1 ? this.sliceColor : '#f1f5f9'}" stroke="#cbd5e1" stroke-width="2"/>`
        : `<path d="M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z" fill="${i < shaded ? this.sliceColor : '#f8fafc'}" stroke="#cbd5e1" stroke-width="2" />`;

      paths += pathData;
    }

    wrap.innerHTML = `
      <svg viewBox="0 0 200 200" width="180" height="180" class="tm-fraction-svg">
        ${paths}
      </svg>
      <div class="tm-fraction-badge">
        <span>${shaded} / ${total} Shaded</span>
      </div>
    `;

    parentElement.appendChild(wrap);
  }
}
