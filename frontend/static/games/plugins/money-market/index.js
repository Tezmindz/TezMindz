/**
 * Money Market Game Template
 * 100% Data-Driven Olympiad Currency and Transactions Game
 */
import { CashRegister } from './components/CashRegister.js';

export class MoneyMarketGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;
    if (!this.container) throw new Error('[MoneyMarketGame] Container not found.');
    this.data = data || {};
    this.config = Object.assign({ onAnswer: null, onComplete: null }, config);
    this.hasAnswered = false;
    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';
    const root = document.createElement('div');
    root.className = 'tm-game-money';

    // Header
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">🪙 Currency & Shopping Math</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Calculate the change')}</h2>
    `;
    root.appendChild(header);

    // Cash register receipt
    const reg = new CashRegister(this.data.items || [], this.data.amountPaid || 0, this.data.currencySymbol || '₹');
    reg.render(root);

    // Options
    const optionsGrid = document.createElement('div');
    optionsGrid.className = 'tm-options-grid';
    (this.data.options || []).forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'tm-option-btn';
      btn.textContent = opt;
      btn.addEventListener('click', () => this.handleSelect(opt));
      optionsGrid.appendChild(btn);
    });
    root.appendChild(optionsGrid);

    // Feedback
    const feedback = document.createElement('div');
    feedback.id = 'tm-money-feedback';
    feedback.style.display = 'none';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleSelect(selected) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;

    const isCorrect = String(selected).trim() === String(this.data.correctAnswer).trim();
    const fb = this.container.querySelector('#tm-money-feedback');
    if (fb) {
      fb.style.display = 'block';
      fb.className = `tm-feedback ${isCorrect ? 'tm-feedback-correct' : 'tm-feedback-wrong'}`;
      fb.innerHTML = `
        <div style="font-weight: 800; margin-bottom: 4px;">${isCorrect ? '✓ Exact Change Calculated!' : '✕ Incorrect Calculation'}</div>
        <div>${this.data.explanation || `The correct change is ${this.data.correctAnswer}.`}</div>
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
}

export function initGame(container, data, config) {
  return new MoneyMarketGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.MoneyMarket = { initGame, MoneyMarketGame };
}
