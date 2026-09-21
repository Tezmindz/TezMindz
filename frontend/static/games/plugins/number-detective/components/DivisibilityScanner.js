/**
 * DivisibilityScanner Component
 * Ported from reference NumberDetective.tsx
 * Features:
 * - Digit placeholders with missing asterisk slot (*)
 * - Interactive digit keypad (0-9)
 * - Real-time sum computation and divisibility rule validation
 * - Dynamic feedback status banner
 */
export class DivisibilityScanner {
  constructor(options = {}) {
    this.digits = options.digits || ["7", "4", "*", "3", "2"];
    this.targetDivisor = options.targetDivisor || 9;
    this.neededDigit = options.neededDigit !== undefined ? options.neededDigit : 2;
    this.onTestDigit = options.onTestDigit || (() => {});

    this.selectedDigit = null;
    this.scannerStatus = 'idle'; // 'idle' | 'success' | 'fail'
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-scanner-wrapper';
    this.renderInternal();
    parentElement.appendChild(this.container);
  }

  testDigit(d) {
    this.selectedDigit = d;

    // Calculate sum of known digits plus tested digit d
    let sum = 0;
    this.digits.forEach(digit => {
      if (digit === "*") {
        sum += d;
      } else {
        const n = parseInt(digit, 10);
        if (!isNaN(n)) sum += n;
      }
    });

    const isDivisible = sum % this.targetDivisor === 0;
    this.scannerStatus = isDivisible ? 'success' : 'fail';
    this.currentSum = sum;

    this.renderInternal();

    this.onTestDigit({
      digit: d,
      sum: this.currentSum,
      isDivisible: isDivisible,
      targetDivisor: this.targetDivisor
    });
  }

  renderInternal() {
    if (!this.container) return;

    // Calculate sum for prompt
    let knownSum = 0;
    this.digits.forEach(d => {
      if (d !== "*") {
        const n = parseInt(d, 10);
        if (!isNaN(n)) knownSum += n;
      }
    });

    this.container.innerHTML = `
      <div class="tm-scanner-card">
        <div class="tm-scanner-header">
          <div class="tm-scanner-title">🔍 Divisibility Scanner Detective</div>
          <span class="tm-scanner-rule-badge">Divisor Rule: ÷ ${this.targetDivisor}</span>
        </div>

        <div class="tm-scanner-stage">
          <span class="tm-scanner-prompt-sub">
            Test missing digit for divisibility by ${this.targetDivisor}:
          </span>

          {/* Number Display with Slot */}
          <div class="tm-scanner-digits-row">
            ${this.digits.map((digit) => {
              const isMissing = digit === "*";
              const displayVal = isMissing ? (this.selectedDigit !== null ? this.selectedDigit : "*") : digit;
              return `
                <div class="tm-digit-slot ${isMissing ? 'slot-missing' : 'slot-fixed'} ${isMissing && this.selectedDigit !== null ? 'slot-filled' : ''}">
                  ${displayVal}
                </div>
              `;
            }).join('')}
          </div>

          {/* Real-time Scanner Result */}
          ${this.scannerStatus !== 'idle' ? `
            <div class="tm-scanner-feedback ${this.scannerStatus === 'success' ? 'status-success' : 'status-fail'}">
              ${this.scannerStatus === 'success' 
                ? `<span>✓ <strong>Sum = ${knownSum} + ${this.selectedDigit} = ${this.currentSum}</strong> (Divisible by ${this.targetDivisor}! 🎉)</span>` 
                : `<span>✕ <strong>Sum = ${knownSum} + ${this.selectedDigit} = ${this.currentSum}</strong> (Not divisible by ${this.targetDivisor})</span>`}
            </div>
          ` : ''}
        </div>

        {/* Digit Keypad (0-9) */}
        <div class="tm-scanner-keypad-section">
          <span class="tm-keypad-title">Tap a digit to test in scanner:</span>
          <div class="tm-scanner-keypad-grid">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map(num => `
              <button type="button" class="tm-keypad-btn ${this.selectedDigit === num ? 'btn-active' : ''}" data-num="${num}">
                ${num}
              </button>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    this.container.querySelectorAll('.tm-keypad-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const num = parseInt(btn.getAttribute('data-num'), 10);
        this.testDigit(num);
      });
    });
  }
}
