/**
 * BarGraph Component
 * Renders an animated SVG bar chart with labels and values
 */
export class BarGraph {
  constructor(chartData = [], unitLabel = 'Value') {
    this.chartData = chartData;
    this.unitLabel = unitLabel;
  }

  render(parentElement) {
    const wrap = document.createElement('div');
    wrap.className = 'tm-chart-stage';

    const maxVal = Math.max(...this.chartData.map(d => d.value || 0), 40);
    const barsHtml = this.chartData.map((bar, idx) => {
      const heightPercent = Math.min(100, Math.round((bar.value / maxVal) * 100));
      return `
        <div class="tm-bar-col">
          <span class="tm-bar-val">${bar.value}</span>
          <div class="tm-bar-track">
            <div class="tm-bar-fill" style="height: ${heightPercent}%; background-color: ${bar.color || '#3b82f6'};"></div>
          </div>
          <span class="tm-bar-label">${this.escapeHtml(bar.label)}</span>
        </div>
      `;
    }).join('');

    wrap.innerHTML = `
      <div class="tm-chart-header">
        <span class="tm-chart-unit">📊 ${this.escapeHtml(this.unitLabel)}</span>
      </div>
      <div class="tm-chart-bars">
        ${barsHtml}
      </div>
    `;

    parentElement.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
