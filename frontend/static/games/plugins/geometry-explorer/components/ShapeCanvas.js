/**
 * ShapeCanvas Component
 * Ported from reference ShapeLab.tsx
 * Features:
 * - Interactive Shape Lab visualizer
 * - Grid overlay toggle button
 * - Animated perimeter walkway toggle
 * - Corner right-angle marks
 * - Real-time perimeter & area calculation cards
 */
export class ShapeCanvas {
  constructor(shapeData = {}) {
    this.length = shapeData.length || shapeData.dimensions?.width || 65;
    this.breadth = shapeData.breadth || shapeData.dimensions?.height || 35;
    this.unit = shapeData.unit || 'm';
    this.showGrid = false;
    this.showPerimeterWalk = true;
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-shape-lab-wrapper';
    this.renderInternal();
    parentElement.appendChild(this.container);
  }

  toggleGrid() {
    this.showGrid = !this.showGrid;
    this.renderInternal();
  }

  togglePerimeterWalk() {
    this.showPerimeterWalk = !this.showPerimeterWalk;
    this.renderInternal();
  }

  renderInternal() {
    if (!this.container) return;

    const perimeter = 2 * (this.length + this.breadth);
    const area = this.length * this.breadth;

    this.container.innerHTML = `
      <div class="tm-shapelab-card">
        <div class="tm-shapelab-header">
          <div class="tm-shapelab-title">📐 Interactive Geometry &amp; Shape Lab</div>
          <div class="tm-shapelab-toggles">
            <button type="button" class="btn-toggle ${this.showGrid ? 'toggle-on' : ''}" id="btn-toggle-grid">
              ${this.showGrid ? '✓ Grid ON' : '⊞ Grid Overlay'}
            </button>
            <button type="button" class="btn-toggle ${this.showPerimeterWalk ? 'toggle-on' : ''}" id="btn-toggle-walk">
              ${this.showPerimeterWalk ? '🚶 Walk ON' : '🚶 Walkway'}
            </button>
          </div>
        </div>

        {/* Visual Stage */}
        <div class="tm-shapelab-stage ${this.showGrid ? 'stage-grid-active' : ''}">
          <svg viewBox="0 0 280 160" class="tm-shape-svg">
            <defs>
              <linearGradient id="shapeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#059669" />
                <stop offset="100%" stop-color="#047857" />
              </linearGradient>
            </defs>

            <!-- Rectangle Body -->
            <rect
              x="40"
              y="30"
              width="200"
              height="100"
              rx="4"
              fill="url(#shapeGradient)"
              stroke="#34d399"
              stroke-width="3"
              stroke-dasharray="${this.showPerimeterWalk ? '8,4' : 'none'}"
              class="${this.showPerimeterWalk ? 'tm-perimeter-walk-anim' : ''}"
            />

            <!-- Corner Right-Angle Marks -->
            <rect x="42" y="32" width="10" height="10" fill="none" stroke="#a7f3d0" stroke-width="1.5" />
            <rect x="228" y="32" width="10" height="10" fill="none" stroke="#a7f3d0" stroke-width="1.5" />
            <rect x="42" y="118" width="10" height="10" fill="none" stroke="#a7f3d0" stroke-width="1.5" />
            <rect x="228" y="118" width="10" height="10" fill="none" stroke="#a7f3d0" stroke-width="1.5" />

            <!-- Dimension Labels -->
            <!-- Top Length -->
            <text x="140" y="22" text-anchor="middle" fill="#34d399" font-size="12" font-weight="bold" font-family="monospace">
              Length = ${this.length} ${this.unit}
            </text>
            <!-- Bottom Length -->
            <text x="140" y="146" text-anchor="middle" fill="#6ee7b7" font-size="11" font-family="monospace">
              ${this.length} ${this.unit}
            </text>
            <!-- Left Breadth -->
            <text x="25" y="85" text-anchor="middle" fill="#34d399" font-size="11" font-weight="bold" font-family="monospace" transform="rotate(-90 25 85)">
              Breadth = ${this.breadth} ${this.unit}
            </text>
            <!-- Right Breadth -->
            <text x="255" y="85" text-anchor="middle" fill="#6ee7b7" font-size="11" font-family="monospace" transform="rotate(90 255 85)">
              ${this.breadth} ${this.unit}
            </text>
          </svg>

          <div class="tm-walkway-formula">
            Walkway Perimeter = 2 × (${this.length} + ${this.breadth}) = <strong>${perimeter} ${this.unit}</strong>
          </div>
        </div>

        {/* Measurement Metric Cards */}
        <div class="tm-metrics-grid">
          <div class="tm-metric-pill metric-perimeter">
            <span class="tm-metric-label">📏 Perimeter:</span>
            <strong class="tm-metric-val">${perimeter} ${this.unit}</strong>
          </div>
          <div class="tm-metric-pill metric-area">
            <span class="tm-metric-label">⊞ Area:</span>
            <strong class="tm-metric-val">${area} sq. ${this.unit}</strong>
          </div>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const gridBtn = this.container.querySelector('#btn-toggle-grid');
    if (gridBtn) {
      gridBtn.addEventListener('click', () => this.toggleGrid());
    }

    const walkBtn = this.container.querySelector('#btn-toggle-walk');
    if (walkBtn) {
      walkBtn.addEventListener('click', () => this.togglePerimeterWalk());
    }
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
