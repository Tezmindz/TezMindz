/**
 * Geometry & Shapes Arena Plugin
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
        shapeEmoji: "📐",
        shapeName: "Right-Angled Triangle",
        prompt: "Identify the shape that has 3 straight sides and exactly one 90° right angle.",
        options: [
          { text: "Right-Angled Triangle", isCorrect: true },
          { text: "Equilateral Triangle", isCorrect: false },
          { text: "Rectangle", isCorrect: false },
          { text: "Trapezium", isCorrect: false }
        ],
        hint: "Count the sides: 3 sides make a triangle, and look for the square 90-degree corner!"
      },
      {
        shapeEmoji: "🔷",
        shapeName: "Regular Hexagon",
        prompt: "A honeycomb cell has 6 equal straight edges and 6 equal vertices. What polygon is this?",
        options: [
          { text: "Hexagon (6 sides)", isCorrect: true },
          { text: "Pentagon (5 sides)", isCorrect: false },
          { text: "Octagon (8 sides)", isCorrect: false },
          { text: "Heptagon (7 sides)", isCorrect: false }
        ],
        hint: "Prefix 'Hexa' means six in Greek."
      },
      {
        shapeEmoji: "📦",
        shapeName: "Cube",
        prompt: "A 3D solid box with 6 identical square faces, 12 edges, and 8 vertices is called a:",
        options: [
          { text: "Cube", isCorrect: true },
          { text: "Cuboid", isCorrect: false },
          { text: "Square Pyramid", isCorrect: false },
          { text: "Cylinder", isCorrect: false }
        ],
        hint: "Think of standard 6-sided rolling game dice!"
      }
    ];

    let rounds = defaultRounds;
    if (questions) {
      rounds = questions.map((q, idx) => {
        const d = q.data || {};
        const rawOpts = d.options || ["Option A", "Option B", "Option C", "Option D"];
        const correct = String(q.correct_answer || rawOpts[0]);
        return {
          shapeEmoji: d.shape_emoji || defaultRounds[idx % defaultRounds.length].shapeEmoji,
          shapeName: d.shape_name || `Shape ${idx + 1}`,
          prompt: q.prompt || `Round ${idx + 1}: Select the matching geometric property`,
          options: rawOpts.map(opt => ({
            text: typeof opt === 'string' ? opt : (opt.text || String(opt)),
            isCorrect: (typeof opt === 'string' ? opt : (opt.text || String(opt))) === correct
          })),
          hint: (q.hints && q.hints[0]) || "Review the polygon attributes carefully."
        };
      });
    }

    let currentRoundIdx = 0;
    let selectedIdx = null;

    function renderUI() {
      const cur = rounds[currentRoundIdx];
      container.innerHTML = `
        <div class="geometry-arena-wrapper">
          <div class="geom-mission-banner">
            <h2>✨ ${gameData.title || "Geometry & Shapes Arena"}</h2>
            <p><strong>Round ${currentRoundIdx + 1} of ${rounds.length}:</strong> ${cur.prompt}</p>
          </div>

          <div class="geom-visual-stage">
            <div class="geom-shape-display">${cur.shapeEmoji}</div>
            <div style="font-weight: 800; color: #475569; font-size: 0.9rem;">Inspect the Geometric Form</div>
          </div>

          <div class="geom-options-grid">
            ${cur.options.map((opt, idx) => `
              <button type="button" class="geom-option-btn ${selectedIdx === idx ? 'selected' : ''}" data-idx="${idx}">
                <span style="font-weight:900; color:#4F46E5;">${String.fromCharCode(65 + idx)}.</span>
                <span>${opt.text}</span>
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

          <div id="geom-hint-box" style="display:none; margin-top:14px; background:#EFF6FF; border:1.5px solid #BFDBFE; color:#1E40AF; padding:12px 16px; border-radius:12px; font-size:0.9rem;"></div>
          <div id="geom-feedback-box" class="geom-feedback-toast"></div>
        </div>
      `;

      attachEventListeners();
    }

    function attachEventListeners() {
      const cur = rounds[currentRoundIdx];

      container.querySelectorAll('.geom-option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          selectedIdx = parseInt(btn.getAttribute('data-idx'), 10);
          renderUI();
        });
      });

      const hintBtn = container.querySelector('#geom-btn-hint');
      const hintBox = container.querySelector('#geom-hint-box');
      if (hintBtn && hintBox) {
        hintBtn.addEventListener('click', () => {
          hintsUsed++;
          hintBox.style.display = 'block';
          hintBox.innerHTML = `<strong>Geometry Hint:</strong> ${cur.hint}`;
        });
      }

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
            feedback.innerHTML = `🎉 <strong>CORRECT!</strong> You identified the correct geometric form!`;

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
                      topic: '2D & 3D Geometry'
                    }
                  });
                }
              }, 1000);
            }
          } else {
            feedback.className = 'geom-feedback-toast almost';
            feedback.innerHTML = `💪 <strong>Think again!</strong> Review the number of sides, edges, and angles!`;
          }
        });
      }
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
