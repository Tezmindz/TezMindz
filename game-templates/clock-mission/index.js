/**
 * Clock Mission - Main Simulation Engine
 * Concept: Measurement of Time, Timelines, Elapsed Time & Clock Mechanics
 * Implements the Tezmindz 5-Stage Mastery Architecture
 */
import { ClockFace } from './components/ClockFace.js';
import { FeedbackPanel } from './components/FeedbackPanel.js';

export class ClockMissionGame {
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

    this.currentStage = this.data.currentStage || 'STAGE_B';
    this.hintIndex = 0;
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

    // 2. Header (Question Prompt from JSON)
    const header = document.createElement('div');
    header.className = 'tm-header';
    header.innerHTML = `
      <span class="tm-badge">⏱️ Concept: Time & Timelines</span>
      <h2 class="tm-prompt">${this.escapeHtml(this.data.prompt || 'Calculate the time')}</h2>
      ${this.data.subPrompt ? `<p class="tm-subprompt">${this.escapeHtml(this.data.subPrompt)}</p>` : ''}
    `;
    root.appendChild(header);

    // Stage A: Discovery Prompts
    if (this.currentStage === 'STAGE_A') {
      const discoveryBox = document.createElement('div');
      discoveryBox.className = 'tm-discovery-card';
      const qList = (this.data.discoveryGuidingQuestions || [
        "What happens to the hour hand when the minute hand moves 60 minutes?",
        "What remains constant when you jump by 1 hour?"
      ]).map(q => `<li>${this.escapeHtml(q)}</li>`).join('');

      discoveryBox.innerHTML = `
        <div class="tm-discovery-title">🔍 Explore & Observe:</div>
        <ul class="tm-discovery-list">${qList}</ul>
        <div class="tm-discovery-sub">Manipulate the clock hands below to test your hypothesis.</div>
      `;
      root.appendChild(discoveryBox);
    }

    // 3. Interactive Playground (Hidden in Stage E if anti-memorisation hides visual)
    const hideVisual = this.currentStage === 'STAGE_E' && this.data.antiMemorisation?.hideClockVisual;
    if (!hideVisual) {
      const playground = document.createElement('div');
      playground.className = 'tm-playground';

      const initHours = this.data.initialTime ? this.data.initialTime.hours : 12;
      const initMinutes = this.data.initialTime ? this.data.initialTime.minutes : 0;

      this.clockFace = new ClockFace(playground, {
        hours: initHours,
        minutes: initMinutes,
        interactive: this.config.allowDragHands,
        onTimeChange: (time) => this.handleTimeManipulated(time)
      });

      root.appendChild(playground);
    } else {
      const abstractNotice = document.createElement('div');
      abstractNotice.className = 'tm-abstract-notice';
      abstractNotice.innerHTML = `
        <div class="tm-abstract-icon">🧠</div>
        <div class="tm-abstract-title">Anti-Memorisation Challenge</div>
        <p>Solve this unseen question by pure mathematical reasoning without visual clock assistance.</p>
      `;
      root.appendChild(abstractNotice);
    }

    // Stage C: Rule Formulation Mode
    if (this.currentStage === 'STAGE_C' && this.data.ruleDiscovery) {
      const ruleBox = document.createElement('div');
      ruleBox.className = 'tm-rule-box';
      ruleBox.innerHTML = `
        <div class="tm-rule-prompt">${this.escapeHtml(this.data.ruleDiscovery.statementPrompt || 'State the discovered mathematical rule:')}</div>
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

    // 4. Progressive Hints Engine (Stages B & D)
    const hints = this.data.progressiveHints || (this.data.hint ? [this.data.hint] : []);
    if (hints.length > 0 && (this.currentStage === 'STAGE_B' || this.currentStage === 'STAGE_D')) {
      const hintSection = document.createElement('div');
      hintSection.className = 'tm-hint-section';
      
      const currentHintText = hints[Math.min(this.hintIndex, hints.length - 1)];
      hintSection.innerHTML = `
        <div class="tm-hint-header">
          <span>💡 Progressive Hint (${this.hintIndex + 1} of ${hints.length})</span>
          ${this.hintIndex < hints.length - 1 ? `<button class="tm-next-hint-btn">Next Step Hint →</button>` : ''}
        </div>
        <div class="tm-hint-body">${this.escapeHtml(currentHintText)}</div>
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
    const feedbackContainer = document.createElement('div');
    feedbackContainer.id = 'tm-feedback-root';
    root.appendChild(feedbackContainer);
    this.feedbackPanel = new FeedbackPanel(feedbackContainer);

    this.container.appendChild(root);
  }

  handleTimeManipulated(time) {
    if (this.config.onManipulate) {
      this.config.onManipulate(time);
    }
  }

  handleOptionSelect(selectedText, buttonElement) {
    if (this.hasAnswered) return;
    this.hasAnswered = true;
    this.selectedOption = selectedText;

    const isCorrect = String(selectedText).trim() === String(this.data.correctAnswer).trim();

    if (buttonElement) {
      buttonElement.classList.add(isCorrect ? 'tm-option-correct' : 'tm-option-wrong');
    }

    this.feedbackPanel.show({
      isCorrect,
      correctAnswer: this.data.correctAnswer,
      explanation: this.data.explanation || 'Review the timeline steps.',
      rule: this.data.ruleDiscovery?.correctRule
    });

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
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
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
  return new ClockMissionGame(container, data, config);
}

if (typeof window !== 'undefined') {
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.ClockMission = { initGame, ClockMissionGame };
}
