/**
 * CashRegister Component
 * Ported from reference MoneyShop.tsx
 * Features:
 * - Interactive shopping item quantity steppers (+ / -)
 * - Dynamic subtotal and grand total bill calculation
 * - Indian currency cash pad (+₹10, +₹20, +₹50, +₹100, +₹500)
 * - Dynamic change-due calculation
 * - Reset cart button
 */
export class CashRegister {
  constructor(options = {}) {
    const rawItems = options.items || [
      { name: "Notebook", price: 45, qty: 4 },
      { name: "Pen", price: 15, qty: 6 }
    ];
    this.initialItems = rawItems.map(i => ({
      name: i.name || 'Item',
      price: i.price !== undefined ? i.price : 20,
      qty: (i.qty !== undefined ? i.qty : (i.quantity !== undefined ? i.quantity : 1))
    }));
    this.items = JSON.parse(JSON.stringify(this.initialItems));
    this.currencySymbol = options.currencySymbol || '₹';
    this.cashTendered = options.amountPaid || 0;
    this.onChange = options.onChange || (() => {});
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-cash-register-wrapper';
    this.renderInternal();
    parentElement.appendChild(this.container);
  }

  updateQty(index, delta) {
    this.items[index].qty = Math.max(0, this.items[index].qty + delta);
    this.renderInternal();
    this.notifyChange();
  }

  addCash(amount) {
    this.cashTendered += amount;
    this.renderInternal();
    this.notifyChange();
  }

  resetShop() {
    this.items = JSON.parse(JSON.stringify(this.initialItems));
    this.cashTendered = 0;
    this.renderInternal();
    this.notifyChange();
  }

  getGrandTotal() {
    return this.items.reduce((sum, item) => sum + item.price * item.qty, 0);
  }

  getBalanceChange() {
    const total = this.getGrandTotal();
    return this.cashTendered >= total ? this.cashTendered - total : 0;
  }

  notifyChange() {
    this.onChange({
      items: this.items,
      grandTotal: this.getGrandTotal(),
      cashTendered: this.cashTendered,
      changeDue: this.getBalanceChange()
    });
  }

  renderInternal() {
    if (!this.container) return;

    const grandTotal = this.getGrandTotal();
    const balanceChange = this.getBalanceChange();

    this.container.innerHTML = `
      <div class="tm-market-card">
        <div class="tm-market-header">
          <div class="tm-market-title">🛍️ Money Shop &amp; Cash Register</div>
          <button type="button" class="btn-market-reset" id="tm-btn-shop-reset" title="Reset cart items">
            🔄 Reset Cart
          </button>
        </div>

        {/* Cart Items List */}
        <div class="tm-cart-list">
          ${this.items.map((item, idx) => `
            <div class="tm-cart-item-row">
              <div class="tm-item-info">
                <span class="tm-item-name">${this.escapeHtml(item.name)}</span>
                <span class="tm-item-rate">${this.currencySymbol}${item.price} each</span>
              </div>

              <div class="tm-item-actions">
                <div class="tm-stepper-box">
                  <button type="button" class="btn-qty btn-minus" data-idx="${idx}">−</button>
                  <span class="tm-qty-count">${item.qty}</span>
                  <button type="button" class="btn-qty btn-plus" data-idx="${idx}">+</button>
                </div>
                <span class="tm-item-subtotal">${this.currencySymbol}${item.price * item.qty}</span>
              </div>
            </div>
          `).join('')}
        </div>

        {/* Grand Total Banner */}
        <div class="tm-bill-banner">
          <div class="tm-bill-label">
            <span>🧾 Total Payable Amount:</span>
          </div>
          <div class="tm-bill-amount" id="tm-bill-grand-total">
            ${this.currencySymbol}${grandTotal}
          </div>
        </div>

        {/* Interactive Indian Currency Cash Pad */}
        <div class="tm-cash-pad-section">
          <span class="tm-cash-pad-title">Customer Cash Given (Tap notes to add):</span>
          <div class="tm-cash-buttons-grid">
            <button type="button" class="btn-cash note-10" data-cash="10">+${this.currencySymbol}10</button>
            <button type="button" class="btn-cash note-20" data-cash="20">+${this.currencySymbol}20</button>
            <button type="button" class="btn-cash note-50" data-cash="50">+${this.currencySymbol}50</button>
            <button type="button" class="btn-cash note-100" data-cash="100">+${this.currencySymbol}100</button>
            <button type="button" class="btn-cash note-500" data-cash="500">+${this.currencySymbol}500</button>
          </div>

          {/* Change readout */}
          <div class="tm-change-summary">
            <div class="tm-change-col">
              <span class="tm-change-label">Cash Received:</span>
              <strong class="tm-val-tendered">${this.currencySymbol}${this.cashTendered}</strong>
            </div>
            <div class="tm-change-col">
              <span class="tm-change-label">Change to Return:</span>
              <strong class="tm-val-change" id="tm-change-due-val">${this.currencySymbol}${balanceChange}</strong>
            </div>
          </div>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const resetBtn = this.container.querySelector('#tm-btn-shop-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetShop());
    }

    this.container.querySelectorAll('.btn-minus').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        this.updateQty(idx, -1);
      });
    });

    this.container.querySelectorAll('.btn-plus').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        this.updateQty(idx, 1);
      });
    });

    this.container.querySelectorAll('.btn-cash').forEach(btn => {
      btn.addEventListener('click', () => {
        const amt = parseInt(btn.getAttribute('data-cash'), 10);
        this.addCash(amt);
      });
    });
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
