/**
 * TimelineTracker Component
 * Renders time intervals, start/end clock milestones, and duration calculations.
 */
export class TimelineTracker {
  constructor(timeData = {}) {
    this.timeData = timeData;
  }

  render(container) {
    if (!this.timeData || (!this.timeData.startTime && !this.timeData.endTime)) return;

    const wrap = document.createElement('div');
    wrap.className = 'tm-timeline-box';
    wrap.innerHTML = `
      <div class="tm-timeline-header">⏱️ Time Elapsed Monitor</div>
      <div class="tm-timeline-bar">
        <div class="tm-timeline-node">
          <span class="tm-node-label">Start</span>
          <strong class="tm-node-val">${this.escapeHtml(this.timeData.startTime || '--:--')}</strong>
        </div>
        <div class="tm-timeline-line">➔</div>
        <div class="tm-timeline-node">
          <span class="tm-node-label">End</span>
          <strong class="tm-node-val">${this.escapeHtml(this.timeData.endTime || '--:--')}</strong>
        </div>
      </div>
      ${this.timeData.durationMinutes ? `
        <div class="tm-timeline-duration">
          Duration: <strong>${this.timeData.durationMinutes} minutes</strong>
        </div>
      ` : ''}
    `;
    container.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
