/**
 * ScaleBeam Component
 * Renders an interactive dual-pan balance scale with dynamic physics-based beam tilting,
 * weight adding/removing, and real-time equilibrium validation.
 */
export class ScaleBeam {
  constructor(leftPanData = {}, rightPanData = {}, options = {}) {
    this.initialLeftItems = leftPanData.items || ["⭐", "5 kg"];
    this.initialRightItems = rightPanData.items || ["15 kg"];
    this.initialLeftWeight = leftPanData.weight !== undefined ? leftPanData.weight : 10;
    this.initialRightWeight = rightPanData.weight !== undefined ? rightPanData.weight : 15;

    this.leftItems = [...this.initialLeftItems];
    this.rightItems = [...this.initialRightItems];
    this.leftWeight = this.initialLeftWeight;
    this.rightWeight = this.initialRightWeight;

    this.unit = options.unit || 'kg';
    this.onChange = options.onChange || (() => {});
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-balance-stage';
    this.renderInternal();
    parentElement.appendChild(this.container);
  }

  addWeightToLeft(amount, label = null) {
    this.leftWeight += amount;
    this.leftItems.push(label || `+${amount} ${this.unit}`);
    this.renderInternal();
    this.notifyChange();
  }

  addWeightToRight(amount, label = null) {
    this.rightWeight += amount;
    this.rightItems.push(label || `+${amount} ${this.unit}`);
    this.renderInternal();
    this.notifyChange();
  }

  resetScale() {
    this.leftItems = [...this.initialLeftItems];
    this.rightItems = [...this.initialRightItems];
    this.leftWeight = this.initialLeftWeight;
    this.rightWeight = this.initialRightWeight;
    this.renderInternal();
    this.notifyChange();
  }

  notifyChange() {
    this.onChange({
      leftWeight: this.leftWeight,
      rightWeight: this.rightWeight,
      isBalanced: this.leftWeight === this.rightWeight,
      diff: Math.abs(this.leftWeight - this.rightWeight)
    });
  }

  renderInternal() {
    if (!this.container) return;

    // Calculate beam tilt: positive tilt means right is heavier (right goes down), negative means left is heavier
    const diff = this.rightWeight - this.leftWeight;
    const tiltAngle = Math.max(-14, Math.min(14, diff * 2.2));
    const isBalanced = this.leftWeight === this.rightWeight;

    this.container.innerHTML = `
      <div class="tm-scale-fulcrum">
        <div class="tm-scale-header-bar">
          <span class="tm-scale-indicator-badge ${isBalanced ? 'status-balanced' : 'status-tilted'}">
            ${isBalanced 
              ? `⚖️ Balanced! (${this.leftWeight} ${this.unit} == ${this.rightWeight} ${this.unit})` 
              : diff > 0 
                ? `⬇️ Right pan is heavier by ${diff} ${this.unit}` 
                : `⬇️ Left pan is heavier by ${Math.abs(diff)} ${this.unit}`}
          </span>
          <button type="button" class="btn-scale-reset" id="tm-scale-reset-btn">🔄 Reset</button>
        </div>

        <!-- Scale Assembly -->
        <div class="tm-scale-rig">
          <div class="tm-scale-beam" style="transform: rotate(${tiltAngle}deg); transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);">
            <!-- Left Pan Assembly -->
            <div class="tm-pan-assembly tm-pan-left" style="transform: rotate(${-tiltAngle}deg); transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);">
              <div class="tm-pan-string"></div>
              <div class="tm-pan-dish">
                <div class="tm-dish-title">Left Pan (${this.leftWeight} ${this.unit})</div>
                <div class="tm-dish-items">
                  ${this.leftItems.map(i => `<span class="tm-pan-item tm-item-left">${this.escapeHtml(i)}</span>`).join('')}
                </div>
              </div>
            </div>

            <!-- Fulcrum Pivot -->
            <div class="tm-pivot-point">▲</div>

            <!-- Right Pan Assembly -->
            <div class="tm-pan-assembly tm-pan-right" style="transform: rotate(${-tiltAngle}deg); transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);">
              <div class="tm-pan-string"></div>
              <div class="tm-pan-dish">
                <div class="tm-dish-title">Right Pan (${this.rightWeight} ${this.unit})</div>
                <div class="tm-dish-items">
                  ${this.rightItems.map(i => `<span class="tm-pan-item tm-item-right">${this.escapeHtml(i)}</span>`).join('')}
                </div>
              </div>
            </div>
          </div>
          <div class="tm-scale-stand"></div>
          <div class="tm-scale-base"></div>
        </div>

        {/* Interactive Weights Pad */}
        <div class="tm-scale-weight-pad">
          <span class="tm-pad-label">Tap to place test weights on Left Pan:</span>
          <div class="tm-weight-buttons">
            <button type="button" class="btn-weight" data-weight="1">+1 ${this.unit}</button>
            <button type="button" class="btn-weight" data-weight="2">+2 ${this.unit}</button>
            <button type="button" class="btn-weight" data-weight="5">+5 ${this.unit}</button>
            <button type="button" class="btn-weight" data-weight="10">+10 ${this.unit}</button>
          </div>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const resetBtn = this.container.querySelector('#tm-scale-reset-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetScale());
    }

    this.container.querySelectorAll('.btn-weight').forEach(btn => {
      btn.addEventListener('click', () => {
        const wt = parseInt(btn.getAttribute('data-weight'), 10);
        this.addWeightToLeft(wt);
      });
    });
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
