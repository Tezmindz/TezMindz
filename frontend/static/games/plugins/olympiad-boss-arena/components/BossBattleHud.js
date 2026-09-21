/**
 * BossBattleHud Component
 * Interactive Olympiad Boss Battle Stage ported from TezMindz BossBattle.tsx
 * Renders Player vs Boss arena stage, animated health bars, attack effects,
 * and weakness clues.
 */
export class BossBattleHud {
  constructor(bossData = {}) {
    this.bossName = bossData.bossName || bossData.title || "Arch-Sorcerer Mathalon (Achievers Boss)";
    this.bossAvatar = bossData.avatar || "🐲";
    this.maxHp = bossData.maxHp || 100;
    this.currentHp = bossData.currentHp !== undefined ? bossData.currentHp : 100;
    this.isAttacking = false;
  }

  render(container) {
    this.container = container;
    const hud = document.createElement('div');
    hud.className = 'tm-boss-battle-stage';
    this.wrapper = hud;
    this.renderStage();
    container.appendChild(hud);
  }

  renderStage() {
    if (!this.wrapper) return;

    const hpPercent = Math.max(0, Math.min(100, Math.round((this.currentHp / this.maxHp) * 100)));

    this.wrapper.innerHTML = `
      <div class="tm-bbs-flare"></div>
      
      <div class="tm-bbs-top">
        <div class="tm-bbs-title-row">
          <span class="tm-bbs-badge-icon">🛡️</span>
          <h3 class="tm-bbs-name">${this.escapeHtml(this.bossName)}</h3>
        </div>
        <span class="tm-bbs-stage-pill">Achievers Multi-Step</span>
      </div>

      <!-- Boss HP Bar -->
      <div class="tm-bbs-hp-section">
        <div class="tm-bbs-hp-meta">
          <span class="tm-bbs-boss-label">👾 Enemy Boss HP</span>
          <span class="tm-bbs-hp-readout font-mono">${this.currentHp} / ${this.maxHp} HP</span>
        </div>
        <div class="tm-bbs-hp-track">
          <div class="tm-bbs-hp-fill" style="width: ${hpPercent}%;"></div>
        </div>
      </div>

      <!-- Duel Arena Stage -->
      <div class="tm-bbs-arena ${this.isAttacking ? 'is-clashing' : ''}">
        <!-- Player -->
        <div class="tm-bbs-combatant tm-bbs-player">
          <div class="tm-bbs-avatar-circle tm-bbs-player-circle">
            <span class="tm-bbs-emoji">🧑‍🚀</span>
            <span class="tm-bbs-lvl-tag">L5</span>
          </div>
          <span class="tm-bbs-combatant-name">Math Explorer</span>
        </div>

        <!-- Center Clash / Strike Action -->
        <div class="tm-bbs-clash-center">
          <span class="tm-bbs-vs-badge">VS</span>
          <button type="button" class="tm-bbs-attack-btn" id="tm-bbs-btn-strike" title="Test Boss Weakness">
            <span>⚔️ Strike</span>
          </button>
          <span class="tm-bbs-clash-indicator">${this.isAttacking ? '🔥 HIT!' : '⚡ Ready'}</span>
        </div>

        <!-- Boss -->
        <div class="tm-bbs-combatant tm-bbs-boss">
          <div class="tm-bbs-avatar-circle tm-bbs-boss-circle ${this.isAttacking ? 'hit-shake' : ''}">
            <span class="tm-bbs-emoji">${this.bossAvatar}</span>
          </div>
          <span class="tm-bbs-combatant-name">Mathalon Boss</span>
        </div>
      </div>

      <!-- Boss Weakness Checklist -->
      <div class="tm-bbs-weakness-box">
        <span class="tm-bbs-weakness-title">⚔️ Boss Weakness Clues:</span>
        <div class="tm-bbs-clue-line">
          <span class="tm-bbs-clue-step">1</span>
          <span>Break down complex algebraic or geometric relations into 2 separate steps.</span>
        </div>
        <div class="tm-bbs-clue-line">
          <span class="tm-bbs-clue-step">2</span>
          <span>Double check carry-overs, units conversion and negative signs.</span>
        </div>
      </div>
    `;

    const strikeBtn = this.wrapper.querySelector('#tm-bbs-btn-strike');
    if (strikeBtn) {
      strikeBtn.addEventListener('click', () => this.triggerHit(25));
    }
  }

  triggerHit(damage = 25) {
    this.isAttacking = true;
    this.currentHp = Math.max(0, this.currentHp - damage);
    this.renderStage();

    setTimeout(() => {
      this.isAttacking = false;
      this.renderStage();
    }, 600);
  }

  defeat() {
    this.currentHp = 0;
    this.isAttacking = true;
    this.renderStage();
    setTimeout(() => {
      this.isAttacking = false;
      this.renderStage();
    }, 800);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
