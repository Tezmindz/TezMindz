/**
 * Dream House Builder 3D Plugin
 * Standardized TezMindz Game Plugin Contract
 */
(function() {
  const PLUGIN_ID = 'house-builder';

  function initGame(container, gameData, callbacks) {
    const startTime = Date.now();
    let hintsUsed = 0;

    // Load dynamic stages from questions or default house-builder curriculum
    const questions = (gameData && gameData.questions && gameData.questions.length > 0)
      ? gameData.questions
      : null;

    const defaultStages = [
      {
        stageNumber: 1,
        title: "Buy Land & Inspect Deed",
        houseArt: "🏞️",
        prompt: "The prime plot deed is valued at ₹2,50,000. Which option shows this amount written in words?",
        options: [
          { text: "Two Lakh Fifty Thousand", isCorrect: true },
          { text: "Twenty-Five Thousand", isCorrect: false },
          { text: "Two Thousand Five Hundred", isCorrect: false },
          { text: "Twenty-Five Lakh", isCorrect: false }
        ],
        hint: "In Indian number system: 2 is in Lakhs, 50 in Thousands = Two Lakh Fifty Thousand."
      },
      {
        stageNumber: 2,
        title: "Foundation Concrete Mixing",
        houseArt: "🧱",
        prompt: "Foundation requires 45,000 kg of cement. If each truck carries 5,000 kg, how many trucks are needed?",
        options: [
          { text: "9 Trucks", isCorrect: true },
          { text: "8 Trucks", isCorrect: false },
          { text: "10 Trucks", isCorrect: false },
          { text: "7 Trucks", isCorrect: false }
        ],
        hint: "Divide 45,000 by 5,000: 45 ÷ 5 = 9."
      },
      {
        stageNumber: 3,
        title: "Brickwork & Wall Assembly",
        houseArt: "🏠",
        prompt: "Identify the place value of digit '7' in the brick order number: 3,74,250.",
        options: [
          { text: "70,000 (Ten Thousands)", isCorrect: true },
          { text: "7,000 (Thousands)", isCorrect: false },
          { text: "700 (Hundreds)", isCorrect: false },
          { text: "7,00,000 (Lakhs)", isCorrect: false }
        ],
        hint: "Digit positions from right: 0 (Ones), 5 (Tens), 2 (Hundreds), 4 (Thousands), 7 (Ten Thousands)."
      },
      {
        stageNumber: 4,
        title: "Roofing & Painting",
        houseArt: "🏡",
        prompt: "Which paint estimate is the lowest cost: ₹18,400, ₹18,040, ₹18,440, or ₹18,004?",
        options: [
          { text: "₹18,004", isCorrect: true },
          { text: "₹18,040", isCorrect: false },
          { text: "₹18,400", isCorrect: false },
          { text: "₹18,440", isCorrect: false }
        ],
        hint: "Compare digits starting from the hundreds place: 0 is less than 4."
      },
      {
        stageNumber: 5,
        title: "Final Architectural Sign-off",
        houseArt: "🏰",
        prompt: "Total house budget was ₹5,00,000. Total expenses came to ₹4,85,000. How much budget remains?",
        options: [
          { text: "₹15,000 Savings", isCorrect: true },
          { text: "₹25,000 Savings", isCorrect: false },
          { text: "₹10,000 Savings", isCorrect: false },
          { text: "₹50,000 Savings", isCorrect: false }
        ],
        hint: "Subtract ₹4,85,000 from ₹5,00,000 = ₹15,000."
      }
    ];

    let stages = defaultStages;
    if (questions) {
      stages = questions.map((q, idx) => {
        const d = q.data || {};
        const rawOpts = d.options || ["Option A", "Option B", "Option C", "Option D"];
        const correct = String(q.correct_answer || rawOpts[0]);
        return {
          stageNumber: idx + 1,
          title: q.prompt ? `Stage ${idx + 1}` : (defaultStages[idx] ? defaultStages[idx].title : `Stage ${idx + 1}`),
          houseArt: defaultStages[idx] ? defaultStages[idx].houseArt : "🏠",
          prompt: q.prompt || (defaultStages[idx] ? defaultStages[idx].prompt : `Question ${idx + 1}`),
          options: rawOpts.map(opt => ({
            text: typeof opt === 'string' ? opt : (opt.text || String(opt)),
            isCorrect: (typeof opt === 'string' ? opt : (opt.text || String(opt))) === correct
          })),
          hint: (q.hints && q.hints[0]) || (defaultStages[idx] ? defaultStages[idx].hint : "Review the question carefully.")
        };
      });
    }

    let currentStageIdx = 0;
    let selectedOptionIdx = null;

    function renderUI() {
      const cur = stages[currentStageIdx];
      container.innerHTML = `
        <div class="house-builder-wrapper">
          <div class="hb-header-hud">
            <div>
              <span class="hb-stage-badge">Level ${cur.stageNumber} / ${stages.length}</span>
              <strong style="margin-left: 10px; font-size: 1.05rem;">${cur.title}</strong>
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8;">
              🏗️ Dream House Architect
            </div>
          </div>

          <div class="hb-house-progress-canvas">
            <div class="hb-house-art" id="hb-art">${cur.houseArt}</div>
          </div>

          <div class="hb-workstation-panel">
            <div class="hb-prompt-title">${cur.prompt}</div>

            <div class="hb-options-grid">
              ${cur.options.map((opt, idx) => `
                <div class="hb-option-tile ${selectedOptionIdx === idx ? 'selected' : ''}" data-idx="${idx}">
                  <span style="font-weight: 800; color: #818CF8;">${String.fromCharCode(65 + idx)}.</span>
                  <span style="font-weight: 700; color: #FFFFFF;">${opt.text}</span>
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

            <div id="hb-hint-card" style="display:none; margin-top:14px; background:rgba(251,191,36,0.1); border:1px solid #F59E0B; padding:12px; border-radius:12px; color:#FDE68A;"></div>
            <div id="hb-feedback" class="hb-feedback-banner"></div>
          </div>
        </div>
      `;

      attachEventListeners();
    }

    function attachEventListeners() {
      const cur = stages[currentStageIdx];

      container.querySelectorAll('.hb-option-tile').forEach(el => {
        el.addEventListener('click', () => {
          selectedOptionIdx = parseInt(el.getAttribute('data-idx'), 10);
          renderUI();
        });
      });

      const hintBtn = container.querySelector('#hb-btn-hint');
      const hintCard = container.querySelector('#hb-hint-card');
      if (hintBtn && hintCard) {
        hintBtn.addEventListener('click', () => {
          hintsUsed++;
          hintCard.style.display = 'block';
          hintCard.innerHTML = `<strong>Architect Hint:</strong> ${cur.hint}`;
        });
      }

      const submitBtn = container.querySelector('#hb-btn-confirm');
      const feedback = container.querySelector('#hb-feedback');
      if (submitBtn && feedback) {
        submitBtn.addEventListener('click', () => {
          if (selectedOptionIdx === null) {
            alert("Please select a construction decision first!");
            return;
          }

          const chosen = cur.options[selectedOptionIdx];
          feedback.style.display = 'block';

          if (chosen.isCorrect) {
            submitBtn.disabled = true;
            feedback.className = 'hb-feedback-banner correct';
            feedback.innerHTML = `🎉 <strong>STAGE MASTERED!</strong> Construction approved!`;

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
                      house_grade: 'Masterpiece'
                    }
                  });
                }
              }, 1000);
            }
          } else {
            feedback.className = 'hb-feedback-banner almost';
            feedback.innerHTML = `💪 <strong>Safety Notice!</strong> That specification doesn't match the architectural blueprint. Review the figures and try again!`;
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
  window.TezMindzGameRegistry['house_builder'] = window.TezMindzGameRegistry[PLUGIN_ID];
})();
