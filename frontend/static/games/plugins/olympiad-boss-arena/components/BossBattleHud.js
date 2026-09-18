/**
 * BossBattleHud Component
 * Renders Boss avatar, health bar, and battle stats.
 */
export class BossBattleHud {
  constructor(bossData = {}) {
    this.bossData = Object.assign({
      bossName: 'Olympiad Titan',
      avatar: '👾',
      maxHp: 100,
      currentHp: 100,
      themeColor: '#e11d48'
    }, bossData);
  }

  render(container) {
    const wrap = document.createElement('div');
    wrap.className = 'tm-boss-hud';

    const hpPercent = Math.max(0, Math.min(100, (this.bossData.currentHp / this.bossData.maxHp) * 100));

    wrap.innerHTML = `
      <div class="tm-boss-card">
        <div class="tm-boss-avatar">${this.bossData.avatar || '👾'}</div>
        <div class="tm-boss-info">
          <div class="tm-boss-name-row">
            <span class="tm-boss-title">${this.escapeHtml(this.bossData.bossName)}</span>
            <span class="tm-boss-hp-text">HP: ${this.bossData.currentHp} / ${this.bossData.maxHp}</span>
          </div>
          <div class="tm-hp-bar-bg">
            <div class="tm-hp-bar-fill" style="width: ${hpPercent}%; background: ${this.bossData.themeColor || '#e11d48'};"></div>
          </div>
        </div>
      </div>
    `;

    container.appendChild(wrap);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
