/**
 * Pizza Fraction Challenge Plugin
 * Fully Interactive SVG Pizza Lab Ported from Reference Implementation
 * Standardized TezMindz Game Plugin Contract
 */
(function() {
  const PLUGIN_ID = 'fraction-pizza';

  function initGame(container, gameData, callbacks) {
    const startTime = Date.now();
    let hintsUsed = 0;

    const questions = (gameData && gameData.questions && gameData.questions.length > 0)
      ? gameData.questions
      : null;
    let currentQuestionIndex = 0;

    const fallbackConfig = (gameData && gameData.config) || {};
    const defaultTotalUnits = fallbackConfig.total_units || 8;
    const defaultTarget = fallbackConfig.target || { num: 3, den: 8 };

    function getActiveQuestion() {
      if (questions && questions[currentQuestionIndex]) {
        const q = questions[currentQuestionIndex];
        const d = q.data || {};
        const den = d.total_units || (d.target && d.target.den) || 8;
        const num = (d.target && d.target.num) !== undefined
          ? d.target.num
          : parseInt(q.correct_answer || '3', 10);
        return {
          id: q.id,
          prompt: q.prompt || `Select exactly ${num}/${den} of the pizza to serve the customer!`,
          totalUnits: den,
          targetNum: num,
          targetDen: den,
          initialSelected: (d.initial_selected !== undefined) ? d.initial_selected : 0,
          hints: q.hints || [
            `The denominator (${den}) indicates the total number of equal slices.`,
            `The numerator (${num}) is the number of slices you need to shade/select.`,
            `Click on individual pizza slices to toggle them on or off.`
          ]
        };
      }

      return {
        id: 'default',
        prompt: `Select exactly ${defaultTarget.num}/${defaultTarget.den} of the pizza to serve the customer!`,
        totalUnits: defaultTotalUnits,
        targetNum: defaultTarget.num,
        targetDen: defaultTarget.den,
        initialSelected: 0,
        hints: [
          `The denominator (${defaultTarget.den}) indicates the total number of equal slices.`,
          `The numerator (${defaultTarget.num}) is the number of slices you need to shade/select.`,
          `Click on individual pizza slices to toggle them on or off.`
        ]
      };
    }

    let activeQ = getActiveQuestion();
    let totalSlices = activeQ.totalUnits;
    let selectedSlices = [];

    // Helper: SVG slice path using polar trigonometry
    function getSlicePath(index, total) {
      const anglePerSlice = (2 * Math.PI) / total;
      const startAngle = index * anglePerSlice - Math.PI / 2;
      const endAngle = (index + 1) * anglePerSlice - Math.PI / 2;
      const r = 90;
      const cx = 100;
      const cy = 100;

      const x1 = cx + r * Math.cos(startAngle);
      const y1 = cy + r * Math.sin(startAngle);
      const x2 = cx + r * Math.cos(endAngle);
      const y2 = cy + r * Math.sin(endAngle);

      const largeArc = anglePerSlice > Math.PI ? 1 : 0;
      return `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`;
    }

    function toggleSlice(index) {
      if (selectedSlices.includes(index)) {
        selectedSlices = selectedSlices.filter(i => i !== index);
      } else {
        selectedSlices.push(index);
      }
      updatePizzaVisual();
      updateReadout();
    }

    function setPreset(count) {
      selectedSlices = Array.from({ length: Math.min(count, totalSlices) }, (_, i) => i);
      updatePizzaVisual();
      updateReadout();
    }

    function resetSlices() {
      selectedSlices = [];
      updatePizzaVisual();
      updateReadout();
    }

    function renderUI() {
      container.innerHTML = `
        <div class="pizza-fraction-wrapper">
          <div class="pizza-mission-banner">
            <h2>🍕 ${escapeHtml(gameData.title || "Interactive Fraction Pizza Lab")}</h2>
            <p>${escapeHtml(activeQ.prompt)}</p>
            <div class="pizza-target-fraction">Target: ${activeQ.targetNum} / ${activeQ.targetDen}</div>
          </div>

          <div class="pizza-interactive-stage">
            {/* Pizza Visual Card */}
            <div class="pizza-display-card">
              <div class="pizza-card-header">
                <span class="pizza-zone-title">🍕 Interactive Pizza (Tap slices to toggle)</span>
                <button type="button" class="btn-pizza-reset" id="pf-btn-reset" title="Reset pizza slices">
                  🔄 Reset
                </button>
              </div>

              <div class="pizza-svg-container">
                <svg viewBox="0 0 200 200" class="pizza-svg" id="pf-svg-pizza">
                  <!-- Crust border -->
                  <circle cx="100" cy="100" r="96" fill="#78350f" stroke="#b45309" stroke-width="4" />
                  <circle cx="100" cy="100" r="90" fill="#fef3c7" />

                  <!-- Slices -->
                  <g id="pf-slices-group">
                    ${Array.from({ length: totalSlices }).map((_, i) => {
                      const isSelected = selectedSlices.includes(i);
                      return `
                        <path
                          d="${getSlicePath(i, totalSlices)}"
                          fill="${isSelected ? '#f59e0b' : '#334155'}"
                          stroke="#1e293b"
                          stroke-width="2"
                          data-slice-index="${i}"
                          class="pizza-slice-path ${isSelected ? 'slice-selected' : ''}"
                        />
                      `;
                    }).join('')}
                  </g>

                  <!-- Center cheese garnish -->
                  <circle cx="100" cy="100" r="9" fill="#d97706" stroke="#92400e" stroke-width="2" />
                </svg>
              </div>

              <div class="pizza-tap-tip">
                💡 <em>Click or tap any slice on the pizza</em> to shade or unshade it!
              </div>
            </div>

            {/* Live Readout & Controls Card */}
            <div class="pizza-control-card">
              <span class="pizza-zone-title">📊 Live Fraction Readout</span>

              <div class="pizza-fraction-display-box">
                <span class="fraction-numerator" id="pf-readout-num">${selectedSlices.length}</span>
                <div class="fraction-divider-bar"></div>
                <span class="fraction-denominator" id="pf-readout-den">${totalSlices}</span>
              </div>

              <div class="pizza-count-breakdown">
                <div class="count-row">
                  <span class="count-label">Selected (Shaded):</span>
                  <strong class="count-value text-amber" id="pf-count-selected">${selectedSlices.length} of ${totalSlices} parts</strong>
                </div>
                <div class="count-row">
                  <span class="count-label">Remaining:</span>
                  <strong class="count-value text-slate" id="pf-count-remaining">${totalSlices - selectedSlices.length} of ${totalSlices} parts</strong>
                </div>
              </div>

              <div class="pizza-presets-section">
                <span class="presets-title">Quick Adjust:</span>
                <div class="presets-buttons">
                  <button type="button" class="btn-preset" data-preset="1">1/${totalSlices}</button>
                  <button type="button" class="btn-preset" data-preset="${Math.floor(totalSlices / 2)}">1/2 (${Math.floor(totalSlices / 2)}/${totalSlices})</button>
                  <button type="button" class="btn-preset" data-preset="${activeQ.targetNum}">Target (${activeQ.targetNum}/${totalSlices})</button>
                  <button type="button" class="btn-preset" data-preset="${totalSlices}">All (${totalSlices}/${totalSlices})</button>
                </div>
              </div>
            </div>
          </div>

          <div class="pizza-action-bar">
            <button type="button" class="btn-pizza-hint" id="pf-btn-hint">
              💡 Chef's Hint (${hintsUsed}/3)
            </button>
            <button type="button" class="btn-pizza-bake" id="pf-btn-bake">
              <span>🔥 Serve to Customer</span>
            </button>
          </div>

          <div id="pf-hint-box" class="pizza-hint-toast" style="display:none;"></div>
          <div id="pf-feedback-box" class="pizza-feedback-toast"></div>
        </div>
      `;

      attachEventListeners();
    }

    function updatePizzaVisual() {
      const paths = container.querySelectorAll('.pizza-slice-path');
      paths.forEach((path) => {
        const idx = parseInt(path.getAttribute('data-slice-index'), 10);
        const isSelected = selectedSlices.includes(idx);
        path.setAttribute('fill', isSelected ? '#f59e0b' : '#334155');
        if (isSelected) {
          path.classList.add('slice-selected');
        } else {
          path.classList.remove('slice-selected');
        }
      });
    }

    function updateReadout() {
      const numEl = container.querySelector('#pf-readout-num');
      const selEl = container.querySelector('#pf-count-selected');
      const remEl = container.querySelector('#pf-count-remaining');
      if (numEl) numEl.textContent = selectedSlices.length;
      if (selEl) selEl.textContent = `${selectedSlices.length} of ${totalSlices} parts`;
      if (remEl) remEl.textContent = `${totalSlices - selectedSlices.length} of ${totalSlices} parts`;
    }

    function attachEventListeners() {
      // Slices click/touch
      const paths = container.querySelectorAll('.pizza-slice-path');
      paths.forEach((path) => {
        path.addEventListener('click', (e) => {
          e.preventDefault();
          const idx = parseInt(path.getAttribute('data-slice-index'), 10);
          toggleSlice(idx);
        });
      });

      // Reset
      const resetBtn = container.querySelector('#pf-btn-reset');
      if (resetBtn) {
        resetBtn.addEventListener('click', resetSlices);
      }

      // Presets
      container.querySelectorAll('.btn-preset').forEach(btn => {
        btn.addEventListener('click', () => {
          const val = parseInt(btn.getAttribute('data-preset'), 10);
          if (!isNaN(val)) setPreset(val);
        });
      });

      // Hint
      const hintBtn = container.querySelector('#pf-btn-hint');
      const hintBox = container.querySelector('#pf-hint-box');
      if (hintBtn && hintBox) {
        hintBtn.addEventListener('click', () => {
          hintsUsed++;
          hintBtn.textContent = `💡 Chef's Hint (${Math.min(hintsUsed, 3)}/3)`;
          hintBox.style.display = 'block';
          const hintText = activeQ.hints[Math.min(hintsUsed - 1, activeQ.hints.length - 1)] || "Count the slices carefully!";
          hintBox.innerHTML = `<strong>Chef's Hint:</strong> ${escapeHtml(hintText)}`;
        });
      }

      // Bake / Serve
      const bakeBtn = container.querySelector('#pf-btn-bake');
      const feedbackBox = container.querySelector('#pf-feedback-box');
      if (bakeBtn && feedbackBox) {
        bakeBtn.addEventListener('click', () => {
          const currentCount = selectedSlices.length;
          feedbackBox.style.display = 'block';

          if (currentCount === activeQ.targetNum) {
            bakeBtn.disabled = true;
            bakeBtn.innerHTML = '<span>✅ Perfect Order Served!</span>';
            feedbackBox.className = 'pizza-feedback-toast correct';
            feedbackBox.innerHTML = `🎉 <strong>DELICIOUS!</strong> You shaded exactly ${currentCount}/${activeQ.targetDen} of the pizza!`;

            const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));

            if (callbacks && typeof callbacks.onProgress === 'function') {
              callbacks.onProgress({
                stage: currentQuestionIndex + 1,
                totalStages: (questions ? questions.length : 1),
                score: 100
              });
            }

            if (questions && currentQuestionIndex + 1 < questions.length) {
              setTimeout(() => {
                currentQuestionIndex++;
                activeQ = getActiveQuestion();
                totalSlices = activeQ.totalUnits;
                selectedSlices = [];
                renderUI();
              }, 1200);
            } else {
              setTimeout(() => {
                if (callbacks && typeof callbacks.onComplete === 'function') {
                  callbacks.onComplete({
                    score: 100,
                    accuracy: 1.0,
                    time_spent: timeSpent,
                    gameplay_data: {
                      slices_placed: currentCount,
                      target_fraction: `${activeQ.targetNum}/${activeQ.targetDen}`,
                      hints_used: hintsUsed
                    }
                  });
                }
              }, 1000);
            }
          } else {
            feedbackBox.className = 'pizza-feedback-toast almost';
            feedbackBox.innerHTML = `💪 <strong>Almost!</strong> You selected ${currentCount}/${activeQ.targetDen} slices, but the customer ordered ${activeQ.targetNum}/${activeQ.targetDen}. Click slices to adjust and try again!`;
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
  window.TezMindzGameRegistry['fraction_pizza'] = window.TezMindzGameRegistry[PLUGIN_ID];
})();
