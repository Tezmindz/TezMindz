/**
 * TezMindz Universal Game Shell & Plugin Runner
 * 
 * Auto-discovers and mounts game plugins adhering to the standard lifecycle contract:
 *   initGame(container, gameData, callbacks)
 *
 * Dynamically resolves plugin slugs without hardcoded game lists:
 * - Scans candidate slugs derived from context.game_type, context.slug, context.title
 * - Probes and parses game.manifest.json to locate folder and metadata
 * - Dynamically loads stylesheets (manifest.styles or styles.css)
 * - Dynamically imports index.js (supporting modern ES modules and classic IIFE scripts)
 * - Harmonizes question/sample data and standard lifecycle callbacks
 *
 * Enforces authoritative reward granting:
 *   Client reports gameplay metrics (score, accuracy, time_spent, gameplay_data);
 *   Backend calculates and grants XP and Coins via the gamification ledger.
 */

function toSlug(str) {
  if (!str || typeof str !== 'string') return '';
  return str
    .toLowerCase()
    .trim()
    .replace(/_/g, '-')
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}

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
        if (this.activePlugin && this.activePlugin.config) {
          this.activePlugin.config.soundEnabled = !this.isMuted;
        }
      });
    }
  }

  /**
   * Dynamically generate candidate plugin slugs from context
   * without hardcoding individual game names.
   */
  getCandidateSlugs() {
    const candidates = [];
    const addCandidate = (val) => {
      const s = toSlug(val);
      if (s && s !== 'other' && !candidates.includes(s)) {
        candidates.push(s);
      }
    };

    // 1. Explicit slug / plugin fields in context or config
    addCandidate(this.context.plugin);
    addCandidate(this.context.plugin_slug);
    addCandidate(this.context.slug);
    if (this.context.config && typeof this.context.config === 'object') {
      addCandidate(this.context.config.plugin);
      addCandidate(this.context.config.plugin_slug);
      addCandidate(this.context.config.slug);
    }

    // 2. game_type field (e.g. clock-mission, number_detective, fraction_pizza)
    addCandidate(this.context.game_type);

    // 3. title field (e.g. "Clock Mission", "Geometry Arena Quest")
    addCandidate(this.context.title);

    // 4. Sub-phrases if title contains punctuation/delimiters
    if (this.context.title) {
      const parts = this.context.title.split(/[:\-\(\)—\|]/);
      for (const part of parts) {
        addCandidate(part);
      }
    }

    return candidates;
  }

  /**
   * Dynamically resolve plugin folder and load game.manifest.json
   */
  async resolvePluginManifest() {
    const candidates = this.getCandidateSlugs();
    console.log('[TezMindz GameShell] Probing candidate plugin slugs:', candidates);

    let manifest = null;
    let resolvedSlug = null;

    for (const slug of candidates) {
      try {
        const res = await fetch(`/static/games/plugins/${slug}/game.manifest.json`);
        if (res.ok) {
          manifest = await res.json();
          resolvedSlug = slug;
          console.log(`[TezMindz GameShell] Successfully discovered plugin '${slug}' via manifest:`, manifest);
          break;
        }
      } catch (e) {
        // Continue searching
      }
    }

    // Fallback if manifest probe didn't resolve (e.g. offline)
    if (!resolvedSlug) {
      resolvedSlug = candidates[0] || 'number-train';
      console.warn(`[TezMindz GameShell] Could not discover manifest from candidates. Using fallback '${resolvedSlug}'.`);
    }

    return { resolvedSlug, manifest };
  }

  async loadPlugin() {
    const { resolvedSlug, manifest } = await this.resolvePluginManifest();
    const slug = resolvedSlug;
    console.log(`[TezMindz GameShell] Loading plugin: '${slug}'`);

    const stylesFile = (manifest && (manifest.styles || manifest.style)) || 'styles.css';
    const entryPoint = (manifest && (manifest.entryPoint || manifest.entrypoint)) || 'index.js';

    // 1. Inject Stylesheet if not already present
    const cssId = `plugin-style-${slug}`;
    if (!document.getElementById(cssId)) {
      const link = document.createElement('link');
      link.id = cssId;
      link.rel = 'stylesheet';
      link.href = `/static/games/plugins/${slug}/${stylesFile}`;
      document.head.appendChild(link);
    }

    // 2. Dynamically load script (supports ES module imports/exports & standard IIFE scripts)
    const scriptUrl = `/static/games/plugins/${slug}/${entryPoint}`;
    let moduleObj = null;

    try {
      moduleObj = await import(scriptUrl);
    } catch (importErr) {
      console.warn(`[TezMindz GameShell] Dynamic import of '${scriptUrl}' failed:`, importErr);
      // Fallback: inject via script tag if not yet in window.TezMindzGameRegistry
      if (!window.TezMindzGameRegistry || !window.TezMindzGameRegistry[slug]) {
        try {
          await this.loadScript(scriptUrl);
        } catch (scriptErr) {
          console.warn(`[TezMindz GameShell] Standard script tag failed, attempting type=module:`, scriptErr);
          await this.loadScript(scriptUrl, true);
        }
      }
    }

    // 3. Resolve initGame function across ES module exports and registries
    let initFn = null;

    // A) From ES module namespace
    if (moduleObj) {
      if (typeof moduleObj.initGame === 'function') {
        initFn = moduleObj.initGame;
      } else if (moduleObj.default) {
        if (typeof moduleObj.default.initGame === 'function') {
          initFn = moduleObj.default.initGame;
        } else if (typeof moduleObj.default === 'function') {
          initFn = moduleObj.default;
        }
      }
    }

    // B) From window.TezMindzGameRegistry
    window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
    if (!initFn && window.TezMindzGameRegistry) {
      const reg = window.TezMindzGameRegistry;
      const keys = [slug, slug.replace(/-/g, '_'), slug.replace(/_/g, '-')];
      for (const k of keys) {
        if (reg[k] && typeof reg[k].initGame === 'function') {
          initFn = reg[k].initGame;
          break;
        }
      }
    }

    // C) From window.TezMindz namespace (e.g. window.TezMindz.ClockMission)
    if (!initFn && window.TezMindz) {
      const pascalSlug = slug
        .split('-')
        .map(p => p.charAt(0).toUpperCase() + p.slice(1))
        .join('');
      
      const nsCandidates = [
        window.TezMindz[pascalSlug],
        window.TezMindz[slug],
        window.TezMindz[slug.replace(/-/g, '_')]
      ];

      for (const ns of nsCandidates) {
        if (ns && typeof ns.initGame === 'function') {
          initFn = ns.initGame;
          break;
        }
      }

      if (!initFn) {
        const cleanSlug = slug.replace(/[^a-z0-9]/gi, '').toLowerCase();
        for (const [k, v] of Object.entries(window.TezMindz)) {
          if (k.toLowerCase().replace(/[^a-z0-9]/g, '') === cleanSlug) {
            if (v && typeof v.initGame === 'function') {
              initFn = v.initGame;
              break;
            }
          }
        }
      }
    }

    // Ensure central registry is populated
    if (initFn) {
      window.TezMindzGameRegistry[slug] = {
        id: slug,
        initGame: initFn
      };
    } else {
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

    // 4. Assemble harmonized gameData payload
    const sampleData = (manifest && manifest.sampleData) ? JSON.parse(JSON.stringify(manifest.sampleData)) : {};
    const firstQ = (this.context.questions && this.context.questions.length > 0) ? this.context.questions[0] : null;

    const gameData = Object.assign(
      {},
      sampleData,
      {
        gameId: this.context.game_id || this.context.id,
        title: this.context.title,
        slug: slug,
        difficulty: this.context.difficulty || 'easy',
        config: Object.assign({}, (manifest && (manifest.config || manifest.default_config)) || {}, this.context.config || {}),
        questions: this.context.questions || [],
        sessionId: this.context.session_id,
        student: this.context.student || {}
      }
    );

    if (firstQ) {
      if (firstQ.prompt) gameData.prompt = firstQ.prompt;
      if (firstQ.correct_answer) gameData.correctAnswer = firstQ.correct_answer;
      if (firstQ.hints && firstQ.hints.length > 0) {
        gameData.hint = firstQ.hints[0];
        gameData.hints = firstQ.hints;
      }
      if (firstQ.data && typeof firstQ.data === 'object') {
        Object.assign(gameData, firstQ.data);
      }
    }

    // 5. Assemble standard lifecycle callbacks & options
    const callbacks = {
      theme: 'light',
      soundEnabled: !this.isMuted,
      onComplete: (completionData) => this.handleGameComplete(completionData),
      onProgress: (progressData) => this.handleGameProgress(progressData),
      onError: (error) => this.handleGameError(error),
      onAnswer: (answerData) => {
        console.log(`[TezMindz GameShell] Answer registered:`, answerData);
        if (answerData && answerData.isCorrect !== undefined && this.scoreElement) {
          this.scoreElement.textContent = answerData.isCorrect ? '100' : '0';
        }
      },
      onHint: (hintData) => {
        console.log(`[TezMindz GameShell] Hint requested:`, hintData);
      }
    };

    // 6. Mount and initialize the game plugin
    try {
      this.activePlugin = initFn(this.container, gameData, callbacks);
    } catch (err) {
      console.error(`[TezMindz GameShell] Error during initGame for '${slug}':`, err);
      this.handleGameError(err);
    }
  }

  loadScript(src, isModule = false) {
    return new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[src="${src}"]`);
      if (existing) {
        return resolve();
      }
      const script = document.createElement('script');
      if (isModule) {
        script.type = 'module';
      }
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
    const finalScore = (completionData && completionData.score !== undefined) ? completionData.score : 100;

    console.log("[TezMindz GameShell] Submitting game results to authoritative backend...", completionData);

    const submitPayload = {
      game_id: gameId,
      score: finalScore,
      accuracy: (completionData && completionData.accuracy !== undefined) ? completionData.accuracy : 1.0,
      time_spent: (completionData && completionData.time_spent) || elapsedSeconds,
      gameplay_data: (completionData && completionData.gameplay_data) || {}
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
