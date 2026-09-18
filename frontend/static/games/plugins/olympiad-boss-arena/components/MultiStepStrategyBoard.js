/**
 * MultiStepStrategyBoard Component
 * Renders sub-steps, intermediate milestones, and strategy checkpoints for complex Olympiad questions.
 */
export class MultiStepStrategyBoard {
  constructor(steps = []) {
    this.steps = steps;
  }

  render(container) {
    if (!this.steps || this.steps.length === 0) return;

    const wrap = document.createElement('div');
    wrap.className = 'tm-strategy-board';

    wrap.innerHTML = `
      <div class="tm-strategy-title">⚔️ Tactical Strategy Decomposition</div>
      <div class="tm-strategy-list">
        ${this.steps.map((step, idx) => `
          <div class="tm-strategy-item">
            <span class="tm-strategy-step-num">Step ${idx + 1}</span>
            <span class="tm-strategy-step-text">${this.escapeHtml(step)}</span>
          </div>
        `).join('')}
      </div>
    `;

    container.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
