/**
 * NumberGrid Component
 * Displays candidate number suspect cards with click-to-select and elimination toggle.
 */
export class NumberGrid {
  constructor(options = {}) {
    this.candidates = options.candidates || [];
    this.onSelect = options.onSelect || (() => {});
    this.container = null;
  }

  render(parentElement) {
    this.container = document.createElement('div');
    this.container.className = 'tm-suspect-grid';

    this.candidates.forEach((num) => {
      const card = document.createElement('div');
      card.className = 'tm-suspect-card';
      card.dataset.value = String(num);

      card.innerHTML = `
        <div class="tm-suspect-stamp">SUSPECT</div>
        <div class="tm-suspect-number">${num}</div>
        <button type="button" class="tm-suspect-pick-btn">Lock In Code</button>
      `;

      card.querySelector('.tm-suspect-pick-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        this.onSelect(String(num), card);
      });

      card.addEventListener('click', () => {
        this.onSelect(String(num), card);
      });

      this.container.appendChild(card);
    });

    parentElement.appendChild(this.container);
  }

  highlightResult(correctAnswer, selectedValue) {
    const cards = this.container.querySelectorAll('.tm-suspect-card');
    cards.forEach((card) => {
      const val = card.dataset.value;
      if (val === String(correctAnswer)) {
        card.classList.add('tm-card-correct');
      } else if (val === String(selectedValue)) {
        card.classList.add('tm-card-wrong');
      } else {
        card.classList.add('tm-card-eliminated');
      }
    });
  }
}
