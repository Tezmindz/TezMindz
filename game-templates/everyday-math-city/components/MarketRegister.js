/**
 * MarketRegister Component
 * Interactive receipt and till register for money shopping problems.
 */
export class MarketRegister {
  constructor(cartItems = [], currency = '₹', paidAmount = 0) {
    this.cartItems = cartItems;
    this.currency = currency;
    this.paidAmount = paidAmount;
  }

  render(container) {
    const wrap = document.createElement('div');
    wrap.className = 'tm-market-register';

    let total = 0;
    const itemsHtml = this.cartItems.map(item => {
      const lineTotal = (item.qty || 1) * (item.unitPrice || 0);
      total += lineTotal;
      return `
        <div class="tm-receipt-row">
          <span class="tm-receipt-name">${item.icon || '📦'} ${this.escapeHtml(item.name)} (x${item.qty})</span>
          <span class="tm-receipt-cost">${this.currency}${lineTotal}</span>
        </div>
      `;
    }).join('');

    wrap.innerHTML = `
      <div class="tm-receipt-card">
        <div class="tm-receipt-header">🧾 Everyday Math Supermarket</div>
        <div class="tm-receipt-body">
          ${itemsHtml || '<div class="tm-empty-cart">No items in register</div>'}
        </div>
        <div class="tm-receipt-divider"></div>
        <div class="tm-receipt-total">
          <span>Total Bill:</span>
          <strong>${this.currency}${total}</strong>
        </div>
        ${this.paidAmount ? `
          <div class="tm-receipt-paid">
            <span>Cash Tendered:</span>
            <span>${this.currency}${this.paidAmount}</span>
          </div>
        ` : ''}
      </div>
    `;

    container.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
