/**
 * PatternRenderer Component
 * Ported from reference PatternMachine.tsx
 * Features:
 * - Interactive Gear Analyzer button
 * - Animated spinning gear
 * - Step delta difference pills between sequence elements (e.g. +5, +10, etc.)
 * - Pulse effect on missing term slot
 * - Rule discovery insight card
 */
export class PatternRenderer {
  constructor(sequence = [], missingIndex = -1, options = {}) {
    this.sequence = sequence.length > 0 ? sequence : [4, 9, 19, 39, 79, "?"];
    this.missingIndex = missingIndex !== -1 ? missingIndex : this.sequence.indexOf('?');
    if (this.missingIndex === -1 && this.sequence.includes('?')) {
      this.missingIndex = this.sequence.indexOf('?');
    }
    this.deltas = options.deltas || this.calculateDeltas(this.sequence);
    this.missingVal = options.missingVal || 159;
    this.ruleText = options.ruleText || "The difference doubles at each step (+5, +10, +20, +40, +80).";
    this.onAnalyze = options.onAnalyze || (() => {});

    this.revealed = false;
    this.spinning = false;
    this.container = null;
  }

  calculateDeltas(seq) {
    const deltas = [];
    for (let i = 0; i < seq.length - 1; i++) {
      const a = Number(seq[i]);
      const b = Number(seq[i + 1]);
      if (!isNaN(a) && !isNaN(b)) {
        const diff = b - a;
        deltas.push((diff >= 0 ? `+${diff}` : `${diff}`));
      } else {
        deltas.push("×2 + 1");
      }
    }
    return deltas;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-pattern-engine-wrapper';
    this.renderInternal();
    parentElement.appendChild(this.container);
  }

  testGear() {
    this.spinning = true;
    this.renderInternal();

    setTimeout(() => {
      this.spinning = false;
      this.revealed = true;
      this.renderInternal();
      this.onAnalyze({
        revealed: true,
        missingVal: this.missingVal
      });
    }, 500);
  }

  fillMissingSlot(value, isCorrect) {
    this.revealed = true;
    this.missingVal = value;
    this.renderInternal();
  }

  renderInternal() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="tm-pattern-card">
        <div class="tm-pattern-header">
          <div class="tm-pattern-title">
            <span class="tm-gear-icon ${this.spinning ? 'gear-spinning' : ''}">⚙️</span>
            <span>Pattern Engine &amp; Series Machine</span>
          </div>
          <button type="button" class="btn-analyze-gear" id="tm-btn-gear">
            ▶ Analyze Gear
          </button>
        </div>

        {/* Visual Sequence Track */}
        <div class="tm-sequence-track">
          <div class="tm-sequence-row">
            ${this.sequence.map((item, idx) => {
              const isMissing = idx === this.missingIndex || item === "?";
              const val = isMissing && this.revealed ? this.missingVal : item;
              const delta = this.deltas[idx];

              return `
                <div class="tm-seq-node-col">
                  <div class="tm-seq-box ${isMissing ? 'box-missing' : 'box-fixed'} ${isMissing && this.revealed ? 'box-revealed' : ''}">
                    ${val}
                  </div>
                  <span class="tm-seq-pos">T${idx + 1}</span>
                </div>

                ${idx < this.sequence.length - 1 ? `
                  <div class="tm-delta-connector">
                    <span class="tm-delta-badge">${delta || '→'}</span>
                    <span class="tm-delta-arrow">→</span>
                  </div>
                ` : ''}
              `;
            }).join('')}
          </div>
        </div>

        {/* Rule Identified Banner */}
        ${this.revealed ? `
          <div class="tm-rule-banner">
            <span class="tm-sparkle-icon">✨</span>
            <span>
              <strong>Rule Identified:</strong> ${this.ruleText}
            </span>
          </div>
        ` : `
          <div class="tm-hint-sub">
            💡 Click <strong>"Analyze Gear"</strong> to observe step deltas and uncover the mathematical rule!
          </div>
        `}
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const gearBtn = this.container.querySelector('#tm-btn-gear');
    if (gearBtn) {
      gearBtn.addEventListener('click', () => this.testGear());
    }
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
