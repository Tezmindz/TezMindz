/**
 * ==========================================================================
 * Number Detective - Main Game Entry Point
 * 
 * 100% Data-driven Olympiad logic detective game.
 * ==========================================================================
 */

import { ClueBoard } from './components/ClueBoard.js';
import { NumberGrid } from './components/NumberGrid.js';

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
      <span class="tm-badge">🕵️ Logic Case File</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Crack the Mystery Code')}</h2>
    `;
    root.appendChild(header);

    // 2. Clue Board (Data-driven from data.clues)
    const clueBoard = new ClueBoard(this.data.clues || []);
    clueBoard.render(root);

    // 3. Suspect Number Cards (Data-driven from data.candidateNumbers)
    this.numberGrid = new NumberGrid({
      candidates: this.data.candidateNumbers || [],
      onSelect: (selectedNumber) => this.handleNumberSelect(selectedNumber)
    });
    this.numberGrid.render(root);

    // 4. Feedback Panel
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
          <div>${this.data.explanation || 'You correctly matched all clues.'}</div>
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
}
