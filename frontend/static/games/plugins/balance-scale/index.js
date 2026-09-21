/**
 * Balance Scale Game Template
 * 100% Data-Driven Olympiad Balance Equation Game
 */
import { ScaleBeam } from './components/ScaleBeam.js';

export class BalanceScaleGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;
    if (!this.container) throw new Error('[BalanceScaleGame] Container not found.');
    this.data = data || {};
    this.config = Object.assign({ onAnswer: null, onComplete: null }, config);
    this.hasAnswered = false;
    this.scale = null;
    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';
    const root = document.createElement('div');
    root.className = 'tm-game-balance';

    // Header
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">⚖️ Algebraic Balance Quest</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Solve the balance scale equation')}</h2>
    `;
    root.appendChild(header);

    // Interactive Scale component
    const leftPan = this.data.leftPan || { items: ["⭐", "5 kg"], weight: 10 };
    const rightPan = this.data.rightPan || { items: ["15 kg"], weight: 15 };
    this.scale = new ScaleBeam(leftPan, rightPan, {
      unit: this.data.unit || 'kg',
      onChange: (state) => {
        // Dynamic balance notification
      }
    });
    this.scale.render(root);

    // Options Grid
    const optionsGrid = document.createElement('div');
    optionsGrid.className = 'tm-options-grid';
    (this.data.options || [5, 10, 15, 20]).forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'tm-option-btn';
      btn.textContent = typeof opt === 'number' ? `${opt} ${this.data.unit || 'kg'}` : opt;
      btn.addEventListener('click', () => this.handleSelect(opt, btn));
      optionsGrid.appendChild(btn);
    });
    root.appendChild(optionsGrid);

    // Feedback
    const feedback = document.createElement('div');
    feedback.id = 'tm-balance-feedback';
    feedback.style.display = 'none';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleSelect(selected, btnEl) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;

    const isCorrect = String(selected).trim().replace(/[^\d]/g, '') === String(this.data.correctAnswer).trim().replace(/[^\d]/g, '');

    if (btnEl) {
      btnEl.classList.add(isCorrect ? 'tm-opt-correct' : 'tm-opt-wrong');
    }

    const fb = this.container.querySelector('#tm-balance-feedback');
    if (fb) {
      fb.style.display = 'block';
      fb.className = `tm-feedback ${isCorrect ? 'tm-feedback-correct' : 'tm-feedback-wrong'}`;
      fb.innerHTML = `
        <div style="font-weight: 800; margin-bottom: 4px;">${isCorrect ? '✓ Balanced Perfectly!' : '✕ Out of Balance'}</div>
        <div>${this.data.explanation || `The unknown weight is ${this.data.correctAnswer}.`}</div>
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
      this.config.onComplete({ score: isCorrect ? 100 : 0 });
    }
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  updateData(newData) {
    this.data = newData;
    this.hasAnswered = false;
    this.render();
  }

  destroy() {
    this.container.innerHTML = '';
  }
}

export function initGame(container, data, config) {
  return new BalanceScaleGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.BalanceScale = { initGame, BalanceScaleGame };
  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry['balance-scale'] = { id: 'balance-scale', initGame };
  window.TezMindzGameRegistry['balance_scale'] = window.TezMindzGameRegistry['balance-scale'];
}
