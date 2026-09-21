/**
 * Fraction Lab Game Template
 * 100% Data-Driven Interactive Visual Fraction Game
 */
import { FractionCircle } from './components/FractionCircle.js';

export class FractionLabGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;
    if (!this.container) throw new Error('[FractionLabGame] Container not found.');
    this.data = data || {};
    this.config = Object.assign({ onAnswer: null, onComplete: null, onProgress: null }, config);
    this.hasAnswered = false;
    this.fractionCircle = null;
    this.currentNumerator = this.data.numerator !== undefined ? this.data.numerator : 1;
    this.currentDenominator = this.data.denominator || 4;
    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';
    const root = document.createElement('div');
    root.className = 'tm-game-fraction';

    // Header
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">🍕 Fractions &amp; Ratios Lab</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Explore and match the fraction')}</h2>
      <p class="tm-subtext" style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">
        💡 <em>Tap or click slices</em> on the circle to shade them and observe the fraction change!
      </p>
    `;
    root.appendChild(header);

    // Visual interactive circle
    const visualContainer = document.createElement('div');
    visualContainer.className = 'tm-visual-stage';

    this.fractionCircle = new FractionCircle(
      this.currentNumerator,
      this.currentDenominator,
      this.config.sliceColor || '#ec4899',
      {
        interactive: true,
        onChange: (state) => {
          this.currentNumerator = state.selectedCount;
          const liveReadout = root.querySelector('#tm-fraction-live-value');
          if (liveReadout) {
            liveReadout.textContent = `${state.selectedCount} / ${state.totalCount}`;
          }
          // If options exist, highlight matching option if any
          root.querySelectorAll('.tm-option-btn').forEach(btn => {
            const btnFraction = btn.getAttribute('data-fraction');
            if (btnFraction === `${state.selectedCount}/${state.totalCount}`) {
              btn.classList.add('tm-opt-highlighted');
            } else {
              btn.classList.remove('tm-opt-highlighted');
            }
          });
        }
      }
    );
    this.fractionCircle.render(visualContainer);
    root.appendChild(visualContainer);

    // Live Readout Bar
    const liveBar = document.createElement('div');
    liveBar.className = 'tm-live-fraction-bar';
    liveBar.innerHTML = `
      <span style="font-size: 0.85rem; color: #64748b; font-weight: 700;">Active Shaded Fraction:</span>
      <strong id="tm-fraction-live-value" style="font-size: 1.2rem; color: #ec4899; font-family: monospace; margin-left: 8px;">
        ${this.currentNumerator} / ${this.currentDenominator}
      </strong>
    `;
    root.appendChild(liveBar);

    // Options Grid (if multiple choice options provided)
    if (this.data.options && this.data.options.length > 0) {
      const optionsTitle = document.createElement('div');
      optionsTitle.style.cssText = "font-size: 0.85rem; font-weight: 700; color: #475569; margin-top: 14px; text-transform: uppercase;";
      optionsTitle.textContent = "Select Matching Solution:";
      root.appendChild(optionsTitle);

      const optionsGrid = document.createElement('div');
      optionsGrid.className = 'tm-options-grid';
      this.data.options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'tm-option-btn';
        btn.setAttribute('data-fraction', String(opt).trim());
        btn.textContent = opt;
        btn.addEventListener('click', () => this.handleSelect(opt, btn));
        optionsGrid.appendChild(btn);
      });
      root.appendChild(optionsGrid);
    }

    // Feedback
    const feedback = document.createElement('div');
    feedback.id = 'tm-fraction-feedback';
    feedback.style.display = 'none';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleSelect(selected, btnEl) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;

    const isCorrect = String(selected).trim() === String(this.data.correctAnswer).trim();

    if (btnEl) {
      btnEl.classList.add(isCorrect ? 'tm-btn-correct' : 'tm-btn-wrong');
    }

    const fb = this.container.querySelector('#tm-fraction-feedback');
    if (fb) {
      fb.style.display = 'block';
      fb.className = `tm-feedback ${isCorrect ? 'tm-feedback-correct' : 'tm-feedback-wrong'}`;
      fb.innerHTML = `
        <div style="font-weight: 800; margin-bottom: 4px;">${isCorrect ? '✓ Exact Fraction Identified!' : '✕ Incorrect Fraction'}</div>
        <div>${this.data.explanation || `The correct fraction is ${this.data.correctAnswer}.`}</div>
      `;
    }

    if (this.config.onAnswer) {
      this.config.onAnswer({
        questionId: this.data.questionId,
        selectedAnswer: selected,
        correctAnswer: this.data.correctAnswer,
        isCorrect
      });
    }

    if (this.config.onComplete) {
      this.config.onComplete({
        score: isCorrect ? 100 : 0,
        accuracy: isCorrect ? 1.0 : 0.0,
        gameplay_data: {
          selected_fraction: selected,
          correct_fraction: this.data.correctAnswer
        }
      });
    }
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  updateData(newData) {
    this.data = newData;
    this.hasAnswered = false;
    this.currentNumerator = this.data.numerator !== undefined ? this.data.numerator : 1;
    this.currentDenominator = this.data.denominator || 4;
    this.render();
  }

  destroy() {
    this.container.innerHTML = '';
  }
}

export function initGame(container, data, config) {
  return new FractionLabGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.FractionLab = { initGame, FractionLabGame };
  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry['fraction-lab'] = { id: 'fraction-lab', initGame };
  window.TezMindzGameRegistry['fraction_lab'] = window.TezMindzGameRegistry['fraction-lab'];
}
