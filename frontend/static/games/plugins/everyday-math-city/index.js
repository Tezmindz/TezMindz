/**
 * Everyday Math City Game Engine
 * World 4: Everyday Mathematics, Shopping, Money, Time & Measurement
 * TezMindz 5-Stage Mastery Architecture
 */
import { MarketRegister } from './components/MarketRegister.js';
import { TimelineTracker } from './components/TimelineTracker.js';

export class EverydayMathCityGame {
  constructor(container, data, config = {}) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;

    if (!this.container) {
      throw new Error('[EverydayMathCityGame] Target container not found.');
    }

    this.data = data || {};
    this.config = Object.assign({
      theme: 'light',
      soundEnabled: true,
      onAnswer: null,
      onComplete: null,
      onHint: null
    }, config);

    this.currentStage = this.data.currentStage || 'STAGE_B';
    this.hintIndex = 0;
    this.hasAnswered = false;
    this.selectedOption = null;

    this.init();
  }

  init() {
    this.render();
  }

  render() {
    this.container.innerHTML = '';

    const root = document.createElement('div');
    root.className = 'tm-game-everyday-math';

    // 1. Stage Progress Navigation
    const stageNav = document.createElement('div');
    stageNav.className = 'tm-stage-nav';
    const stages = [
      { id: 'STAGE_A', label: 'Stage A: Discovery' },
      { id: 'STAGE_B', label: 'Stage B: Guided Sim' },
      { id: 'STAGE_C', label: 'Stage C: Rule Discovery' },
      { id: 'STAGE_D', label: 'Stage D: Practice' },
      { id: 'STAGE_E', label: 'Stage E: Anti-Memorisation' }
    ];
    stageNav.innerHTML = stages.map(s => `
      <button class="tm-stage-pill ${this.currentStage === s.id ? 'active' : ''}" data-stage="${s.id}">
        ${s.label}
      </button>
    `).join('');
    stageNav.querySelectorAll('.tm-stage-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.currentStage = e.target.getAttribute('data-stage');
        this.hasAnswered = false;
        this.hintIndex = 0;
        this.render();
      });
    });
    root.appendChild(stageNav);

    // 2. Header
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">🏙️ Everyday Math City</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Solve the real-world math challenge')}</h2>
      ${this.data.subPrompt ? `<p class="tm-subprompt">${this.escapeHtml(this.data.subPrompt)}</p>` : ''}
    `;
    root.appendChild(header);

    // Stage A: Concept Discovery
    if (this.currentStage === 'STAGE_A') {
      const discovery = document.createElement('div');
      discovery.className = 'tm-discovery-card';
      const qList = (this.data.discoveryGuidingQuestions || [
        "How do you determine unit price from a bulk price pack?",
        "Why is change returned always the difference between cash given and bill amount?",
        "How do minutes relate to portions of an hour (15m = 1/4 hr, 30m = 1/2 hr)?"
      ]).map(q => `<li>${this.escapeHtml(q)}</li>`).join('');

      discovery.innerHTML = `
        <div class="tm-discovery-title">🔍 Explore & Observe:</div>
        <ul class="tm-discovery-list">${qList}</ul>
        <div class="tm-discovery-sub">Review the receipt and schedule data below.</div>
      `;
      root.appendChild(discovery);
    }

    // 3. Interactive Playground (Hidden in Stage E if anti-memorisation)
    const hideRegister = this.currentStage === 'STAGE_E' && this.data.antiMemorisation?.hideRegister;
    if (!hideRegister) {
      const playground = document.createElement('div');
      playground.className = 'tm-playground';

      if (this.data.cartItems && this.data.cartItems.length > 0) {
        const register = new MarketRegister(
          this.data.cartItems,
          this.data.currency || '₹',
          this.data.paidAmount || 0
        );
        register.render(playground);
      }

      if (this.data.timeData) {
        const tracker = new TimelineTracker(this.data.timeData);
        tracker.render(playground);
      }

      root.appendChild(playground);
    } else {
      const abstractNotice = document.createElement('div');
      abstractNotice.className = 'tm-abstract-notice';
      abstractNotice.innerHTML = `
        <div class="tm-abstract-icon">🧠</div>
        <div class="tm-abstract-title">Anti-Memorisation Challenge</div>
        <p>Solve this applied word problem with mental math without visual cash register scaffolding.</p>
      `;
      root.appendChild(abstractNotice);
    }

    // Stage C: Rule Discovery
    if (this.currentStage === 'STAGE_C' && this.data.ruleDiscovery) {
      const ruleBox = document.createElement('div');
      ruleBox.className = 'tm-rule-box';
      ruleBox.innerHTML = `
        <div class="tm-rule-prompt">${this.escapeHtml(this.data.ruleDiscovery.statementPrompt || 'State the discovered consumer rule:')}</div>
        <div class="tm-rule-options">
          ${(this.data.ruleDiscovery.ruleOptions || []).map(opt => `
            <button class="tm-rule-opt-btn" data-rule="${this.escapeHtml(opt)}">
              ${this.escapeHtml(opt)}
            </button>
          `).join('')}
        </div>
      `;
      ruleBox.querySelectorAll('.tm-rule-opt-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const chosen = e.currentTarget.getAttribute('data-rule');
          const isRuleCorrect = chosen === this.data.ruleDiscovery.correctRule;
          e.currentTarget.style.borderColor = isRuleCorrect ? '#10b981' : '#f43f5e';
          e.currentTarget.style.backgroundColor = isRuleCorrect ? '#ecfdf5' : '#fff1f2';
        });
      });
      root.appendChild(ruleBox);
    }

    // 4. Progressive Hints (Stages B & D)
    const hints = this.data.progressiveHints || (this.data.hint ? [this.data.hint] : []);
    if (hints.length > 0 && (this.currentStage === 'STAGE_B' || this.currentStage === 'STAGE_D')) {
      const hintSection = document.createElement('div');
      hintSection.className = 'tm-hint-section';
      const currentHint = hints[Math.min(this.hintIndex, hints.length - 1)];
      hintSection.innerHTML = `
        <div class="tm-hint-header">
          <span>💡 Progressive Hint (${this.hintIndex + 1} of ${hints.length})</span>
          ${this.hintIndex < hints.length - 1 ? `<button class="tm-next-hint-btn">Next Step Hint →</button>` : ''}
        </div>
        <div class="tm-hint-body">${this.escapeHtml(currentHint)}</div>
      `;
      const nextBtn = hintSection.querySelector('.tm-next-hint-btn');
      if (nextBtn) {
        nextBtn.addEventListener('click', () => {
          this.hintIndex = Math.min(this.hintIndex + 1, hints.length - 1);
          this.render();
        });
      }
      root.appendChild(hintSection);
    }

    // 5. Options Grid
    const optionsGrid = document.createElement('div');
    optionsGrid.className = 'tm-options-grid';
    (this.data.options || []).forEach((opt, idx) => {
      const btn = document.createElement('button');
      btn.className = 'tm-option-btn';
      btn.textContent = opt;
      btn.setAttribute('data-option', opt);
      btn.setAttribute('data-index', idx);
      btn.addEventListener('click', () => this.handleOptionSelect(opt, btn));
      optionsGrid.appendChild(btn);
    });
    root.appendChild(optionsGrid);

    // 6. Feedback Container
    const feedback = document.createElement('div');
    feedback.className = 'tm-feedback-panel';
    feedback.id = 'tm-everyday-feedback';
    feedback.style.display = 'none';
    root.appendChild(feedback);

    this.container.appendChild(root);
  }

  handleOptionSelect(selectedText, buttonElement) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;
    this.selectedOption = selectedText;

    const isCorrect = String(selectedText).trim() === String(this.data.correctAnswer).trim();

    if (buttonElement) {
      buttonElement.classList.add(isCorrect ? 'tm-option-correct' : 'tm-option-wrong');
    }

    const fb = this.container.querySelector('#tm-everyday-feedback');
    if (fb) {
      fb.style.display = 'block';
      fb.className = `tm-feedback-panel ${isCorrect ? 'tm-feedback-correct' : 'tm-feedback-wrong'}`;
      fb.innerHTML = `
        <div class="tm-feedback-title">${isCorrect ? '🎉 Smart Consumer!' : '💡 Calculation Review'}</div>
        <div class="tm-feedback-text">
          ${isCorrect ? 'Your real-world math calculation is accurate!' : `Correct Answer: <strong>${this.escapeHtml(this.data.correctAnswer)}</strong>`}
        </div>
        ${this.data.explanation ? `<div class="tm-feedback-explanation">${this.escapeHtml(this.data.explanation)}</div>` : ''}
      `;
    }

    if (this.config.onAnswer) {
      this.config.onAnswer({
        questionId: this.data.questionId,
        selectedAnswer: selectedText,
        correctAnswer: this.data.correctAnswer,
        isCorrect,
        stage: this.currentStage
      });
    }

    if (this.config.onComplete && isCorrect) {
      this.config.onComplete({
        questionId: this.data.questionId,
        score: 100,
        stars: 3
      });
    }
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  updateData(newData) {
    this.data = newData;
    this.hasAnswered = false;
    this.selectedOption = null;
    this.hintIndex = 0;
    this.render();
  }
}

export function initGame(container, data, config) {
  return new EverydayMathCityGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.EverydayMathCity = { initGame, EverydayMathCityGame };
  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry['everyday-math-city'] = { id: 'everyday-math-city', initGame };
}
