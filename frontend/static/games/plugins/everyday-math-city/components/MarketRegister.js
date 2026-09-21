/**
 * MarketRegister Component
 * Interactive receipt and till register for money shopping problems.
 * Features item quantity adjustments, Indian currency pad, and live change computation.
 */
export class MarketRegister {
  constructor(cartItems = [], currency = '₹', paidAmount = 0, options = {}) {
    const defaultItems = cartItems.length > 0 ? cartItems : [
      { name: "Notebook", unitPrice: 45, qty: 4, icon: "📓" },
      { name: "Pen", unitPrice: 15, qty: 6, icon: "🖊️" }
    ];
    this.initialItems = defaultItems.map(i => ({
      name: i.name || 'Item',
      unitPrice: i.unitPrice !== undefined ? i.unitPrice : (i.price || 20),
      qty: i.qty !== undefined ? i.qty : 1,
      icon: i.icon || '📦'
    }));
    this.cartItems = JSON.parse(JSON.stringify(this.initialItems));
    this.currency = currency;
    this.cashTendered = paidAmount || 0;
    this.container = null;
  }

  render(container) {
    this.container = document.createElement('div');
    this.container.className = 'tm-market-register';
    this.renderInternal();
    container.appendChild(this.container);
  }

  updateQty(index, delta) {
    this.cartItems[index].qty = Math.max(0, this.cartItems[index].qty + delta);
    this.renderInternal();
  }

  addCash(amount) {
    this.cashTendered += amount;
    this.renderInternal();
  }

  resetRegister() {
    this.cartItems = JSON.parse(JSON.stringify(this.initialItems));
    this.cashTendered = 0;
    this.renderInternal();
  }

  getGrandTotal() {
    return this.cartItems.reduce((sum, item) => sum + item.qty * item.unitPrice, 0);
  }

  renderInternal() {
    if (!this.container) return;

    const total = this.getGrandTotal();
    const balanceChange = this.cashTendered >= total ? this.cashTendered - total : 0;

    const itemsHtml = this.cartItems.map((item, idx) => {
      const lineTotal = item.qty * item.unitPrice;
      return `
        <div class="tm-receipt-row" style="display:flex; align-items:center; justify-content:space-between; padding:6px 0; border-bottom:1px dashed #e2e8f0;">
          <div>
            <span style="font-weight:700;">${item.icon} ${this.escapeHtml(item.name)}</span>
            <span style="font-size:0.75rem; color:#64748b; font-family:monospace; margin-left:6px;">${this.currency}${item.unitPrice} ea</span>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <div style="display:flex; align-items:center; background:#f1f5f9; border-radius:6px; border:1px solid #cbd5e1;">
              <button type="button" class="btn-em-qty btn-em-minus" data-idx="${idx}" style="border:none; background:transparent; padding:2px 8px; cursor:pointer; font-weight:bold;">−</button>
              <span style="font-family:monospace; font-weight:800; padding:0 4px;">${item.qty}</span>
              <button type="button" class="btn-em-qty btn-em-plus" data-idx="${idx}" style="border:none; background:transparent; padding:2px 8px; cursor:pointer; font-weight:bold;">+</button>
            </div>
            <strong style="font-family:monospace; color:#0891b2; min-width:50px; text-align:right;">${this.currency}${lineTotal}</strong>
          </div>
        </div>
      `;
    }).join('');

    this.container.innerHTML = `
      <div class="tm-receipt-card" style="background:#ffffff; border:2px solid #06b6d4; border-radius:16px; padding:16px; max-width:480px; margin:0 auto; box-shadow:0 8px 20px rgba(0,0,0,0.06);">
        <div class="tm-receipt-header" style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #e2e8f0; padding-bottom:8px; margin-bottom:8px;">
          <strong style="color:#0e7490; font-size:0.95rem;">🧾 Everyday Math Supermarket</strong>
          <button type="button" id="btn-em-reset" style="background:#f1f5f9; border:1px solid #cbd5e1; border-radius:6px; font-size:0.75rem; padding:3px 8px; cursor:pointer;">🔄 Reset</button>
        </div>
        <div class="tm-receipt-body">
          ${itemsHtml || '<div class="tm-empty-cart">No items in register</div>'}
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#ecfeff; border:1px solid #a5f3fc; border-radius:10px; padding:10px 14px; margin:12px 0;">
          <span style="font-weight:700; color:#155e75;">Total Payable Bill:</span>
          <strong style="font-size:1.3rem; color:#0891b2; font-family:monospace;">${this.currency}${total}</strong>
        </div>

        <!-- Cash pad -->
        <div style="border-top:1px solid #e2e8f0; padding-top:10px;">
          <span style="font-size:0.75rem; color:#64748b; font-weight:700; display:block; margin-bottom:6px;">Add Cash Given:</span>
          <div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:4px; margin-bottom:8px;">
            <button type="button" class="btn-em-cash" data-cash="10" style="background:#fef3c7; border:1px solid #b45309; color:#92400e; padding:4px 0; border-radius:6px; font-weight:bold; font-size:0.75rem; cursor:pointer;">+${this.currency}10</button>
            <button type="button" class="btn-em-cash" data-cash="20" style="background:#fef9c3; border:1px solid #ca8a04; color:#854d0e; padding:4px 0; border-radius:6px; font-weight:bold; font-size:0.75rem; cursor:pointer;">+${this.currency}20</button>
            <button type="button" class="btn-em-cash" data-cash="50" style="background:#cffafe; border:1px solid #0891b2; color:#155e75; padding:4px 0; border-radius:6px; font-weight:bold; font-size:0.75rem; cursor:pointer;">+${this.currency}50</button>
            <button type="button" class="btn-em-cash" data-cash="100" style="background:#e0e7ff; border:1px solid #4f46e5; color:#3730a3; padding:4px 0; border-radius:6px; font-weight:bold; font-size:0.75rem; cursor:pointer;">+${this.currency}100</button>
            <button type="button" class="btn-em-cash" data-cash="500" style="background:#d1fae5; border:1px solid #059669; color:#065f46; padding:4px 0; border-radius:6px; font-weight:bold; font-size:0.75rem; cursor:pointer;">+${this.currency}500</button>
          </div>
          <div style="display:flex; justify-content:space-between; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:0.8rem;">
            <span>Cash Tendered: <strong style="font-family:monospace;">${this.currency}${this.cashTendered}</strong></span>
            <span style="color:#059669;">Change Due: <strong style="font-family:monospace;">${this.currency}${balanceChange}</strong></span>
          </div>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const resetBtn = this.container.querySelector('#btn-em-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetRegister());
    }

    this.container.querySelectorAll('.btn-em-minus').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        this.updateQty(idx, -1);
      });
    });

    this.container.querySelectorAll('.btn-em-plus').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        this.updateQty(idx, 1);
      });
    });

    this.container.querySelectorAll('.btn-em-cash').forEach(btn => {
      btn.addEventListener('click', () => {
        const cash = parseInt(btn.getAttribute('data-cash'), 10);
        this.addCash(cash);
      });
    });
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
