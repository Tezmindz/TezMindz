/**
 * TezMindz Universal Game Shell & Plugin Runner
 * 
 * Auto-discovers and mounts game plugins adhering to the standard lifecycle contract:
 *   initGame(container, gameData, callbacks)
 *
 * Enforces authoritative reward granting:
 *   Client reports gameplay metrics (score, accuracy, time_spent, gameplay_data);
 *   Backend calculates and grants XP and Coins via the gamification ledger.
 */
class TezMindzGameShell {
  constructor(context) {
    this.context = context || window.GAME_CONTEXT || {};
    this.container = document.getElementById('game-runner-viewport');
    this.timerElement = document.getElementById('shell-hud-timer');
    this.scoreElement = document.getElementById('shell-hud-score');
    this.stageElement = document.getElementById('shell-hud-stage');
    this.victoryModal = document.getElementById('shell-victory-modal');
    
    this.startTime = Date.now();
    this.timerInterval = null;
    this.activePlugin = null;
    this.isMuted = false;
  }

  init() {
    this.startTimer();
    this.initAudioToggle();
    this.loadPlugin();
  }

  startTimer() {
    if (!this.timerElement) return;
    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      const m = Math.floor(elapsed / 60);
      const s = elapsed % 60;
      this.timerElement.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
    }, 1000);
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  initAudioToggle() {
    const btn = document.getElementById('shell-audio-toggle');
    if (btn) {
      btn.addEventListener('click', () => {
        this.isMuted = !this.isMuted;
        btn.innerHTML = this.isMuted ? '🔇 Sound: OFF' : '🔊 Sound: ON';
      });
    }
  }

  resolvePluginSlug() {
    const rawType = (this.context.game_type || '').toLowerCase().trim();
    const rawTitle = (this.context.title || '').toLowerCase().trim();

    // Map common aliases to plugin folder names
    if (rawType === 'house_builder' || rawType === 'house-builder' || rawTitle.includes('house builder')) {
      return 'house-builder';
    }
    if (rawType === 'fraction_pizza' || rawType === 'fraction-pizza' || rawTitle.includes('pizza')) {
      return 'fraction-pizza';
    }
    if (rawType === 'number_train' || rawType === 'number-train' || rawTitle.includes('train')) {
      return 'number-train';
    }
    if (rawType === 'geometry-challenge' || rawType === 'geometry_challenge' || rawTitle.includes('geometry') || rawTitle.includes('shape')) {
      return 'geometry-challenge';
    }

    // Default to game_type with underscores replaced by dashes
    if (rawType && rawType !== 'other') {
      return rawType.replace(/_/g, '-');
    }

    // Fallback default
    return 'number-train';
  }

  async loadPlugin() {
    const slug = this.resolvePluginSlug();
    console.log(`[TezMindz GameShell] Loading plugin template: '${slug}'`);

    // 1. Inject Stylesheet if not already present
    const cssId = `plugin-style-${slug}`;
    if (!document.getElementById(cssId)) {
      const link = document.createElement('link');
      link.id = cssId;
      link.rel = 'stylesheet';
      link.href = `/static/games/plugins/${slug}/styles.css`;
      document.head.appendChild(link);
    }

    // 2. Load Script if not already loaded in window.TezMindzGameRegistry
    if (!window.TezMindzGameRegistry || !window.TezMindzGameRegistry[slug]) {
      await this.loadScript(`/static/games/plugins/${slug}/index.js`);
    }

    const registry = window.TezMindzGameRegistry || {};
    const plugin = registry[slug];

    if (!plugin || typeof plugin.initGame !== 'function') {
      console.error(`[TezMindz GameShell] Plugin '${slug}' does not export a valid initGame function.`);
      if (this.container) {
        this.container.innerHTML = `
          <div style="padding: 40px; text-align: center; background: #FFF1F2; border: 2px solid #FECDD3; border-radius: 20px; margin: 20px auto; max-width: 600px;">
            <h3 style="color: #BE123C; margin-bottom: 8px;">Game Template Not Found</h3>
            <p style="color: #4C0519;">Could not locate game plugin '${slug}'. Verify that <code>frontend/static/games/plugins/${slug}/index.js</code> exists and registers itself.</p>
          </div>
        `;
      }
      return;
    }

    // 3. Assemble gameData payload
    const gameData = {
      gameId: this.context.game_id || this.context.id,
      title: this.context.title,
      slug: slug,
      difficulty: this.context.difficulty || 'easy',
      config: this.context.config || {},
      questions: this.context.questions || [],
      sessionId: this.context.session_id,
      student: this.context.student || {}
    };

    // 4. Assemble standard lifecycle callbacks
    const callbacks = {
      onComplete: (completionData) => this.handleGameComplete(completionData),
      onProgress: (progressData) => this.handleGameProgress(progressData),
      onError: (error) => this.handleGameError(error)
    };

    // 5. Mount and initialize the game plugin
    try {
      this.activePlugin = plugin.initGame(this.container, gameData, callbacks);
    } catch (err) {
      console.error(`[TezMindz GameShell] Error during initGame for '${slug}':`, err);
      this.handleGameError(err);
    }
  }

  loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = () => resolve();
      script.onerror = (e) => reject(e);
      document.body.appendChild(script);
    });
  }

  handleGameProgress(progressData) {
    if (progressData && progressData.score !== undefined && this.scoreElement) {
      this.scoreElement.textContent = progressData.score;
    }
    if (progressData && progressData.stage !== undefined && this.stageElement) {
      const total = progressData.totalStages ? ` / ${progressData.totalStages}` : '';
      this.stageElement.textContent = `Stage ${progressData.stage}${total}`;
    }
  }

  handleGameError(error) {
    const toast = document.getElementById('shell-toast-error');
    if (toast) {
      toast.textContent = `Notice: ${error.message || error}`;
      toast.style.display = 'block';
      setTimeout(() => { toast.style.display = 'none'; }, 4000);
    }
  }

  getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    if (match) return match[1];
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    return this.context.csrfToken || '';
  }

  async handleGameComplete(completionData) {
    this.stopTimer();
    const elapsedSeconds = Math.max(1, Math.round((Date.now() - this.startTime) / 1000));
    const gameId = this.context.game_id || this.context.id;
    const finalScore = completionData.score || 100;

    console.log("[TezMindz GameShell] Submitting game results to authoritative backend...", completionData);

    const submitPayload = {
      game_id: gameId,
      score: finalScore,
      accuracy: completionData.accuracy !== undefined ? completionData.accuracy : 1.0,
      time_spent: completionData.time_spent || elapsedSeconds,
      gameplay_data: completionData.gameplay_data || {}
    };

    try {
      const response = await fetch('/api/game/submit/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken()
        },
        credentials: 'same-origin',
        body: JSON.stringify(submitPayload)
      });

      const result = await response.json();
      console.log("[TezMindz GameShell] Server response:", result);

      const xpEarned = result.xp_awarded !== undefined ? result.xp_awarded : 15;
      const coinsEarned = result.coins_awarded !== undefined ? result.coins_awarded : 5;
      const totalXp = result.total_xp || 0;

      this.showVictoryModal({
        score: finalScore,
        xpEarned: xpEarned,
        coinsEarned: coinsEarned,
        totalXp: totalXp,
        timeSpent: submitPayload.time_spent
      });

    } catch (err) {
      console.error("[TezMindz GameShell] Submit network error:", err);
      // Fallback display if network has an issue
      this.showVictoryModal({
        score: finalScore,
        xpEarned: 15,
        coinsEarned: 5,
        totalXp: 0,
        timeSpent: elapsedSeconds
      });
    }
  }

  showVictoryModal(stats) {
    if (!this.victoryModal) return;

    // Trigger confetti if library loaded
    if (typeof confetti === 'function') {
      confetti({
        particleCount: 120,
        spread: 70,
        origin: { y: 0.6 }
      });
    }

    const xpEl = document.getElementById('shell-modal-xp');
    const coinsEl = document.getElementById('shell-modal-coins');
    const scoreEl = document.getElementById('shell-modal-score');
    const timeEl = document.getElementById('shell-modal-time');

    if (xpEl) xpEl.textContent = `+${stats.xpEarned} XP`;
    if (coinsEl) coinsEl.textContent = `+${stats.coinsEarned} Coins`;
    if (scoreEl) scoreEl.textContent = `${stats.score} PTS`;
    if (timeEl) timeEl.textContent = `${stats.timeSpent}s`;

    this.victoryModal.style.display = 'flex';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.tezMindzShell = new TezMindzGameShell(window.GAME_CONTEXT);
  window.tezMindzShell.init();
});
