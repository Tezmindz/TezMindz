/**
 * PlaceValueBoard Component
 * Interactive Place Value Explorer ported from TezMindz NumberBuilder.tsx
 * Supports Indian & International numbering systems with dynamic column selection,
 * live face value vs place value calculation, and exponent readouts.
 */
export class PlaceValueBoard {
  constructor(options = {}) {
    if (typeof options === 'string') {
      this.numberStr = options;
      this.highlightDigit = null;
      this.system = 'Indian';
    } else {
      this.numberStr = options.numberStr || options.number || "4,78,32,109";
      this.highlightDigit = options.highlightDigit || options.targetDigit || "7";
      this.system = options.system || "Indian";
      this.digits = options.digits || null;
    }

    // Default Indian system places if full number is not provided
    this.places = this.generatePlaces();
    this.selectedPlace = this.places[1]?.name || this.places[0]?.name;
  }

  generatePlaces() {
    // If digits map provided e.g. { thousands: 4, hundreds: 5, tens: 2, ones: 9 }
    if (this.digits && typeof this.digits === 'object' && !Array.isArray(this.digits)) {
      const colDefs = [
        { name: "Ten Thousands (T-Th)", val: 10000, key: 'tenThousands', fallbackKey: 'ten_thousands' },
        { name: "Thousands (Th)", val: 1000, key: 'thousands' },
        { name: "Hundreds (H)", val: 100, key: 'hundreds' },
        { name: "Tens (T)", val: 10, key: 'tens' },
        { name: "Ones (O)", val: 1, key: 'ones' }
      ];
      const result = [];
      for (const col of colDefs) {
        if (this.digits[col.key] !== undefined || (col.fallbackKey && this.digits[col.fallbackKey] !== undefined)) {
          const d = this.digits[col.key] !== undefined ? this.digits[col.key] : this.digits[col.fallbackKey];
          result.push({
            name: col.name,
            val: col.val,
            digit: String(d)
          });
        }
      }
      if (result.length > 0) return result;
    }

    // Otherwise parse numberStr digits into Indian place values
    const cleanDigits = String(this.numberStr).replace(/\D/g, '');
    const indianColNames = [
      { name: "Crores (C)", val: 10000000 },
      { name: "Ten Lakhs (TL)", val: 1000000 },
      { name: "Lakhs (L)", val: 100000 },
      { name: "Ten Thousands (T-Th)", val: 10000 },
      { name: "Thousands (Th)", val: 1000 },
      { name: "Hundreds (H)", val: 100 },
      { name: "Tens (T)", val: 10 },
      { name: "Ones (O)", val: 1 }
    ];

    if (cleanDigits.length > 0) {
      // align from right (ones) to left
      const paddedCols = [];
      const len = cleanDigits.length;
      for (let i = 0; i < len; i++) {
        const digitChar = cleanDigits[len - 1 - i];
        const colDef = indianColNames[indianColNames.length - 1 - i] || {
          name: `10^${i}`,
          val: Math.pow(10, i)
        };
        paddedCols.unshift({
          name: colDef.name,
          val: colDef.val,
          digit: digitChar
        });
      }
      return paddedCols;
    }

    return [
      { name: "Crores (C)", val: 10000000, digit: "4" },
      { name: "Ten Lakhs (TL)", val: 1000000, digit: "7" },
      { name: "Lakhs (L)", val: 100000, digit: "8" },
      { name: "Ten Thousands (T-Th)", val: 10000, digit: "3" },
      { name: "Thousands (Th)", val: 1000, digit: "2" },
      { name: "Hundreds (H)", val: 100, digit: "1" },
      { name: "Tens (T)", val: 10, digit: "0" },
      { name: "Ones (O)", val: 1, digit: "9" }
    ];
  }

  render(container) {
    this.container = container;
    const board = document.createElement('div');
    board.className = 'tm-pv-explorer-board';

    this.wrapper = board;
    this.updateBoardView();
    container.appendChild(board);
  }

  updateBoardView() {
    if (!this.wrapper) return;

    const activeCol = this.places.find(p => p.name === this.selectedPlace) || this.places[0];
    const activeDigitNum = Number(activeCol?.digit || 0);
    const placeValCalculated = activeDigitNum * (activeCol?.val || 1);

    this.wrapper.innerHTML = `
      <div class="tm-pve-header">
        <div class="tm-pve-title">
          <span class="tm-pve-icon">👑</span>
          <span class="tm-pve-heading">Place Value Explorer (${this.system} System)</span>
        </div>
        <span class="tm-pve-num-badge">${this.numberStr}</span>
      </div>

      <!-- Interactive Strip of Place Value Columns -->
      <div class="tm-pve-strip">
        ${this.places.map((p, idx) => {
          const isSelected = this.selectedPlace === p.name;
          const isTarget = this.highlightDigit && p.digit === String(this.highlightDigit);
          const exponent = Math.round(Math.log10(p.val));

          return `
            <button type="button" class="tm-pve-col-card ${isSelected ? 'is-selected' : ''} ${isTarget ? 'is-target' : ''}" data-col-name="${p.name}">
              <span class="tm-pve-col-label">${p.name.split(' ')[0]}</span>
              <span class="tm-pve-col-digit">${p.digit}</span>
              <span class="tm-pve-col-power">10<sup>${exponent}</sup></span>
            </button>
          `;
        }).join('')}
      </div>

      <!-- Live Inspector Card -->
      <div class="tm-pve-inspector">
        <div class="tm-pve-inspector-left">
          <div class="tm-pve-stat-line">
            <span class="tm-pve-stat-label">Selected Column:</span>
            <strong class="tm-pve-stat-val tm-pve-highlight">${activeCol ? activeCol.name : '-'}</strong>
          </div>
          <div class="tm-pve-stat-line">
            <span class="tm-pve-stat-label">Face Value:</span>
            <strong class="tm-pve-stat-val">${activeDigitNum}</strong>
          </div>
        </div>

        <div class="tm-pve-inspector-right">
          <span class="tm-pve-calc-label">Calculated Place Value:</span>
          <span class="tm-pve-calc-value">${placeValCalculated.toLocaleString('en-IN')}</span>
          <span class="tm-pve-calc-formula">(${activeDigitNum} × ${(activeCol?.val || 1).toLocaleString('en-IN')})</span>
        </div>
      </div>

      <div class="tm-pve-footer-hint">
        <span>💡 Tap any column to inspect how digit weight multiplies face value by powers of 10.</span>
      </div>
    `;

    // Attach click listeners to columns
    this.wrapper.querySelectorAll('.tm-pve-col-card').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const colName = e.currentTarget.getAttribute('data-col-name');
        this.selectedPlace = colName;
        this.updateBoardView();
      });
    });
  }
}
