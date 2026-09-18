/**
 * Geometry Explorer Game Template
 * 100% Data-Driven Olympiad Geometry, Perimeter & Polygon Game
 */
import { ShapeCanvas } from './components/ShapeCanvas.js';

export class GeometryExplorerGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;
    if (!this.container) throw new Error('[GeometryExplorerGame] Container not found.');
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
    root.className = 'tm-game-geometry';

    // Header
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">📐 Geometry & Perimeter</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Calculate the measurement')}</h2>
    `;
    root.appendChild(header);

    // Shape canvas
    const canvas = new ShapeCanvas(this.data.shape || {});
    canvas.render(root);

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
    feedback.id = 'tm-geometry-feedback';
    feedback.style.display = 'none';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleSelect(selected) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;

    const isCorrect = String(selected).trim() === String(this.data.correctAnswer).trim();
    const fb = this.container.querySelector('#tm-geometry-feedback');
    if (fb) {
      fb.style.display = 'block';
      fb.className = `tm-feedback ${isCorrect ? 'tm-feedback-correct' : 'tm-feedback-wrong'}`;
      fb.innerHTML = `
        <div style="font-weight: 800; margin-bottom: 4px;">${isCorrect ? '✓ Exact Geometric Measure!' : '✕ Measure Incorrect'}</div>
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
}

export function initGame(container, data, config) {
  return new GeometryExplorerGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.GeometryExplorer = { initGame, GeometryExplorerGame };
}
