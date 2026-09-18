/**
 * CashRegister Component
 * Renders an itemized shopping invoice and currency notes/coins
 */
export class CashRegister {
  constructor(items = [], amountPaid = 0, currencySymbol = '₹') {
    this.items = items;
    this.amountPaid = amountPaid;
    this.currencySymbol = currencySymbol;
  }

  render(parentElement) {
    const wrap = document.createElement('div');
    wrap.className = 'tm-market-stage';

    const itemsHtml = this.items.map(item => `
      <div class="tm-receipt-row">
        <span>${this.escapeHtml(item.name || 'Item')}</span>
        <span class="tm-receipt-price">${this.currencySymbol}${item.price * (item.quantity || 1)}</span>
      </div>
    `).join('');

    wrap.innerHTML = `
      <div class="tm-receipt-card">
        <div class="tm-receipt-title">🛒 Purchase Receipt</div>
        <div class="tm-receipt-list">
          ${itemsHtml}
        </div>
        <div class="tm-receipt-paid">
          <span>Amount Handed to Cashier:</span>
          <span class="tm-paid-badge">${this.currencySymbol}${this.amountPaid}</span>
        </div>
      </div>
    `;

    parentElement.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
