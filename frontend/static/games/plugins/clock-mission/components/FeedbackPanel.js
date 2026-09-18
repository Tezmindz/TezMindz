/**
 * FeedbackPanel Component
 * Handles correct/incorrect state, mathematical explanations, and hints.
 */
export class FeedbackPanel {
  constructor(options = {}) {
    this.explanation = options.explanation || '';
    this.hint = options.hint || '';
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-feedback-panel tm-hidden';
    parentElement.appendChild(this.container);
  }

  showSuccess(explanation) {
    this.container.className = 'tm-feedback-panel tm-feedback-success';
    this.container.innerHTML = `
      <div class="tm-feedback-badge">✓ Correct! Concept Mastered</div>
      <div class="tm-feedback-body">${explanation || this.explanation}</div>
    `;
    this.container.classList.remove('tm-hidden');
  }

  showError(correctAnswer, explanation) {
    this.container.className = 'tm-feedback-panel tm-feedback-error';
    this.container.innerHTML = `
      <div class="tm-feedback-badge">✕ Keep Trying!</div>
      <div class="tm-feedback-meta">Correct Answer: <strong>${correctAnswer}</strong></div>
      <div class="tm-feedback-body">${explanation || this.explanation}</div>
    `;
    this.container.classList.remove('tm-hidden');
  }

  showHint() {
    this.container.className = 'tm-feedback-panel tm-feedback-hint';
    this.container.innerHTML = `
      <div class="tm-feedback-badge">💡 Strategic Hint</div>
      <div class="tm-feedback-body">${this.hint}</div>
    `;
    this.container.classList.remove('tm-hidden');
  }

  hide() {
    if (this.container) {
      this.container.className = 'tm-feedback-panel tm-hidden';
      this.container.innerHTML = '';
    }
  }
}
