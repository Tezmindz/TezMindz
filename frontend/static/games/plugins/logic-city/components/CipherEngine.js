/**
 * CipherEngine Component
 * Ported from reference CodeBreaker.tsx
 * Features:
 * - Rotor shift adjuster (+1, +2, -1)
 * - Interactive letter tiles showing letter, shift, and decoded output
 * - Live decoded ribbon
 * - Clue transformation comparison
 */
export class CipherEngine {
  constructor(sequence = [], missingIndex = -1, rules = [], options = {}) {
    this.sequence = sequence;
    this.missingIndex = missingIndex;
    this.rules = rules;

    this.sourceWord = options.sourceWord || (typeof sequence[0] === 'string' && sequence[0].length > 1 ? sequence[0] : "ERASER");
    this.exampleSource = options.exampleSource || (rules[0] ? rules[0].source : "PENCIL");
    this.exampleTarget = options.exampleTarget || (rules[0] ? rules[0].target : "QFODJM");
    this.activeShift = options.shift || 1;
    this.container = null;
  }

  getShiftedChar(char, shift) {
    const code = char.charCodeAt(0);
    if (code >= 65 && code <= 90) {
      let s = code + shift;
      if (s > 90) s = 65 + (s - 91);
      if (s < 65) s = 90 - (64 - s);
      return String.fromCharCode(s);
    }
    return char;
  }

  setShift(shift) {
    this.activeShift = shift;
    this.renderInternal();
  }

  render(container) {
    this.container = document.createElement('div');
    this.container.className = 'tm-cipher-wrapper';
    this.renderInternal();
    container.appendChild(this.container);
  }

  renderInternal() {
    if (!this.container) return;

    const wordChars = this.sourceWord.split('');
    const decodedWord = wordChars.map(c => this.getShiftedChar(c, this.activeShift)).join('');

    this.container.innerHTML = `
      <div class="tm-cipher-machine-card" style="background:#0f172a; border:1.5px solid #6366f1; border-radius:16px; padding:16px; color:#ffffff; margin-bottom:14px; box-shadow:0 8px 24px rgba(0,0,0,0.15);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:8px; margin-bottom:12px;">
          <div style="color:#818cf8; font-weight:800; font-size:0.95rem;">🔑 Code Breaker Cipher Machine</div>
          <span style="font-family:monospace; font-size:0.75rem; background:rgba(99,102,241,0.2); color:#a5b4fc; border:1px solid #6366f1; padding:2px 8px; border-radius:6px;">
            Rotor Shift: +${this.activeShift}
          </span>
        </div>

        <!-- Clue Banner if present -->
        ${this.exampleSource && this.exampleTarget ? `
          <div style="display:flex; justify-content:space-around; align-items:center; background:#1e293b; border-radius:10px; padding:8px 12px; margin-bottom:12px; font-size:0.8rem;">
            <span>Clue: <strong style="color:#fbbf24; font-family:monospace; background:#0f172a; padding:2px 6px; border-radius:4px;">${this.escapeHtml(this.exampleSource)}</strong></span>
            <span style="color:#64748b;">➔</span>
            <span>Becomes: <strong style="color:#34d399; font-family:monospace; background:#0f172a; padding:2px 6px; border-radius:4px;">${this.escapeHtml(this.exampleTarget)}</strong></span>
          </div>
        ` : ''}

        <!-- Interactive Tiles Stage -->
        <div style="background:#020617; border-radius:12px; padding:16px; text-align:center; margin-bottom:12px;">
          <span style="font-size:0.75rem; color:#94a3b8; display:block; margin-bottom:8px;">Word to Decode:</span>
          <div style="display:flex; justify-content:center; gap:6px; flex-wrap:wrap; margin-bottom:14px;">
            ${wordChars.map(letter => `
              <div style="display:flex; flex-direction:column; align-items:center;">
                <div style="width:38px; height:42px; background:#1e293b; border:1px solid #475569; border-radius:8px; display:flex; align-items:center; justify-content:center; font-family:monospace; font-weight:800; font-size:1.1rem; color:#f8fafc;">
                  ${this.escapeHtml(letter)}
                </div>
                <span style="font-size:0.65rem; color:#818cf8; font-family:monospace; margin:2px 0;">+${this.activeShift}</span>
                <div style="width:38px; height:42px; background:rgba(67, 56, 202, 0.5); border:1.5px solid #6366f1; border-radius:8px; display:flex; align-items:center; justify-content:center; font-family:monospace; font-weight:800; font-size:1.1rem; color:#c7d2fe;">
                  ${this.getShiftedChar(letter, this.activeShift)}
                </div>
              </div>
            `).join('')}
          </div>

          <!-- Decoded Output Ribbon -->
          <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(49, 46, 129, 0.6); border:1px solid #6366f1; padding:6px 16px; border-radius:9999px;">
            <span style="font-size:0.8rem; color:#a5b4fc;">Decoded Result:</span>
            <strong style="font-family:monospace; font-size:1.2rem; color:#e0e7ff; letter-spacing:3px;">${decodedWord}</strong>
          </div>
        </div>

        <!-- Shift Adjuster Buttons -->
        <div style="display:flex; justify-content:center; gap:8px; align-items:center; font-size:0.8rem;">
          <span style="color:#94a3b8;">Shift Rule:</span>
          <button type="button" class="btn-cipher-shift ${this.activeShift === 1 ? 'active' : ''}" data-shift="1" style="background:${this.activeShift === 1 ? '#4f46e5' : '#1e293b'}; color:#fff; border:1px solid #6366f1; padding:4px 10px; border-radius:6px; font-weight:bold; cursor:pointer;">
            +1 Next Letter
          </button>
          <button type="button" class="btn-cipher-shift ${this.activeShift === 2 ? 'active' : ''}" data-shift="2" style="background:${this.activeShift === 2 ? '#4f46e5' : '#1e293b'}; color:#fff; border:1px solid #6366f1; padding:4px 10px; border-radius:6px; font-weight:bold; cursor:pointer;">
            +2 Skip Letter
          </button>
          <button type="button" class="btn-cipher-shift ${this.activeShift === -1 ? 'active' : ''}" data-shift="-1" style="background:${this.activeShift === -1 ? '#4f46e5' : '#1e293b'}; color:#fff; border:1px solid #6366f1; padding:4px 10px; border-radius:6px; font-weight:bold; cursor:pointer;">
            -1 Previous Letter
          </button>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    this.container.querySelectorAll('.btn-cipher-shift').forEach(btn => {
      btn.addEventListener('click', () => {
        const s = parseInt(btn.getAttribute('data-shift'), 10);
        this.setShift(s);
      });
    });
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
