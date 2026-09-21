/**
 * Number Train Adventure Plugin
 * Standardized TezMindz Game Plugin Contract
 */
(function() {
  const PLUGIN_ID = 'number-train';

  function initGame(container, gameData, callbacks) {
    const startTime = Date.now();
    let hintsUsed = 0;
    
    // Extract dynamic questions from GameContent or game config
    const questions = (gameData && gameData.questions && gameData.questions.length > 0)
      ? gameData.questions
      : null;
    
    let currentQuestionIndex = 0;
    
    // Default fallback question config
    const fallbackConfig = (gameData && gameData.config) || {};
    const defaultTarget = fallbackConfig.target_number || "375420";
    const defaultWords = fallbackConfig.target_words || "Three Lakh Seventy-Five Thousand Four Hundred Twenty";
    const defaultDigits = fallbackConfig.digit_pool || ["3", "7", "5", "4", "2", "0"];

    function getActiveQuestion() {
      if (questions && questions[currentQuestionIndex]) {
        const q = questions[currentQuestionIndex];
        const d = q.data || {};
        return {
          id: q.id,
          prompt: q.prompt || d.target_words || defaultWords,
          targetNumber: String(d.target_number || q.correct_answer || defaultTarget),
          digits: d.digit_pool || String(d.target_number || defaultTarget).split('').sort(() => Math.random() - 0.5),
          hints: q.hints || d.hints || []
        };
      }
      return {
        id: 'default',
        prompt: defaultWords,
        targetNumber: String(defaultTarget),
        digits: defaultDigits,
        hints: [
          "Hint 1: Look at the highest place value compartment first.",
          "Hint 2: In the Indian system, 3 Lakh goes in the leftmost compartment.",
          "Hint 3: 75 Thousand means 7 in Ten-Thousands and 5 in Thousands."
        ]
      };
    }

    let activeQ = getActiveQuestion();
    const compartments = ["Lakhs", "T-Th", "Thousands", "Hundreds", "Tens", "Ones"];
    const slotCount = activeQ.targetNumber.length || 6;
    let placed = new Array(slotCount).fill(null);
    let usedIndices = new Set();

    function renderUI() {
      container.innerHTML = `
        <div class="number-train-game-wrapper">
          <div class="train-mission-banner">
            <h2>🚂 ${gameData.title || "Number Train Adventure"}</h2>
            <p><strong>Goal:</strong> Form the number: <span style="text-decoration: underline;">${activeQ.prompt}</span></p>
          </div>

          <div class="train-visual-track">
            <div class="train-engine-title">🚆 Express Place-Value Engine</div>
            <div class="train-slots-grid" id="nt-slots-grid">
              ${compartments.slice(0, slotCount).map((label, idx) => `
                <div class="train-compartment ${placed[idx] !== null ? 'filled' : ''}" data-slot-idx="${idx}">
                  <span class="compartment-label">${label}</span>
                  <div class="compartment-val">
                    ${placed[idx] !== null 
                      ? `<div class="compartment-digit">${placed[idx]}</div>` 
                      : `<span class="slot-empty-char">_</span>`}
                  </div>
                  <span style="font-size:0.65rem; color:#94A3B8;">Tap to remove</span>
                </div>
              `).join('')}
            </div>
            <div style="margin-top:14px; font-weight:800; color:#334155;">
              Assembled Number: <span id="nt-assembled-display" style="color:#2563EB; letter-spacing:2px; font-size:1.15rem;">${formatLiveNumber(placed)}</span>
            </div>
          </div>

          <div class="train-digit-depot">
            <div class="depot-title">📦 Available Digit Blocks (Tap to place)</div>
            <div class="digits-container" id="nt-digits-container">
              ${activeQ.digits.map((digit, idx) => `
                <button type="button" class="digit-token ${usedIndices.has(idx) ? 'used' : ''}" data-digit-idx="${idx}" ${usedIndices.has(idx) ? 'disabled' : ''}>
                  ${digit}
                </button>
              `).join('')}
            </div>
          </div>

          <div class="train-action-bar">
            <button type="button" class="btn-train-hint" id="nt-btn-hint">
              💡 Need a Hint (${hintsUsed}/3)
            </button>
            <button type="button" class="btn-train-submit" id="nt-btn-submit">
              <span>🚀 Depart Train</span>
            </button>
          </div>

          <div id="nt-hint-box" class="train-hint-card"></div>
          <div id="nt-feedback-box" class="train-feedback-toast"></div>
        </div>
      `;

      attachEventListeners();
    }

    function formatLiveNumber(arr) {
      return arr.map(v => (v !== null ? v : '_')).join(' ');
    }

    function attachEventListeners() {
      // Slot removal
      container.querySelectorAll('.train-compartment').forEach(el => {
        el.addEventListener('click', () => {
          const slotIdx = parseInt(el.getAttribute('data-slot-idx'), 10);
          if (placed[slotIdx] !== null) {
            // Find which digit token index it was
            const digitVal = placed[slotIdx];
            for (let idx of usedIndices) {
              if (activeQ.digits[idx] === digitVal) {
                usedIndices.delete(idx);
                break;
              }
            }
            placed[slotIdx] = null;
            renderUI();
          }
        });
      });

      // Digit selection
      container.querySelectorAll('.digit-token').forEach(el => {
        el.addEventListener('click', () => {
          const digitIdx = parseInt(el.getAttribute('data-digit-idx'), 10);
          if (usedIndices.has(digitIdx)) return;

          const emptySlotIdx = placed.findIndex(v => v === null);
          if (emptySlotIdx === -1) {
            alert("All compartments are filled! Tap a filled compartment to replace a digit.");
            return;
          }

          placed[emptySlotIdx] = activeQ.digits[digitIdx];
          usedIndices.add(digitIdx);
          renderUI();
        });
      });

      // Hint button
      const hintBtn = container.querySelector('#nt-btn-hint');
      const hintBox = container.querySelector('#nt-hint-box');
      if (hintBtn && hintBox) {
        hintBtn.addEventListener('click', () => {
          hintsUsed++;
          hintBtn.textContent = `💡 Need a Hint (${Math.min(hintsUsed, 3)}/3)`;
          hintBox.style.display = 'block';
          const defaultHintList = [
            "Hint 1: Check the highest place value compartment (Lakhs).",
            "Hint 2: Ten-Thousands and Thousands combine to make the thousands period.",
            "Hint 3: Last 3 compartments are Hundreds, Tens, and Ones."
          ];
          const availableHints = (activeQ.hints && activeQ.hints.length > 0) ? activeQ.hints : defaultHintList;
          const hintText = availableHints[Math.min(hintsUsed - 1, availableHints.length - 1)];
          hintBox.innerHTML = `<strong>💡 Hint ${hintsUsed}:</strong> ${hintText}`;
        });
      }

      // Submit button
      const submitBtn = container.querySelector('#nt-btn-submit');
      const feedbackBox = container.querySelector('#nt-feedback-box');
      if (submitBtn && feedbackBox) {
        submitBtn.addEventListener('click', () => {
          const assembled = placed.join('');
          feedbackBox.style.display = 'block';

          if (assembled === activeQ.targetNumber) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>✅ Train Arrived!</span>';
            feedbackBox.className = 'train-feedback-toast correct';
            feedbackBox.innerHTML = `🎉 <strong>EXCELLENT!</strong> ${assembled} is the exact number!`;

            const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));

            // Notify progress
            if (callbacks && typeof callbacks.onProgress === 'function') {
              callbacks.onProgress({
                stage: currentQuestionIndex + 1,
                totalStages: (questions ? questions.length : 1),
                score: 100
              });
            }

            // Check if there are more questions
            if (questions && currentQuestionIndex + 1 < questions.length) {
              setTimeout(() => {
                currentQuestionIndex++;
                activeQ = getActiveQuestion();
                placed = new Array(activeQ.targetNumber.length || 6).fill(null);
                usedIndices.clear();
                renderUI();
              }, 1200);
            } else {
              // Final game completion
              setTimeout(() => {
                if (callbacks && typeof callbacks.onComplete === 'function') {
                  callbacks.onComplete({
                    score: 100,
                    accuracy: 1.0,
                    time_spent: timeSpent,
                    gameplay_data: {
                      hints_used: hintsUsed,
                      final_number: assembled,
                      questions_solved: (questions ? questions.length : 1)
                    }
                  });
                }
              }, 1000);
            }
          } else {
            feedbackBox.className = 'train-feedback-toast almost';
            feedbackBox.innerHTML = `💪 <strong>Almost!</strong> Assembled: ${assembled.replace(/null/g, '_')}. Check the place value positions and try again!`;
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

  // Register in central registry and window
  window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
  window.TezMindzGameRegistry[PLUGIN_ID] = {
    id: PLUGIN_ID,
    initGame: initGame
  };

  // Support alternative slug naming
  window.TezMindzGameRegistry['number_train'] = window.TezMindzGameRegistry[PLUGIN_ID];
  window.TezMindz = window.TezMindz || {};
  window.TezMindz.NumberTrain = { initGame };
})();
