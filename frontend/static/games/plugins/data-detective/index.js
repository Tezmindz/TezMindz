/**
 * Data Detective Game Template
 * 100% Data-Driven Olympiad Data Handling & Charts Game
 * Ported from reference GraphExplorer.tsx
 */
import { BarGraph } from './components/BarGraph.js';

export class DataDetectiveGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;
    if (!this.container) throw new Error('[DataDetectiveGame] Container not found.');
    this.data = data || {};
    this.config = Object.assign({ onAnswer: null, onComplete: null }, config);
    this.hasAnswered = false;
    this.graph = null;
    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';
    const root = document.createElement('div');
    root.className = 'tm-game-chart';

    // Header
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">📊 Data Handling &amp; Graphs</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Inspect the data graph to find the solution')}</h2>
    `;
    root.appendChild(header);

    // Interactive Chart component
    this.graph = new BarGraph(
      this.data.chartData || [
        { label: "Aarav", value: 15, color: "#38bdf8" },
        { label: "Diya", value: 25, color: "#a855f7" },
        { label: "Kabir", value: 20, color: "#34d399" },
        { label: "Tanvi", value: 30, color: "#f59e0b" }
      ],
      this.data.unitLabel || 'Books Read',
      {
        onSelect: (bar) => {
          // Dynamic inspection
        }
      }
    );
    this.graph.render(root);

    // Options
    const optionsGrid = document.createElement('div');
    optionsGrid.className = 'tm-options-grid';
    (this.data.options || []).forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'tm-option-btn';
      btn.textContent = opt;
      btn.addEventListener('click', () => this.handleSelect(opt, btn));
      optionsGrid.appendChild(btn);
    });
    root.appendChild(optionsGrid);

    // Feedback
    const feedback = document.createElement('div');
    feedback.id = 'tm-chart-feedback';
    feedback.style.display = 'none';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleSelect(selected, btnEl) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;

    const isCorrect = String(selected).trim().toLowerCase() === String(this.data.correctAnswer).trim().toLowerCase();

    if (btnEl) {
      btnEl.classList.add(isCorrect ? 'tm-opt-correct' : 'tm-opt-wrong');
    }

    const fb = this.container.querySelector('#tm-chart-feedback');
    if (fb) {
      fb.style.display = 'block';
      fb.className = `tm-feedback ${isCorrect ? 'tm-feedback-correct' : 'tm-feedback-wrong'}`;
      fb.innerHTML = `
        <div style="font-weight: 800; margin-bottom: 4px;">${isCorrect ? '✓ Accurate Data Deduction!' : '✕ Deduction Mismatch'}</div>
        <div>${this.data.explanation || `The correct answer is ${this.data.correctAnswer}.`}</div>
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
  return new DataDetectiveGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.DataDetective = { initGame, DataDetectiveGame };
  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry['data-detective'] = { id: 'data-detective', initGame };
  window.TezMindzGameRegistry['data_detective'] = window.TezMindzGameRegistry['data-detective'];
}
