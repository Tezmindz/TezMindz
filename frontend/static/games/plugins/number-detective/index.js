/**
 * ==========================================================================
 * Number Detective - Main Game Entry Point
 * 
 * 100% Data-driven Olympiad logic & divisibility detective game.
 * Ported from reference NumberDetective.tsx
 * ==========================================================================
 */

import { ClueBoard } from './components/ClueBoard.js';
import { NumberGrid } from './components/NumberGrid.js';
import { DivisibilityScanner } from './components/DivisibilityScanner.js';

export class NumberDetectiveGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' 
      ? document.querySelector(container) 
      : container;

    if (!this.container) {
      throw new Error('[NumberDetectiveGame] Target container not found.');
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
    this.numberGrid = null;
    this.scanner = null;
    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';

    const root = document.createElement('div');
    root.className = 'tm-game-detective';

    // 1. Header with prompt
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">🕵️ Divisibility Case File</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Crack the Mystery Code using Divisibility Rules')}</h2>
    `;
    root.appendChild(header);

    // 2. Interactive Divisibility Scanner
    const scannerHolder = document.createElement('div');
    scannerHolder.className = 'tm-scanner-holder';

    const digits = this.data.digits || (this.data.candidateNumbers && this.data.candidateNumbers[0] ? String(this.data.candidateNumbers[0]).split('') : ["7", "4", "*", "3", "2"]);
    const targetDivisor = this.data.targetDivisor || 9;

    this.scanner = new DivisibilityScanner({
      digits: digits,
      targetDivisor: targetDivisor,
      onTestDigit: (result) => {
        if (result.isDivisible && this.data.correctAnswer === undefined) {
          // If no separate candidate list, the tested digit might be the solution
        }
      }
    });
    this.scanner.render(scannerHolder);
    root.appendChild(scannerHolder);

    // 3. Clue Board (Data-driven from data.clues)
    if (this.data.clues && this.data.clues.length > 0) {
      const clueBoard = new ClueBoard(this.data.clues);
      clueBoard.render(root);
    }

    // 4. Suspect Number Cards / Options (Data-driven from candidateNumbers or options)
    const candidates = this.data.candidateNumbers || this.data.options || [1, 2, 5, 8];
    this.numberGrid = new NumberGrid({
      candidates: candidates,
      onSelect: (selectedNumber) => this.handleNumberSelect(selectedNumber)
    });
    this.numberGrid.render(root);

    // 5. Feedback Panel
    const feedback = document.createElement('div');
    feedback.id = 'tm-detective-feedback';
    feedback.className = 'tm-feedback-panel tm-hidden';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleNumberSelect(selectedNumber) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;

    const isCorrect = String(selectedNumber).trim() === String(this.data.correctAnswer).trim();
    this.numberGrid.highlightResult(this.data.correctAnswer, selectedNumber);

    const feedback = this.container.querySelector('#tm-detective-feedback');
    if (feedback) {
      if (isCorrect) {
        feedback.className = 'tm-feedback-panel tm-feedback-success';
        feedback.innerHTML = `
          <div style="font-weight: 800; margin-bottom: 4px;">🎉 Case Solved! Master Detective!</div>
          <div>${this.data.explanation || 'You correctly satisfied the divisibility rule.'}</div>
        `;
      } else {
        feedback.className = 'tm-feedback-panel tm-feedback-error';
        feedback.innerHTML = `
          <div style="font-weight: 800; margin-bottom: 4px;">✕ Incorrect Code</div>
          <div>The secret number was <strong>${this.data.correctAnswer}</strong>. ${this.data.explanation || ''}</div>
        `;
      }
      feedback.classList.remove('tm-hidden');
    }

    if (typeof this.config.onAnswer === 'function') {
      this.config.onAnswer({
        questionId: this.data.questionId,
        selectedAnswer: selectedNumber,
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
  return new NumberDetectiveGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.NumberDetective = {
    initGame,
    NumberDetectiveGame
  };
  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry['number-detective'] = {
    id: 'number-detective',
    initGame: initGame
  };
  window.TezMindzGameRegistry['number_detective'] = window.TezMindzGameRegistry['number-detective'];
}
