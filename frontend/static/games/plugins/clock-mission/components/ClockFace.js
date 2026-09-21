/**
 * ClockFace Component
 * Interactive SVG analog clock ported from reference ClockMission.tsx
 * Supports angle calculation, quick step adjustments (-1h, -15m, +15m, +1h), and reset.
 */
export class ClockFace {
  constructor(options = {}) {
    this.initialHours = options.hours !== undefined ? options.hours : 8;
    this.initialMinutes = options.minutes !== undefined ? options.minutes : 45;
    this.hours = this.initialHours;
    this.minutes = this.initialMinutes;
    this.isInteractive = options.isInteractive ?? true;
    this.onChange = options.onChange || (() => {});
    this.isManipulating = false;
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-clock-wrapper';

    this.renderInternal();
    parentElement.appendChild(this.container);
  }

  formatTime(h, m) {
    const period = h >= 12 ? 'PM' : 'AM';
    const displayH = h % 12 === 0 ? 12 : h % 12;
    const displayM = m.toString().padStart(2, '0');
    return `${displayH}:${displayM} ${period}`;
  }

  renderInternal() {
    const minuteAngle = this.minutes * 6;
    const hourAngle = (this.hours % 12) * 30 + this.minutes * 0.5;

    this.container.innerHTML = `
      <div class="tm-clock-card">
        <div class="tm-clock-header">
          <div class="tm-clock-title">⏱️ Analog Clock Manipulator</div>
          <button type="button" class="tm-clock-reset-btn" id="tm-clock-reset" title="Reset to problem time">
            🔄 Reset
          </button>
        </div>

        <div class="tm-clock-svg-wrap">
          <svg viewBox="0 0 200 200" class="tm-clock-svg">
            <!-- Bezel & dial -->
            <circle cx="100" cy="100" r="95" fill="#f8fafc" stroke="#0284c7" stroke-width="4" />
            <circle cx="100" cy="100" r="90" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />

            <!-- Hour Ticks & Numbers -->
            <g class="tm-clock-numbers">
              ${Array.from({ length: 12 }, (_, i) => {
                const num = i + 1;
                const angle = (num * 30 * Math.PI) / 180;
                const x = 100 + 72 * Math.sin(angle);
                const y = 100 - 72 * Math.cos(angle);
                const t1x = 100 + 82 * Math.sin(angle);
                const t1y = 100 - 82 * Math.cos(angle);
                const t2x = 100 + 88 * Math.sin(angle);
                const t2y = 100 - 88 * Math.cos(angle);
                return `
                  <g>
                    <line x1="${t1x}" y1="${t1y}" x2="${t2x}" y2="${t2y}" stroke="#64748b" stroke-width="2.5" />
                    <text x="${x}" y="${y + 5}" text-anchor="middle" fill="#0f172a" font-size="14" font-weight="bold" font-family="sans-serif">${num}</text>
                  </g>
                `;
              }).join('')}
            </g>

            <!-- Hour Hand -->
            <line id="tm-hour-hand"
              x1="100" y1="100"
              x2="${100 + 46 * Math.sin((hourAngle * Math.PI) / 180)}"
              y2="${100 - 46 * Math.cos((hourAngle * Math.PI) / 180)}"
              stroke="#d97706" stroke-width="5" stroke-linecap="round" />

            <!-- Minute Hand -->
            <line id="tm-min-hand"
              x1="100" y1="100"
              x2="${100 + 68 * Math.sin((minuteAngle * Math.PI) / 180)}"
              y2="${100 - 68 * Math.cos((minuteAngle * Math.PI) / 180)}"
              stroke="#0284c7" stroke-width="3.5" stroke-linecap="round" />

            <!-- Center Cap -->
            <circle cx="100" cy="100" r="5" fill="#f8fafc" stroke="#0284c7" stroke-width="2" />
          </svg>
        </div>

        <!-- Digital Readout & Angle Calculations -->
        <div class="tm-digital-readout-box">
          <div class="tm-digital-badge" id="tm-digital-badge">
            ${this.formatTime(this.hours, this.minutes)}
          </div>
          <p class="tm-angle-calc-text" id="tm-angle-calc-text">
            Hour angle: ${Math.round(hourAngle)}° | Minute angle: ${Math.round(minuteAngle)}°
          </p>
        </div>

        <!-- Quick Interactive Step Controls -->
        ${this.isInteractive ? `
          <div class="tm-clock-controls-grid">
            <button type="button" class="tm-time-step-btn" data-step="-60">-1 Hr</button>
            <button type="button" class="tm-time-step-btn" data-step="-15">-15 Min</button>
            <button type="button" class="tm-time-step-btn" data-step="15">+15 Min</button>
            <button type="button" class="tm-time-step-btn" data-step="60">+1 Hr</button>
          </div>
        ` : ''}

        <div id="tm-manip-status" class="tm-manip-status" style="${this.isManipulating ? 'display: block;' : 'display: none;'}">
          ✓ Hands adjusted! Observe how time and angles changed.
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    if (!this.container) return;

    // Reset button
    const resetBtn = this.container.querySelector('#tm-clock-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.hours = this.initialHours;
        this.minutes = this.initialMinutes;
        this.isManipulating = false;
        this.updateClock();
      });
    }

    // Step buttons
    this.container.querySelectorAll('.tm-time-step-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const step = parseInt(btn.getAttribute('data-step'), 10);
        this.addMinutes(step);
      });
    });
  }

  addMinutes(delta) {
    this.isManipulating = true;
    let totalMins = this.hours * 60 + this.minutes + delta;
    if (totalMins < 0) totalMins += 24 * 60;
    this.hours = Math.floor((totalMins / 60) % 24);
    this.minutes = totalMins % 60;

    this.updateClock();
  }

  updateClock() {
    const minuteAngle = this.minutes * 6;
    const hourAngle = (this.hours % 12) * 30 + this.minutes * 0.5;

    const hourHand = this.container.querySelector('#tm-hour-hand');
    const minHand = this.container.querySelector('#tm-min-hand');
    const badge = this.container.querySelector('#tm-digital-badge');
    const angleText = this.container.querySelector('#tm-angle-calc-text');
    const status = this.container.querySelector('#tm-manip-status');

    if (hourHand) {
      hourHand.setAttribute('x2', String(100 + 46 * Math.sin((hourAngle * Math.PI) / 180)));
      hourHand.setAttribute('y2', String(100 - 46 * Math.cos((hourAngle * Math.PI) / 180)));
    }
    if (minHand) {
      minHand.setAttribute('x2', String(100 + 68 * Math.sin((minuteAngle * Math.PI) / 180)));
      minHand.setAttribute('y2', String(100 - 68 * Math.cos((minuteAngle * Math.PI) / 180)));
    }
    if (badge) {
      badge.textContent = this.formatTime(this.hours, this.minutes);
    }
    if (angleText) {
      angleText.textContent = `Hour angle: ${Math.round(hourAngle)}° | Minute angle: ${Math.round(minuteAngle)}°`;
    }
    if (status) {
      status.style.display = this.isManipulating ? 'block' : 'none';
    }

    this.onChange({
      hours: this.hours,
      minutes: this.minutes,
      hourAngle,
      minuteAngle,
      formatted: this.formatTime(this.hours, this.minutes)
    });
  }
}
