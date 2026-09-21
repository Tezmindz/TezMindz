/**
 * ==========================================================================
 * Pattern Machine - Main Game Entry Point
 * 
 * 100% Data-driven Olympiad sequence and logic game.
 * Ported from reference PatternMachine.tsx
 * ==========================================================================
 */

import { PatternRenderer } from './components/PatternRenderer.js';

export class PatternMachineGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' 
      ? document.querySelector(container) 
      : container;

    if (!this.container) {
      throw new Error('[PatternMachineGame] Target container not found.');
    }

    this.data = data || {};
    this.config = Object.assign({
      theme: 'light',
      soundEnabled: true,
      onAnswer: null,
      onComplete: null,
      onHint: null
    }, config);

    this.hasAnswered = false;
    this.renderer = null;
    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';

    const root = document.createElement('div');
    root.className = 'tm-game-pattern';

    // 1. Header with prompt
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">⚙️ Sequence Engine</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Analyze the gear engine and find the missing term')}</h2>
    `;
    root.appendChild(header);

    // 2. Interactive Conveyor & Gear Renderer
    const seq = this.data.sequence || [4, 9, 19, 39, 79, "?"];
    this.renderer = new PatternRenderer(
      seq,
      typeof this.data.missingIndex === 'number' ? this.data.missingIndex : -1,
      {
        deltas: this.data.deltas,
        missingVal: this.data.correctAnswer || 159,
        ruleText: this.data.explanation || "The difference doubles at each step (+5, +10, +20, +40, +80)."
      }
    );
    this.renderer.render(root);

    // 3. Answer Options
    const optionsGrid = document.createElement('div');
    optionsGrid.className = 'tm-options-grid';

    (this.data.options || [149, 159, 169, 179]).forEach((opt) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'tm-option-btn';
      btn.innerHTML = `<span class="tm-option-val">${this.escapeHtml(opt)}</span>`;

      btn.addEventListener('click', () => this.handleSelect(opt, btn));
      optionsGrid.appendChild(btn);
    });
    root.appendChild(optionsGrid);

    // 4. Feedback
    const feedback = document.createElement('div');
    feedback.id = 'tm-pattern-feedback';
    feedback.className = 'tm-feedback-panel tm-hidden';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleSelect(selectedVal, btnEl) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;

    const isCorrect = String(selectedVal).trim() === String(this.data.correctAnswer).trim();
    this.renderer.fillMissingSlot(selectedVal, isCorrect);

    if (btnEl) {
      btnEl.classList.add(isCorrect ? 'tm-opt-correct' : 'tm-opt-wrong');
    }

    const feedback = this.container.querySelector('#tm-pattern-feedback');
    if (feedback) {
      if (isCorrect) {
        feedback.className = 'tm-feedback-panel tm-feedback-success';
        feedback.innerHTML = `
          <div style="font-weight: 800; margin-bottom: 4px;">✓ Sequence Verified!</div>
          <div>${this.data.explanation || 'Rule correctly identified.'}</div>
        `;
      } else {
        feedback.className = 'tm-feedback-panel tm-feedback-error';
        feedback.innerHTML = `
          <div style="font-weight: 800; margin-bottom: 4px;">✕ Pattern Broken</div>
          <div>The missing element was <strong>${this.data.correctAnswer}</strong>. ${this.data.explanation || ''}</div>
        `;
      }
      feedback.classList.remove('tm-hidden');
    }

    if (typeof this.config.onAnswer === 'function') {
      this.config.onAnswer({
        questionId: this.data.questionId,
        selectedAnswer: selectedVal,
        correctAnswer: this.data.correctAnswer,
        isCorrect: isCorrect
      });
    }

    if (typeof this.config.onComplete === 'function') {
      this.config.onComplete({
        score: isCorrect ? 100 : 0,
        stars: isCorrect ? 3 : 1
      });
    }
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
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
  return new PatternMachineGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.PatternMachine = {
    initGame,
    PatternMachineGame
  };
  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry['pattern-machine'] = {
    id: 'pattern-machine',
    initGame: initGame
  };
  window.TezMindzGameRegistry['pattern_machine'] = window.TezMindzGameRegistry['pattern-machine'];
}
