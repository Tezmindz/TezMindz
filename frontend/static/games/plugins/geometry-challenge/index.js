/**
 * Geometry & Shapes Arena Plugin
 * Ported from reference ShapeLab & geometry mechanics
 * Standardized TezMindz Game Plugin Contract
 */
(function() {
  const PLUGIN_ID = 'geometry-challenge';

  function initGame(container, gameData, callbacks) {
    const startTime = Date.now();
    let hintsUsed = 0;

    const questions = (gameData && gameData.questions && gameData.questions.length > 0)
      ? gameData.questions
      : null;

    const defaultRounds = [
      {
        shapeType: "triangle",
        shapeName: "Right-Angled Triangle",
        prompt: "Identify the shape that has 3 straight sides, base 12 cm, height 5 cm, and exactly one 90° right angle.",
        dims: { base: 12, height: 5, hypotenuse: 13, unit: "cm" },
        options: [
          { text: "Right-Angled Triangle", isCorrect: true },
          { text: "Equilateral Triangle", isCorrect: false },
          { text: "Rectangle", isCorrect: false },
          { text: "Trapezium", isCorrect: false }
        ],
        hint: "Count the sides: 3 sides make a triangle, and look for the square 90-degree corner!"
      },
      {
        shapeType: "hexagon",
        shapeName: "Regular Hexagon",
        prompt: "A honeycomb cell has 6 equal straight edges and 6 equal vertices. What polygon is this?",
        dims: { side: 6, unit: "cm" },
        options: [
          { text: "Hexagon (6 sides)", isCorrect: true },
          { text: "Pentagon (5 sides)", isCorrect: false },
          { text: "Octagon (8 sides)", isCorrect: false },
          { text: "Heptagon (7 sides)", isCorrect: false }
        ],
        hint: "Prefix 'Hexa' means six in Greek. Count all 6 equal sides."
      },
      {
        shapeType: "cube",
        shapeName: "Cube (3D Solid)",
        prompt: "A 3D solid box with 6 identical square faces, 12 edges, and 8 vertices is called a:",
        dims: { edge: 4, unit: "cm" },
        options: [
          { text: "Cube", isCorrect: true },
          { text: "Cuboid", isCorrect: false },
          { text: "Square Pyramid", isCorrect: false },
          { text: "Cylinder", isCorrect: false }
        ],
        hint: "Think of a standard 6-sided rolling game dice where each face is a square!"
      }
    ];

    let rounds = defaultRounds;
    if (questions) {
      rounds = questions.map((q, idx) => {
        const d = q.data || {};
        const rawOpts = d.options || ["Option A", "Option B", "Option C", "Option D"];
        const correct = String(q.correct_answer || rawOpts[0]);
        const fallback = defaultRounds[idx % defaultRounds.length];
        return {
          shapeType: d.shape_type || fallback.shapeType,
          shapeName: d.shape_name || fallback.shapeName,
          prompt: q.prompt || fallback.prompt,
          dims: d.dimensions || fallback.dims,
          options: rawOpts.map(opt => ({
            text: typeof opt === 'string' ? opt : (opt.text || String(opt)),
            isCorrect: (typeof opt === 'string' ? opt : (opt.text || String(opt))) === correct
          })),
          hint: (q.hints && q.hints[0]) || fallback.hint
        };
      });
    }

    let currentRoundIdx = 0;
    let selectedIdx = null;
    let showGrid = false;

    function renderShapeSVG(round) {
      if (round.shapeType === 'triangle') {
        return `
          <svg viewBox="0 0 240 160" class="geom-svg-shape">
            <polygon points="50,130 190,130 50,30" fill="#fef3c7" stroke="#d97706" stroke-width="3" />
            <!-- Right angle square marker -->
            <rect x="50" y="116" width="14" height="14" fill="none" stroke="#b45309" stroke-width="2" />
            <circle cx="57" cy="123" r="2" fill="#b45309" />
            <!-- Dimension labels -->
            <text x="120" y="146" text-anchor="middle" font-size="11" font-weight="bold" fill="#92400e" font-family="monospace">Base = ${round.dims.base} ${round.dims.unit}</text>
            <text x="36" y="80" text-anchor="middle" font-size="11" font-weight="bold" fill="#92400e" font-family="monospace" transform="rotate(-90 36 80)">Height = ${round.dims.height} ${round.dims.unit}</text>
            <text x="130" y="70" text-anchor="middle" font-size="11" font-weight="bold" fill="#d97706" font-family="monospace" transform="rotate(-35 130 70)">${round.dims.hypotenuse || 13} ${round.dims.unit}</text>
          </svg>
        `;
      } else if (round.shapeType === 'hexagon') {
        return `
          <svg viewBox="0 0 240 160" class="geom-svg-shape">
            <polygon points="120,20 180,55 180,115 120,150 60,115 60,55" fill="#ecfdf5" stroke="#059669" stroke-width="3" />
            <circle cx="120" cy="85" r="4" fill="#059669" />
            <text x="120" y="90" text-anchor="middle" font-size="12" font-weight="bold" fill="#065f46" font-family="sans-serif">6 Equal Sides</text>
            <text x="120" y="12" text-anchor="middle" font-size="10" font-weight="bold" fill="#047857" font-family="monospace">${round.dims.side} ${round.dims.unit}</text>
          </svg>
        `;
      } else {
        // 3D Cube Isometric
        return `
          <svg viewBox="0 0 240 170" class="geom-svg-shape">
            <defs>
              <linearGradient id="cubeT" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#0284c7"/></linearGradient>
              <linearGradient id="cubeL" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0369a1"/><stop offset="100%" stop-color="#075985"/></linearGradient>
              <linearGradient id="cubeR" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0284c7"/><stop offset="100%" stop-color="#0369a1"/></linearGradient>
            </defs>
            <g transform="translate(60, 20)">
              <!-- Top Face -->
              <polygon points="60,0 120,30 60,60 0,30" fill="url(#cubeT)" stroke="#0f172a" stroke-width="1.5" />
              <!-- Left Face -->
              <polygon points="0,30 60,60 60,120 0,90" fill="url(#cubeL)" stroke="#0f172a" stroke-width="1.5" />
              <!-- Right Face -->
              <polygon points="60,60 120,30 120,90 60,120" fill="url(#cubeR)" stroke="#0f172a" stroke-width="1.5" />
            </g>
            <text x="120" y="158" text-anchor="middle" font-size="11" font-weight="bold" fill="#0369a1">6 Identical Square Faces • 12 Edges • 8 Vertices</text>
          </svg>
        `;
      }
    }

    function renderUI() {
      const cur = rounds[currentRoundIdx];
      container.innerHTML = `
        <div class="geometry-arena-wrapper">
          <div class="geom-mission-banner">
            <h2>📐 ${escapeHtml(gameData.title || "Geometry & Shapes Arena")}</h2>
            <p><strong>Mission ${currentRoundIdx + 1} of ${rounds.length}:</strong> ${escapeHtml(cur.prompt)}</p>
          </div>

          <div class="geom-visual-card">
            <div class="geom-card-header">
              <span class="geom-shape-name-tag">🔍 ${escapeHtml(cur.shapeName)}</span>
              <button type="button" class="btn-geom-grid" id="geom-btn-grid">
                ${showGrid ? '✓ Grid ON' : '⊞ Grid Overlay'}
              </button>
            </div>

            <div class="geom-canvas-stage ${showGrid ? 'grid-active' : ''}">
              ${renderShapeSVG(cur)}
            </div>
          </div>

          <div class="geom-options-grid">
            ${cur.options.map((opt, idx) => `
              <button type="button" class="geom-option-btn ${selectedIdx === idx ? 'selected' : ''}" data-idx="${idx}">
                <span class="geom-opt-label">${String.fromCharCode(65 + idx)}.</span>
                <span class="geom-opt-text">${escapeHtml(opt.text)}</span>
              </button>
            `).join('')}
          </div>

          <div class="geom-action-bar">
            <button type="button" class="btn-geom-hint" id="geom-btn-hint">
              💡 Hint
            </button>
            <button type="button" class="btn-geom-submit" id="geom-btn-submit">
              <span>🎯 Confirm Geometric Match</span>
            </button>
          </div>

          <div id="geom-hint-box" style="display:none;" class="geom-hint-toast"></div>
          <div id="geom-feedback-box" class="geom-feedback-toast"></div>
        </div>
      `;

      attachEventListeners();
    }

    function attachEventListeners() {
      const cur = rounds[currentRoundIdx];

      // Grid toggle
      const gridBtn = container.querySelector('#geom-btn-grid');
      if (gridBtn) {
        gridBtn.addEventListener('click', () => {
          showGrid = !showGrid;
          renderUI();
        });
      }

      // Option selection
      container.querySelectorAll('.geom-option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          selectedIdx = parseInt(btn.getAttribute('data-idx'), 10);
          renderUI();
        });
      });

      // Hint
      const hintBtn = container.querySelector('#geom-btn-hint');
      const hintBox = container.querySelector('#geom-hint-box');
      if (hintBtn && hintBox) {
        hintBtn.addEventListener('click', () => {
          hintsUsed++;
          hintBox.style.display = 'block';
          hintBox.innerHTML = `<strong>Geometry Hint:</strong> ${escapeHtml(cur.hint)}`;
        });
      }

      // Submit
      const submitBtn = container.querySelector('#geom-btn-submit');
      const feedback = container.querySelector('#geom-feedback-box');
      if (submitBtn && feedback) {
        submitBtn.addEventListener('click', () => {
          if (selectedIdx === null) {
            alert("Please pick a shape option first!");
            return;
          }

          const chosen = cur.options[selectedIdx];
          feedback.style.display = 'block';

          if (chosen.isCorrect) {
            submitBtn.disabled = true;
            feedback.className = 'geom-feedback-toast correct';
            feedback.innerHTML = `🎉 <strong>CORRECT!</strong> You verified the geometric properties of ${escapeHtml(cur.shapeName)}!`;

            if (callbacks && typeof callbacks.onProgress === 'function') {
              callbacks.onProgress({
                stage: currentRoundIdx + 1,
                totalStages: rounds.length,
                score: Math.round(((currentRoundIdx + 1) / rounds.length) * 100)
              });
            }

            if (currentRoundIdx + 1 < rounds.length) {
              setTimeout(() => {
                currentRoundIdx++;
                selectedIdx = null;
                renderUI();
              }, 1100);
            } else {
              const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
              setTimeout(() => {
                if (callbacks && typeof callbacks.onComplete === 'function') {
                  callbacks.onComplete({
                    score: 100,
                    accuracy: 1.0,
                    time_spent: timeSpent,
                    gameplay_data: {
                      rounds_completed: rounds.length,
                      hints_used: hintsUsed,
                      topic: '2D & 3D Geometry Arena'
                    }
                  });
                }
              }, 1000);
            }
          } else {
            feedback.className = 'geom-feedback-toast almost';
            feedback.innerHTML = `💪 <strong>Think again!</strong> Review the sides, vertices, and right-angle markers!`;
          }
        });
      }
    }

    function escapeHtml(str) {
      if (typeof str !== 'string') return String(str || '');
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    renderUI();

    return {
      destroy: function() {
        container.innerHTML = '';
      }
    };
  }

  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry[PLUGIN_ID] = {
    id: PLUGIN_ID,
    initGame: initGame
  };
  window.TezMindzGameRegistry['geometry_challenge'] = window.TezMindzGameRegistry[PLUGIN_ID];
})();
