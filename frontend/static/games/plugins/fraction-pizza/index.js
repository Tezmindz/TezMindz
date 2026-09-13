/**
 * Pizza Fraction Challenge Plugin
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
    const defaultTotalUnits = fallbackConfig.total_units || 4;
    const defaultTarget = fallbackConfig.target || { num: 1, den: 4 };

    function getActiveQuestion() {
      if (questions && questions[currentQuestionIndex]) {
        const q = questions[currentQuestionIndex];
        const d = q.data || {};
        const target = d.target || { num: parseInt(q.correct_answer || '1', 10), den: d.total_units || 4 };
        return {
          id: q.id,
          prompt: q.prompt || `Assemble ${target.num}/${target.den} of the pizza on the serving plate!`,
          totalUnits: d.total_units || 4,
          targetNum: target.num,
          targetDen: target.den || 4,
          hints: q.hints || [
            `Remember: The denominator (${target.den}) shows total equal slices.`,
            `The numerator (${target.num}) shows how many slices need to be placed on the plate.`
          ]
        };
      }

      return {
        id: 'default',
        prompt: `Assemble ${defaultTarget.num}/${defaultTarget.den} of the pizza on the serving plate!`,
        totalUnits: defaultTotalUnits,
        targetNum: defaultTarget.num,
        targetDen: defaultTarget.den,
        hints: [
          `Hint 1: Slices total ${defaultTarget.den}. You need to transfer ${defaultTarget.num} slice(s).`,
          `Hint 2: Click a slice in the Kitchen Tray to move it to the Serving Plate.`
        ]
      };
    }

    let activeQ = getActiveQuestion();
    // state: arrays of slice IDs
    let traySlices = Array.from({ length: activeQ.totalUnits }, (_, i) => i + 1);
    let plateSlices = [];

    function renderUI() {
      container.innerHTML = `
        <div class="pizza-fraction-wrapper">
          <div class="pizza-mission-banner">
            <h2>🍕 ${gameData.title || "Pizza Fraction Challenge"}</h2>
            <p>${activeQ.prompt}</p>
            <div class="pizza-target-fraction">Target: ${activeQ.targetNum} / ${activeQ.targetDen}</div>
          </div>

          <div class="pizza-kitchen-stage">
            <div class="pizza-zone-card">
              <div class="pizza-zone-title">👨‍🍳 Kitchen Prep Tray (${traySlices.length} slices left)</div>
              <div class="pizza-slices-holder" id="pf-tray-holder">
                ${traySlices.map(id => `
                  <div class="pizza-slice-item" data-slice-id="${id}" title="Click to move to plate">
                    <span class="pizza-slice-icon">🍕</span>
                    <span class="pizza-slice-sub">1/${activeQ.targetDen}</span>
                  </div>
                `).join('')}
                ${traySlices.length === 0 ? '<div style="color:#94A3B8; font-style:italic; margin-top:20px;">All slices moved to plate!</div>' : ''}
              </div>
            </div>

            <div class="pizza-zone-card">
              <div class="pizza-zone-title">🍽️ Customer Serving Plate (<span id="pf-plate-fraction">${plateSlices.length}/${activeQ.targetDen}</span>)</div>
              <div class="pizza-plate-circle" id="pf-plate-circle">
                <div class="pizza-slices-holder" style="gap:6px;">
                  ${plateSlices.map(id => `
                    <div class="pizza-slice-item" data-slice-id="${id}" title="Click to return to tray" style="width:52px;height:52px;">
                      <span class="pizza-slice-icon" style="font-size:1.3rem;">🍕</span>
                    </div>
                  `).join('')}
                  ${plateSlices.length === 0 ? '<span style="color:#94A3B8; font-size:0.85rem;">Tap slices to place here</span>' : ''}
                </div>
              </div>
              <div style="font-size:0.75rem; color:#64748B; margin-top:12px;">(Click any placed slice to return it to the tray)</div>
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

          <div id="pf-hint-box" style="display:none; margin-top:14px; background:#EFF6FF; border:1.5px solid #BFDBFE; color:#1E40AF; padding:12px 16px; border-radius:12px; font-size:0.9rem;"></div>
          <div id="pf-feedback-box" class="pizza-feedback-toast"></div>
        </div>
      `;

      attachEventListeners();
    }

    function attachEventListeners() {
      // Move from tray to plate
      container.querySelectorAll('#pf-tray-holder .pizza-slice-item').forEach(el => {
        el.addEventListener('click', () => {
          const id = parseInt(el.getAttribute('data-slice-id'), 10);
          traySlices = traySlices.filter(x => x !== id);
          plateSlices.push(id);
          renderUI();
        });
      });

      // Move from plate to tray
      container.querySelectorAll('#pf-plate-circle .pizza-slice-item').forEach(el => {
        el.addEventListener('click', () => {
          const id = parseInt(el.getAttribute('data-slice-id'), 10);
          plateSlices = plateSlices.filter(x => x !== id);
          traySlices.push(id);
          renderUI();
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
          hintBox.innerHTML = `<strong>Chef's Hint:</strong> ${hintText}`;
        });
      }

      // Bake / Submit
      const bakeBtn = container.querySelector('#pf-btn-bake');
      const feedbackBox = container.querySelector('#pf-feedback-box');
      if (bakeBtn && feedbackBox) {
        bakeBtn.addEventListener('click', () => {
          const currentCount = plateSlices.length;
          feedbackBox.style.display = 'block';

          if (currentCount === activeQ.targetNum) {
            bakeBtn.disabled = true;
            bakeBtn.innerHTML = '<span>✅ Perfect Order Served!</span>';
            feedbackBox.className = 'pizza-feedback-toast correct';
            feedbackBox.innerHTML = `🎉 <strong>DELICIOUS!</strong> You served exactly ${currentCount}/${activeQ.targetDen} of the pizza!`;

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
                traySlices = Array.from({ length: activeQ.totalUnits }, (_, i) => i + 1);
                plateSlices = [];
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
            feedbackBox.innerHTML = `💪 <strong>Almost!</strong> You have placed ${currentCount}/${activeQ.targetDen} slices, but the customer ordered ${activeQ.targetNum}/${activeQ.targetDen}. Adjust the slices and try again!`;
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
  window.TezMindzGameRegistry['fraction_pizza'] = window.TezMindzGameRegistry[PLUGIN_ID];
})();
