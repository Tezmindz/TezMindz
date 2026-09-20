/**
 * ScaleBeam Component
 * Renders the visual dual-pan balance scale
 */
export class ScaleBeam {
  constructor(leftPanData = {}, rightPanData = {}) {
    this.leftPanData = leftPanData;
    this.rightPanData = rightPanData;
  }

  render(parentElement) {
    const scaleWrap = document.createElement('div');
    scaleWrap.className = 'tm-balance-stage';

    const leftItems = (this.leftPanData.items || []).map(i => `<span class="tm-pan-item tm-item-left">${this.escapeHtml(i)}</span>`).join('');
    const rightItems = (this.rightPanData.items || []).map(i => `<span class="tm-pan-item tm-item-right">${this.escapeHtml(i)}</span>`).join('');

    scaleWrap.innerHTML = `
      <div class="tm-scale-fulcrum">
        <div class="tm-scale-beam">
          <!-- Left Pan -->
          <div class="tm-pan-assembly tm-pan-left">
            <div class="tm-pan-string"></div>
            <div class="tm-pan-dish">
              <div class="tm-dish-items">${leftItems}</div>
            </div>
          </div>

          <!-- Fulcrum Pivot -->
          <div class="tm-pivot-point">▲</div>

          <!-- Right Pan -->
          <div class="tm-pan-assembly tm-pan-right">
            <div class="tm-pan-string"></div>
            <div class="tm-pan-dish">
              <div class="tm-dish-items">${rightItems}</div>
            </div>
          </div>
        </div>
        <div class="tm-scale-stand"></div>
        <div class="tm-scale-base"></div>
      </div>
    `;

    parentElement.appendChild(scaleWrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
