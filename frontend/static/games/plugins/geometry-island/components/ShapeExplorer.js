/**
 * ShapeExplorer Component
 * Ported from reference MirrorLab.tsx and ShapeLab.tsx
 * Supports:
 * - Interactive 2D shapes with perimeter & area calculation
 * - Full Mirror Lab simulator with vertical axis (MN) & horizontal axis (AB) reflection toggles
 * - Live SVG reflection flipping
 */
export class ShapeExplorer {
  constructor(shapeData = {}) {
    this.shapeData = Object.assign({
      type: 'RECTANGLE',
      width: 12,
      height: 8,
      unit: 'cm',
      sides: [],
      axis: 'vertical'
    }, shapeData);

    this.axis = this.shapeData.axis || 'vertical';
    this.showReflection = true;
    this.container = null;
  }

  render(container) {
    this.container = document.createElement('div');
    this.container.className = 'tm-shape-explorer';
    this.renderInternal();
    container.appendChild(this.container);
  }

  toggleAxis(axis) {
    this.axis = axis;
    this.renderInternal();
  }

  renderInternal() {
    if (!this.container) return;

    const isMirror = this.shapeData.type === 'MIRROR' || this.shapeData.hasMirror;

    if (isMirror) {
      this.container.innerHTML = `
        <div class="tm-mirror-card" style="background:#0f172a; border:1.5px solid #a855f7; border-radius:16px; padding:16px; color:#ffffff; margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:8px; margin-bottom:12px;">
            <div style="color:#d8b4fe; font-weight:800; font-size:0.9rem;">✨ Mirror Lab Simulator</div>
            <div style="display:flex; gap:6px;">
              <button type="button" class="btn-axis ${this.axis === 'vertical' ? 'axis-active' : ''}" id="btn-axis-vert" style="background:${this.axis === 'vertical' ? '#9333ea' : '#1e293b'}; color:#fff; border:1px solid #7e22ce; padding:3px 8px; border-radius:6px; font-size:0.75rem; cursor:pointer;">
                Vertical Line (MN)
              </button>
              <button type="button" class="btn-axis ${this.axis === 'horizontal' ? 'axis-active' : ''}" id="btn-axis-horiz" style="background:${this.axis === 'horizontal' ? '#9333ea' : '#1e293b'}; color:#fff; border:1px solid #7e22ce; padding:3px 8px; border-radius:6px; font-size:0.75rem; cursor:pointer;">
                Horizontal Line (AB)
              </button>
            </div>
          </div>

          <!-- Mirror Stage -->
          <div style="display:flex; align-items:center; justify-content:center; gap:16px; background:#020617; border-radius:12px; padding:16px; ${this.axis === 'horizontal' ? 'flex-direction:column;' : 'flex-direction:row;'}">
            <!-- Original -->
            <div style="display:flex; flex-direction:column; align-items:center;">
              <span style="font-size:0.7rem; color:#94a3b8; font-family:monospace; margin-bottom:6px;">ORIGINAL FIGURE</span>
              <div style="width:100px; height:100px; background:#1e293b; border:2px dashed #6366f1; border-radius:12px; padding:8px; display:flex; align-items:center; justify-content:center;">
                <svg viewBox="0 0 100 100" style="width:100%; height:100%;">
                  <polygon points="20,20 60,20 80,45 60,70 20,70 35,45" fill="#6366f1" stroke="#a5b4fc" stroke-width="2" />
                  <circle cx="45" cy="45" r="8" fill="#facc15" />
                  <line x1="20" y1="70" x2="20" y2="90" stroke="#94a3b8" stroke-width="4" stroke-linecap="round" />
                </svg>
              </div>
            </div>

            <!-- Mirror line -->
            <div style="position:relative; display:flex; align-items:center; justify-content:center; ${this.axis === 'vertical' ? 'width:16px; height:100px; flex-direction:column;' : 'width:140px; height:16px; flex-direction:row;'}">
              <div style="${this.axis === 'vertical' ? 'width:2px; height:100%; border-right:2px dashed #22d3ee;' : 'height:2px; width:100%; border-bottom:2px dashed #22d3ee;'}"></div>
              <span style="position:absolute; background:#083344; padding:2px 6px; border-radius:4px; border:1px solid #06b6d4; font-size:0.65rem; color:#67e8f9; font-family:monospace;">
                ${this.axis === 'vertical' ? 'M-N' : 'A-B'}
              </span>
            </div>

            <!-- Reflected -->
            <div style="display:flex; flex-direction:column; align-items:center;">
              <span style="font-size:0.7rem; color:#d8b4fe; font-family:monospace; margin-bottom:6px;">MIRROR IMAGE</span>
              <div style="width:100px; height:100px; background:#1e293b; border:2px solid #a855f7; border-radius:12px; padding:8px; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                <svg viewBox="0 0 100 100" style="width:100%; height:100%; transform:${this.axis === 'vertical' ? 'scaleX(-1)' : 'scaleY(-1)'}; transition:transform 0.3s;">
                  <polygon points="20,20 60,20 80,45 60,70 20,70 35,45" fill="#a855f7" stroke="#e9d5ff" stroke-width="2" />
                  <circle cx="45" cy="45" r="8" fill="#facc15" />
                  <line x1="20" y1="70" x2="20" y2="90" stroke="#94a3b8" stroke-width="4" stroke-linecap="round" />
                </svg>
              </div>
            </div>
          </div>

          <div style="margin-top:12px; background:rgba(147, 51, 234, 0.15); border:1px solid #7e22ce; border-radius:8px; padding:8px 12px; font-size:0.75rem; color:#e9d5ff;">
            <strong>💡 Olympiad Secret Rule:</strong>
            ${this.axis === 'vertical'
              ? ' In a <strong>Vertical Mirror (line MN)</strong>: Left becomes Right, and Right becomes Left. Top and Bottom stay unchanged!'
              : ' In a <strong>Horizontal Mirror (line AB)</strong>: Top becomes Bottom, and Bottom becomes Top (water image). Left and Right stay unchanged!'}
          </div>
        </div>
      `;

      const vertBtn = this.container.querySelector('#btn-axis-vert');
      const horizBtn = this.container.querySelector('#btn-axis-horiz');
      if (vertBtn) vertBtn.addEventListener('click', () => this.toggleAxis('vertical'));
      if (horizBtn) horizBtn.addEventListener('click', () => this.toggleAxis('horizontal'));
      return;
    }

    // Default 2D shape view
    const type = (this.shapeData.type || 'RECTANGLE').toUpperCase();
    const w = this.shapeData.width || 14;
    const h = this.shapeData.height || 8;
    const unit = this.shapeData.unit || 'cm';
    const perimeter = 2 * (w + h);
    const area = w * h;

    this.container.innerHTML = `
      <div style="background:#ffffff; border:2px solid #10b981; border-radius:16px; padding:16px; margin-bottom:14px;">
        <div style="text-align:center;">
          <svg viewBox="0 0 240 160" style="width:100%; max-width:280px; height:150px;">
            <rect x="40" y="30" width="160" height="90" rx="4" fill="#ecfdf5" stroke="#10b981" stroke-width="3" stroke-dasharray="6,3" />
            <rect x="42" y="32" width="10" height="10" fill="none" stroke="#059669" stroke-width="1.5" />
            <text x="120" y="22" text-anchor="middle" font-size="12" font-weight="bold" fill="#047857" font-family="monospace">${w} ${unit}</text>
            <text x="120" y="136" text-anchor="middle" font-size="12" font-weight="bold" fill="#047857" font-family="monospace">${w} ${unit}</text>
            <text x="30" y="80" text-anchor="end" font-size="12" font-weight="bold" fill="#047857" font-family="monospace">${h} ${unit}</text>
            <text x="210" y="80" text-anchor="start" font-size="12" font-weight="bold" fill="#047857" font-family="monospace">${h} ${unit}</text>
          </svg>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:10px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:8px 12px; font-size:0.8rem;">
          <span>📏 Perimeter: <strong style="color:#047857; font-family:monospace;">${perimeter} ${unit}</strong></span>
          <span>⊞ Area: <strong style="color:#059669; font-family:monospace;">${area} sq. ${unit}</strong></span>
        </div>
      </div>
    `;
  }
}
