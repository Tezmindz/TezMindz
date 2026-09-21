/**
 * BarGraph Component
 * Ported from reference GraphExplorer.tsx
 * Interactive Bar Chart with clickable bars, floating pills, selected info banner, and total sum.
 */
export class BarGraph {
  constructor(chartData = [], unitLabel = 'Books Read', options = {}) {
    this.chartData = chartData.length > 0 ? chartData : [
      { label: "Aarav", value: 15, color: "#38bdf8" },
      { label: "Diya", value: 25, color: "#a855f7" },
      { label: "Kabir", value: 20, color: "#34d399" },
      { label: "Tanvi", value: 30, color: "#f59e0b" }
    ];
    this.unitLabel = unitLabel || 'Books Read';
    this.selectedBar = null;
    this.onSelect = options.onSelect || (() => {});
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-chart-stage-wrapper';
    this.renderInternal();
    parentElement.appendChild(this.container);
  }

  handleBarClick(bar) {
    this.selectedBar = bar;
    this.renderInternal();
    this.onSelect(bar);
  }

  renderInternal() {
    if (!this.container) return;

    const maxValue = Math.max(...this.chartData.map(d => d.value || 0), 35);
    const totalSum = this.chartData.reduce((acc, d) => acc + (d.value || 0), 0);

    this.container.innerHTML = `
      <div class="tm-graph-card">
        <div class="tm-graph-header">
          <div class="tm-graph-title">📊 Interactive Bar Graph Explorer</div>
          <span class="tm-graph-yaxis-badge">Y-Axis: ${this.escapeHtml(this.unitLabel)}</span>
        </div>

        {/* Canvas / Chart Bars */}
        <div class="tm-graph-canvas">
          <div class="tm-graph-bars-row">
            ${this.chartData.map((item, idx) => {
              const heightPercent = Math.min(100, Math.round((item.value / maxValue) * 100));
              const isSelected = this.selectedBar && this.selectedBar.label === item.label;

              return `
                <div class="tm-bar-column ${isSelected ? 'bar-selected' : ''}" data-idx="${idx}">
                  <!-- Floating Value Pill -->
                  <div class="tm-bar-value-pill ${isSelected ? 'pill-active' : ''}">
                    ${item.value}
                  </div>

                  <!-- Bar -->
                  <div class="tm-bar-track-wrap">
                    <div
                      class="tm-bar-fill-elem"
                      style="height: ${heightPercent}%; background-color: ${item.color || '#38bdf8'}; ${isSelected ? `box-shadow: 0 0 15px ${item.color || '#38bdf8'}; border: 2px solid #ffffff;` : ''}"
                    ></div>
                  </div>

                  <!-- X-Axis Label -->
                  <span class="tm-bar-xaxis-label">${this.escapeHtml(item.label)}</span>
                </div>
              `;
            }).join('')}
          </div>

          {/* Selected Bar Insight */}
          ${this.selectedBar ? `
            <div class="tm-selected-insight-card">
              <span>ℹ️ Selected: <strong>${this.escapeHtml(this.selectedBar.label)}</strong></span>
              <strong class="tm-insight-value">${this.selectedBar.value} ${this.escapeHtml(this.unitLabel.toLowerCase())}</strong>
            </div>
          ` : ''}
        </div>

        <div class="tm-graph-footer-summary">
          <span>💡 Tap any bar to inspect specific data</span>
          <span class="tm-graph-total-badge">Total: ${totalSum}</span>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    this.container.querySelectorAll('.tm-bar-column').forEach(col => {
      col.addEventListener('click', () => {
        const idx = parseInt(col.getAttribute('data-idx'), 10);
        this.handleBarClick(this.chartData[idx]);
      });
    });
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
