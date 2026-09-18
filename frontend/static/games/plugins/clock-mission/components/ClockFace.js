/**
 * ClockFace Component
 * Renders an interactive SVG analog clock with draggable or stepped hour and minute hands.
 */
export class ClockFace {
  constructor(options = {}) {
    this.hours = options.hours || 12;
    this.minutes = options.minutes || 0;
    this.isInteractive = options.isInteractive ?? true;
    this.onChange = options.onChange || (() => {});
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-clock-wrapper';

    const hourDeg = (this.hours % 12) * 30 + this.minutes * 0.5;
    const minDeg = this.minutes * 6;

    this.container.innerHTML = `
      <div class="tm-clock-dial-container">
        <svg class="tm-clock-svg" viewBox="0 0 200 200" width="100%" height="100%">
          <!-- Outer bezel -->
          <circle cx="100" cy="100" r="94" class="tm-clock-bezel" />
          <circle cx="100" cy="100" r="88" class="tm-clock-face" />

          <!-- Hour Ticks & Numbers -->
          <g class="tm-clock-numbers">
            ${Array.from({ length: 12 }, (_, i) => {
              const num = i + 1;
              const angle = (num * 30 * Math.PI) / 180;
              const x = 100 + 70 * Math.sin(angle);
              const y = 100 - 70 * Math.cos(angle) + 4;
              return `<text x="${x}" y="${y}" text-anchor="middle" class="tm-clock-num">${num}</text>`;
            }).join('')}
          </g>

          <!-- Minute Marks -->
          <g class="tm-clock-ticks">
            ${Array.from({ length: 60 }, (_, i) => {
              if (i % 5 === 0) return '';
              const angle = (i * 6 * Math.PI) / 180;
              const x1 = 100 + 82 * Math.sin(angle);
              const y1 = 100 - 82 * Math.cos(angle);
              const x2 = 100 + 86 * Math.sin(angle);
              const y2 = 100 - 86 * Math.cos(angle);
              return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="tm-clock-tick-line" />`;
            }).join('')}
          </g>

          <!-- Hour Hand -->
          <line id="tm-hour-hand" x1="100" y1="100" x2="100" y2="52" 
            transform="rotate(${hourDeg} 100 100)" 
            class="tm-clock-hand-hour" />

          <!-- Minute Hand -->
          <line id="tm-min-hand" x1="100" y1="100" x2="100" y2="30" 
            transform="rotate(${minDeg} 100 100)" 
            class="tm-clock-hand-min" />

          <!-- Center Cap -->
          <circle cx="100" cy="100" r="5" class="tm-clock-pin-outer" />
          <circle cx="100" cy="100" r="2.5" class="tm-clock-pin-inner" />
        </svg>

        <!-- Digital Readout Display -->
        <div class="tm-digital-readout">
          <span id="tm-digital-text">
            ${String(this.hours).padStart(2, '0')}:${String(this.minutes).padStart(2, '0')}
          </span>
        </div>
      </div>
    `;

    parentElement.appendChild(this.container);

    if (this.isInteractive) {
      this.attachControls(parentElement);
    }
  }

  attachControls(parentElement) {
    const controls = document.createElement('div');
    controls.className = 'tm-clock-quick-controls';
    controls.innerHTML = `
      <div class="tm-btn-group">
        <button type="button" class="tm-control-btn" data-action="minus-15">-15m</button>
        <button type="button" class="tm-control-btn" data-action="minus-5">-5m</button>
        <button type="button" class="tm-control-btn" data-action="plus-5">+5m</button>
        <button type="button" class="tm-control-btn" data-action="plus-15">+15m</button>
        <button type="button" class="tm-control-btn" data-action="plus-60">+1h</button>
      </div>
    `;

    controls.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-action]');
      if (!btn) return;
      const action = btn.dataset.action;

      if (action === 'plus-5') this.addMinutes(5);
      if (action === 'minus-5') this.addMinutes(-5);
      if (action === 'plus-15') this.addMinutes(15);
      if (action === 'minus-15') this.addMinutes(-15);
      if (action === 'plus-60') this.addMinutes(60);
    });

    parentElement.appendChild(controls);
  }

  addMinutes(delta) {
    let total = this.hours * 60 + this.minutes + delta;
    if (total < 0) total += 24 * 60;
    total = total % (24 * 60);

    let h = Math.floor(total / 60) % 12;
    if (h === 0) h = 12;
    this.hours = h;
    this.minutes = total % 60;

    this.updateHands();
    this.onChange({ hours: this.hours, minutes: this.minutes });
  }

  setTime(hours, minutes) {
    this.hours = hours;
    this.minutes = minutes;
    this.updateHands();
  }

  updateHands() {
    const hourHand = this.container.querySelector('#tm-hour-hand');
    const minHand = this.container.querySelector('#tm-min-hand');
    const readout = this.container.querySelector('#tm-digital-text');

    const hourDeg = (this.hours % 12) * 30 + this.minutes * 0.5;
    const minDeg = this.minutes * 6;

    if (hourHand) hourHand.setAttribute('transform', `rotate(${hourDeg} 100 100)`);
    if (minHand) minHand.setAttribute('transform', `rotate(${minDeg} 100 100)`);
    if (readout) {
      readout.textContent = `${String(this.hours).padStart(2, '0')}:${String(this.minutes).padStart(2, '0')}`;
    }
  }
}
