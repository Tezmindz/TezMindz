/**
 * Dream House Builder 3D Plugin
 * Ported from reference CubeBuilder.tsx
 * 3D Isometric Cube Tower visualizer with layer isolation, interactive manual counting, and architecture problem solving.
 * Standardized TezMindz Game Plugin Contract
 */
(function() {
  const PLUGIN_ID = 'house-builder';

  function initGame(container, gameData, callbacks) {
    const startTime = Date.now();
    let hintsUsed = 0;

    const questions = (gameData && gameData.questions && gameData.questions.length > 0)
      ? gameData.questions
      : null;

    const defaultStages = [
      {
        stageNumber: 1,
        title: "3D Foundation Cube Counting",
        prompt: "Inspect the 3D tower structure. The base (Floor 1) has 12 cubes, Floor 2 has 8 cubes, and Floor 3 has 4 cubes. What is the total volume in unit cubes?",
        totalExpected: 24,
        layers: [
          { level: 1, count: 12, label: "Bottom Layer (Base)" },
          { level: 2, count: 8, label: "Middle Layer" },
          { level: 3, count: 4, label: "Top Layer" }
        ],
        options: [
          { text: "24 Unit Cubes", isCorrect: true },
          { text: "20 Unit Cubes", isCorrect: false },
          { text: "28 Unit Cubes", isCorrect: false },
          { text: "16 Unit Cubes", isCorrect: false }
        ],
        hint: "Sum the cubes floor-by-floor: 12 + 8 + 4 = 24 unit cubes."
      },
      {
        stageNumber: 2,
        title: "Surface Area & Exposed Faces",
        prompt: "If each unit cube has an edge length of 2 cm, what is the volume of a single unit cube (2 × 2 × 2)?",
        totalExpected: 8,
        layers: [
          { level: 1, count: 4, label: "Lower Tier" },
          { level: 2, count: 4, label: "Upper Tier" }
        ],
        options: [
          { text: "8 cubic cm (cm³)", isCorrect: true },
          { text: "6 cubic cm", isCorrect: false },
          { text: "12 cubic cm", isCorrect: false },
          { text: "16 cubic cm", isCorrect: false }
        ],
        hint: "Volume of a cube = edge × edge × edge = 2 × 2 × 2 = 8 cm³."
      },
      {
        stageNumber: 3,
        title: "Architectural Budget & Place Value",
        prompt: "The total construction budget for the tower is ₹4,75,000. What is the place value of the digit '7' in ₹4,75,000?",
        totalExpected: 70000,
        layers: [
          { level: 1, count: 10, label: "Plinth Level" },
          { level: 2, count: 6, label: "First Tier" },
          { level: 3, count: 2, label: "Spire" }
        ],
        options: [
          { text: "70,000 (Ten Thousands)", isCorrect: true },
          { text: "7,000 (Thousands)", isCorrect: false },
          { text: "700 (Hundreds)", isCorrect: false },
          { text: "7,00,000 (Lakhs)", isCorrect: false }
        ],
        hint: "In 4,75,000: 0 (Ones), 0 (Tens), 0 (Hundreds), 5 (Thousands), 7 (Ten Thousands) = 70,000."
      }
    ];

    let stages = defaultStages;
    if (questions) {
      stages = questions.map((q, idx) => {
        const d = q.data || {};
        const rawOpts = d.options || ["Option A", "Option B", "Option C", "Option D"];
        const correct = String(q.correct_answer || rawOpts[0]);
        const fallback = defaultStages[idx % defaultStages.length];
        return {
          stageNumber: idx + 1,
          title: q.prompt ? `Stage ${idx + 1}` : fallback.title,
          prompt: q.prompt || fallback.prompt,
          totalExpected: d.total_expected || fallback.totalExpected,
          layers: d.layers || fallback.layers,
          options: rawOpts.map(opt => ({
            text: typeof opt === 'string' ? opt : (opt.text || String(opt)),
            isCorrect: (typeof opt === 'string' ? opt : (opt.text || String(opt))) === correct
          })),
          hint: (q.hints && q.hints[0]) || fallback.hint
        };
      });
    }

    let currentStageIdx = 0;
    let selectedOptionIdx = null;
    let activeLayer = 'all';
    let countedCubes = 0;

    function renderIsometricSVG(layers, active) {
      return `
        <svg viewBox="0 0 300 200" class="hb-iso-svg">
          <defs>
            <linearGradient id="cubeTop" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#34d399" />
              <stop offset="100%" stop-color="#10b981" />
            </linearGradient>
            <linearGradient id="cubeLeft" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#059669" />
              <stop offset="100%" stop-color="#047857" />
            </linearGradient>
            <linearGradient id="cubeRight" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#10b981" />
              <stop offset="100%" stop-color="#065f46" />
            </linearGradient>
          </defs>

          <!-- Layer 1 (Base) -->
          <g id="layer-1" opacity="${active === 'all' || active === 1 ? '1' : '0.15'}" style="transition: opacity 0.3s;">
            ${[
              { x: 150, y: 150 },
              { x: 120, y: 135 },
              { x: 180, y: 135 },
              { x: 90, y: 120 },
              { x: 150, y: 120 },
              { x: 210, y: 120 },
            ].map(pos => `
              <g transform="translate(${pos.x - 20}, ${pos.y})">
                <polygon points="20,0 40,10 20,20 0,10" fill="url(#cubeTop)" stroke="#064e3b" stroke-width="1" />
                <polygon points="0,10 20,20 20,40 0,30" fill="url(#cubeLeft)" stroke="#064e3b" stroke-width="1" />
                <polygon points="20,20 40,10 40,30 20,40" fill="url(#cubeRight)" stroke="#064e3b" stroke-width="1" />
              </g>
            `).join('')}
          </g>

          <!-- Layer 2 (Middle) -->
          <g id="layer-2" opacity="${active === 'all' || active === 2 ? '1' : '0.15'}" style="transition: opacity 0.3s;">
            ${[
              { x: 135, y: 110 },
              { x: 165, y: 110 },
              { x: 105, y: 95 },
              { x: 195, y: 95 },
            ].map(pos => `
              <g transform="translate(${pos.x - 20}, ${pos.y})">
                <polygon points="20,0 40,10 20,20 0,10" fill="#38bdf8" stroke="#0369a1" stroke-width="1" />
                <polygon points="0,10 20,20 20,40 0,30" fill="#0284c7" stroke="#0369a1" stroke-width="1" />
                <polygon points="20,20 40,10 40,30 20,40" fill="#075985" stroke="#0369a1" stroke-width="1" />
              </g>
            `).join('')}
          </g>

          <!-- Layer 3 (Top) -->
          <g id="layer-3" opacity="${active === 'all' || active === 3 ? '1' : '0.15'}" style="transition: opacity 0.3s;">
            ${[
              { x: 150, y: 70 },
              { x: 150, y: 40 },
            ].map(pos => `
              <g transform="translate(${pos.x - 20}, ${pos.y})">
                <polygon points="20,0 40,10 20,20 0,10" fill="#facc15" stroke="#a16207" stroke-width="1" />
                <polygon points="0,10 20,20 20,40 0,30" fill="#eab308" stroke="#a16207" stroke-width="1" />
                <polygon points="20,20 40,10 40,30 20,40" fill="#ca8a04" stroke="#a16207" stroke-width="1" />
              </g>
            `).join('')}
          </g>
        </svg>
      `;
    }

    function renderUI() {
      const cur = stages[currentStageIdx];
      container.innerHTML = `
        <div class="house-builder-wrapper">
          <div class="hb-header-hud">
            <div>
              <span class="hb-stage-badge">Stage ${cur.stageNumber} / ${stages.length}</span>
              <strong style="margin-left: 10px; font-size: 1.05rem;">${escapeHtml(cur.title)}</strong>
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8;">
              🏗️ 3D Cube Tower Architect
            </div>
          </div>

          {/* 3D Isometric Tower Stage */}
          <div class="hb-iso-card">
            <div class="hb-iso-header">
              <span class="hb-iso-title">📦 3D Cube Structure (Layer Isolation)</span>
              <button type="button" class="btn-count-reset" id="hb-btn-count-reset">🔄 Reset Count</button>
            </div>

            <div class="hb-iso-canvas">
              ${renderIsometricSVG(cur.layers, activeLayer)}

              <!-- Counter widget -->
              <div class="hb-counter-widget">
                <div class="hb-count-display">
                  Manual Count: <strong id="hb-count-val">${countedCubes}</strong> / ${cur.totalExpected}
                </div>
                <button type="button" class="btn-click-count" id="hb-btn-click-count">
                  + Click to Count
                </button>
              </div>
            </div>

            <!-- Layer isolation selector -->
            <div class="hb-layers-bar">
              <span class="hb-layers-title">Inspect Floor-by-Floor:</span>
              <div class="hb-layers-buttons">
                <button type="button" class="btn-layer ${activeLayer === 'all' ? 'active' : ''}" data-layer="all">All Floors</button>
                ${cur.layers.map(l => `
                  <button type="button" class="btn-layer ${activeLayer === l.level ? 'active' : ''}" data-layer="${l.level}">
                    Floor ${l.level} (${l.count})
                  </button>
                `).join('')}
              </div>
            </div>
          </div>

          {/* Workstation & Question Panel */}
          <div class="hb-workstation-panel">
            <div class="hb-prompt-title">${escapeHtml(cur.prompt)}</div>

            <div class="hb-options-grid">
              ${cur.options.map((opt, idx) => `
                <div class="hb-option-tile ${selectedOptionIdx === idx ? 'selected' : ''}" data-idx="${idx}">
                  <span class="hb-opt-letter">${String.fromCharCode(65 + idx)}.</span>
                  <span class="hb-opt-label">${escapeHtml(opt.text)}</span>
                </div>
              `).join('')}
            </div>

            <div class="hb-action-bar">
              <button type="button" class="btn-hb-hint" id="hb-btn-hint">
                💡 Architect Hint
              </button>
              <button type="button" class="btn-hb-submit" id="hb-btn-confirm">
                <span>🔨 Confirm &amp; Build Stage</span>
              </button>
            </div>

            <div id="hb-hint-card" style="display:none;" class="hb-hint-toast"></div>
            <div id="hb-feedback" class="hb-feedback-banner"></div>
          </div>
        </div>
      `;

      attachEventListeners();
    }

    function attachEventListeners() {
      const cur = stages[currentStageIdx];

      // Layer buttons
      container.querySelectorAll('.btn-layer').forEach(btn => {
        btn.addEventListener('click', () => {
          const l = btn.getAttribute('data-layer');
          activeLayer = l === 'all' ? 'all' : parseInt(l, 10);
          renderUI();
        });
      });

      // Count button
      const countBtn = container.querySelector('#hb-btn-click-count');
      if (countBtn) {
        countBtn.addEventListener('click', () => {
          countedCubes = Math.min(cur.totalExpected, countedCubes + 1);
          const countVal = container.querySelector('#hb-count-val');
          if (countVal) countVal.textContent = countedCubes;
        });
      }

      // Count reset
      const resetCountBtn = container.querySelector('#hb-btn-count-reset');
      if (resetCountBtn) {
        resetCountBtn.addEventListener('click', () => {
          countedCubes = 0;
          const countVal = container.querySelector('#hb-count-val');
          if (countVal) countVal.textContent = countedCubes;
        });
      }

      // Options
      container.querySelectorAll('.hb-option-tile').forEach(el => {
        el.addEventListener('click', () => {
          selectedOptionIdx = parseInt(el.getAttribute('data-idx'), 10);
          renderUI();
        });
      });

      // Hint
      const hintBtn = container.querySelector('#hb-btn-hint');
      const hintCard = container.querySelector('#hb-hint-card');
      if (hintBtn && hintCard) {
        hintBtn.addEventListener('click', () => {
          hintsUsed++;
          hintCard.style.display = 'block';
          hintCard.innerHTML = `<strong>Architect Hint:</strong> ${escapeHtml(cur.hint)}`;
        });
      }

      // Submit
      const submitBtn = container.querySelector('#hb-btn-confirm');
      const feedback = container.querySelector('#hb-feedback');
      if (submitBtn && feedback) {
        submitBtn.addEventListener('click', () => {
          if (selectedOptionIdx === null) {
            alert("Please select an option first!");
            return;
          }

          const chosen = cur.options[selectedOptionIdx];
          feedback.style.display = 'block';

          if (chosen.isCorrect) {
            submitBtn.disabled = true;
            feedback.className = 'hb-feedback-banner correct';
            feedback.innerHTML = `🎉 <strong>STAGE MASTERED!</strong> 3D Cube structure verified!`;

            if (callbacks && typeof callbacks.onProgress === 'function') {
              callbacks.onProgress({
                stage: currentStageIdx + 1,
                totalStages: stages.length,
                score: Math.round(((currentStageIdx + 1) / stages.length) * 100)
              });
            }

            if (currentStageIdx + 1 < stages.length) {
              setTimeout(() => {
                currentStageIdx++;
                selectedOptionIdx = null;
                activeLayer = 'all';
                countedCubes = 0;
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
                      stages_completed: stages.length,
                      hints_used: hintsUsed,
                      house_grade: '3D Masterpiece'
                    }
                  });
                }
              }, 1000);
            }
          } else {
            feedback.className = 'hb-feedback-banner almost';
            feedback.innerHTML = `💪 <strong>Safety Notice!</strong> That specification doesn't match the 3D cube blueprint. Inspect the layers and try again!`;
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
  window.TezMindzGameRegistry['house_builder'] = window.TezMindzGameRegistry[PLUGIN_ID];
})();
