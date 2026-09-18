/**
 * ==========================================================================
 * Clock Mission - Main Game Entry Point
 * 
 * Implements the standardized TezMindz Data-Driven Game Architecture:
 * - Reads question payload strictly from dynamic JSON config
 * - Mounts onto any target DOM element
 * - Emits standard lifecycle events (onAnswer, onComplete, onHint)
 * ==========================================================================
 */

import { ClockFace } from './components/ClockFace.js';
import { FeedbackPanel } from './components/FeedbackPanel.js';

export class ClockMissionGame {
  /**
   * @param {HTMLElement|string} container - Target DOM node or query selector
   * @param {Object} data - Question payload (matching game.manifest.json schema)
   * @param {Object} config - Optional runtime configuration & callbacks
   */
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string' 
      ? document.querySelector(container) 
      : container;

    if (!this.container) {
      throw new Error('[ClockMissionGame] Target container not found.');
    }

    this.data = data || {};
    this.config = Object.assign({
      theme: 'light',
      allowDragHands: true,
      soundEnabled: true,
      onAnswer: null,
      onComplete: null,
      onHint: null
    }, config);

    this.hasAnswered = false;
    this.selectedOption = null;
    this.clockFace = null;
    this.feedbackPanel = null;

    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';

    const root = document.createElement('div');
    root.className = 'tm-game-clock';

    // 1. Header (Question Prompt from JSON)
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">⏱️ Olympiad Time Mission</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Calculate the time')}</h2>
      ${this.data.subPrompt ? `<p class="tm-subprompt">${this.escapeHtml(this.data.subPrompt)}</p>` : ''}
    `;
    root.appendChild(header);

    // 2. Interactive Playground
    const playground = document.createElement('div');
    playground.className = 'tm-playground';

    // Clock Face component initialization with initialTime from JSON
    const initHours = this.data.initialTime ? this.data.initialTime.hours : 12;
    const initMinutes = this.data.initialTime ? this.data.initialTime.minutes : 0;

    this.clockFace = new ClockFace({
      hours: initHours,
      minutes: initMinutes,
      isInteractive: this.config.allowDragHands,
      onChange: (time) => {
        // Can be used for custom calculations
      }
    });
    this.clockFace.render(playground);
    root.appendChild(playground);

    // 3. Options Grid (Data-driven from data.options)
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'tm-options-grid';

    const optionsList = Array.isArray(this.data.options) ? this.data.options : [];
    const labels = ['A', 'B', 'C', 'D', 'E'];

    optionsList.forEach((optionText, idx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'tm-option-btn';
      btn.dataset.index = String(idx);
      btn.dataset.value = optionText;

      btn.innerHTML = `
        <span class="tm-option-label">${labels[idx] || (idx + 1)}</span>
        <span>${this.escapeHtml(optionText)}</span>
      `;

      btn.addEventListener('click', () => this.handleOptionSelect(optionText, btn));
      optionsContainer.appendChild(btn);
    });
    root.appendChild(optionsContainer);

    // 4. Feedback Panel component
    this.feedbackPanel = new FeedbackPanel({
      explanation: this.data.explanation || '',
      hint: this.data.hint || ''
    });
    this.feedbackPanel.render(root);

    // 5. Footer with Hint and Reset
    const footer = document.createElement('div');
    footer.className = 'tm-footer';

    if (this.data.hint) {
      const hintBtn = document.createElement('button');
      hintBtn.type = 'button';
      hintBtn.className = 'tm-hint-btn';
      hintBtn.innerHTML = '💡 Need a Hint?';
      hintBtn.addEventListener('click', () => {
        this.feedbackPanel.showHint();
        if (typeof this.config.onHint === 'function') {
          this.config.onHint({ questionId: this.data.questionId });
        }
      });
      footer.appendChild(hintBtn);
    }

    root.appendChild(footer);
    this.container.appendChild(root);
  }

  handleOptionSelect(optionText, btnElement) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;
    this.selectedOption = optionText;

    const isCorrect = this.checkAnswer(optionText);

    // Update button styles
    const allButtons = this.container.querySelectorAll('.tm-option-btn');
    allButtons.forEach((b) => {
      if (this.checkAnswer(b.dataset.value)) {
        b.classList.add('tm-correct');
      } else if (b === btnElement && !isCorrect) {
        b.classList.add('tm-wrong');
      }
    });

    if (isCorrect) {
      this.feedbackPanel.showSuccess(this.data.explanation);
    } else {
      this.feedbackPanel.showError(this.data.correctAnswer, this.data.explanation);
    }

    // Emit event to host application
    if (typeof this.config.onAnswer === 'function') {
      this.config.onAnswer({
        questionId: this.data.questionId,
        selectedAnswer: optionText,
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

  checkAnswer(answer) {
    if (!this.data.correctAnswer) return false;
    const cleanA = String(answer).trim().toLowerCase();
    const cleanCorrect = String(this.data.correctAnswer).trim().toLowerCase();
    return cleanA === cleanCorrect;
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

  /**
   * Public API to update game dynamically with new JSON data
   */
  updateData(newData) {
    this.data = newData;
    this.hasAnswered = false;
    this.selectedOption = null;
    this.render();
  }

  destroy() {
    this.container.innerHTML = '';
  }
}

/**
 * Standard Universal Factory function
 * Enables simple integration: window.initGame(container, questionJSON, options)
 */
export function initGame(container, data, config) {
  return new ClockMissionGame(container, data, config);
}

// Global browser window attachment for non-bundled embedding
if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.ClockMission = {
    initGame,
    ClockMissionGame
  };
}
