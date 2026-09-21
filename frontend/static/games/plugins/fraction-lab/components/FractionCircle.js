/**
 * FractionCircle Component
 * Interactive SVG circle partitioned into equal slices with tap/click toggle
 */
export class FractionCircle {
  constructor(numerator = 1, denominator = 4, sliceColor = '#ec4899', options = {}) {
    this.numerator = numerator;
    this.denominator = Math.max(1, denominator);
    this.sliceColor = sliceColor;
    this.interactive = options.interactive ?? true;
    this.onChange = options.onChange || null;

    // Track which slice indices are selected
    this.selectedIndices = Array.from({ length: Math.min(this.denominator, Math.max(0, this.numerator)) }, (_, i) => i);
    this.wrap = null;
  }

  render(parentElement) {
    this.wrap = document.createElement('div');
    this.wrap.className = 'tm-fraction-display';

    this.updateSVG();
    parentElement.appendChild(this.wrap);
  }

  getSlicePath(index, total) {
    const anglePerSlice = (2 * Math.PI) / total;
    const startAngle = index * anglePerSlice - Math.PI / 2;
    const endAngle = (index + 1) * anglePerSlice - Math.PI / 2;
    const r = 85;
    const cx = 100;
    const cy = 100;

    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);

    const largeArc = anglePerSlice > Math.PI ? 1 : 0;
    return `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`;
  }

  toggleSlice(index) {
    if (!this.interactive) return;

    if (this.selectedIndices.includes(index)) {
      this.selectedIndices = this.selectedIndices.filter(i => i !== index);
    } else {
      this.selectedIndices.push(index);
    }

    this.updateSVG();

    if (typeof this.onChange === 'function') {
      this.onChange({
        selectedCount: this.selectedIndices.length,
        totalCount: this.denominator,
        fractionStr: `${this.selectedIndices.length}/${this.denominator}`
      });
    }
  }

  setCount(count) {
    const safeCount = Math.min(this.denominator, Math.max(0, count));
    this.selectedIndices = Array.from({ length: safeCount }, (_, i) => i);
    this.updateSVG();
  }

  updateSVG() {
    if (!this.wrap) return;

    const radius = 85;
    const cx = 100;
    const cy = 100;
    const total = this.denominator;
    const shadedCount = this.selectedIndices.length;

    let paths = '';
    const sliceAngle = (2 * Math.PI) / total;

    for (let i = 0; i < total; i++) {
      const isSelected = this.selectedIndices.includes(i);
      const fillColor = isSelected ? this.sliceColor : '#f8fafc';
      const strokeColor = '#cbd5e1';

      if (total === 1) {
        paths += `
          <circle cx="${cx}" cy="${cy}" r="${radius}" fill="${isSelected ? this.sliceColor : '#f1f5f9'}" stroke="${strokeColor}" stroke-width="2" class="tm-slice-interactive" data-idx="${i}" />
        `;
      } else {
        paths += `
          <path d="${this.getSlicePath(i, total)}" fill="${fillColor}" stroke="${strokeColor}" stroke-width="2" class="tm-slice-interactive" data-idx="${i}" style="cursor: pointer; transition: fill 0.2s;" />
        `;
      }
    }

    this.wrap.innerHTML = `
      <div class="tm-fraction-circle-container">
        <svg viewBox="0 0 200 200" width="200" height="200" class="tm-fraction-svg">
          <circle cx="${cx}" cy="${cy}" r="${radius + 4}" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />
          ${paths}
          <circle cx="${cx}" cy="${cy}" r="6" fill="#64748b" />
        </svg>
        <div class="tm-fraction-badge">
          <span class="tm-fraction-shaded-text">${shadedCount} / ${total} Shaded</span>
        </div>
      </div>
    `;

    // Attach listeners
    this.wrap.querySelectorAll('.tm-slice-interactive').forEach(el => {
      el.addEventListener('click', (e) => {
        const idx = parseInt(el.getAttribute('data-idx'), 10);
        this.toggleSlice(idx);
      });
    });
  }
}
