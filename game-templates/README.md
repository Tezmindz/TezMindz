# TezMindz Modular Olympiad Game Templates

This directory contains standalone, 100% data-driven Olympiad game templates adhering to the standardized structure:

```
<game-slug>/
├── game.manifest.json  # Game metadata, slug, version, inputSchema & sampleData
├── index.js            # Main entry point; receives dynamic JSON data from backend
├── styles.css          # Scoped, conflict-free game styling (.tm-game-*)
├── assets/
│   ├── images/         # Game-specific image assets & SVG icons
│   ├── sounds/         # Game-specific audio cues
│   └── fonts/          # Custom typography
└── components/         # Modular game subcomponents
    └── *.js
```

---

## All 8 Game Templates in this Package

| Template Slug | Game Name | Category | Primary Mechanics |
| :--- | :--- | :--- | :--- |
| `clock-mission` | Clock Mission | Everyday Mathematics | Analog clock hands, elapsed time, angles |
| `number-detective` | Number Detective | Logical Reasoning | Place value clues, divisibility, elimination |
| `pattern-machine` | Pattern Machine | Logical Reasoning | Geometric progressions, gear sequences |
| `balance-scale` | Balance Scale | Mathematical Reasoning | Algebraic balance equations, unknown variables |
| `fraction-lab` | Fraction Lab | Mathematical Reasoning | Shaded pizzas, fraction strips, ratios |
| `geometry-explorer`| Geometry Explorer | Mathematical Reasoning | Polygon perimeter, area, dimensions, symmetry |
| `money-market` | Money Market | Everyday Mathematics | Currency notes & coins, bills, change calculation |
| `data-detective` | Data Detective | Everyday Mathematics | Bar charts, frequency tally marks, data analysis |

---

## Key Architecture Principles

1. **Strictly Data-Driven**:
   Games never hardcode questions or answers. Every question prompt, manipulative state (clock times, balance scale items, fraction slices, data charts), options, hints, and step-by-step explanations are received dynamically via JSON payloads from your backend.

2. **Standard Entry Point (`index.js`)**:
   Every game template exports:
   ```javascript
   export function initGame(containerElement, dataJSON, configOptions) { ... }
   ```
   and sets a global browser fallback `window.TezMindz.<GameSlug>.initGame`.

3. **Backend Communication & Callbacks**:
   Host applications / backends pass lifecycle callbacks in `configOptions`:
   - `onAnswer({ questionId, selectedAnswer, correctAnswer, isCorrect })`
   - `onComplete({ score, stars, timeSpent })`
   - `onHint({ questionId })`

4. **Dynamic Data Hot-Swapping**:
   Games support instant data updates without unmounting:
   ```javascript
   const game = initGame('#game-container', question1JSON);
   // When user advances to next question:
   game.updateData(question2JSON);
   ```

---

## Embedding Example in Any Web Application

```html
<!-- 1. Include Game Scoped CSS -->
<link rel="stylesheet" href="./game-templates/clock-mission/styles.css">

<!-- 2. Target Container -->
<div id="math-game-root"></div>

<!-- 3. Instantiate Game with Backend JSON -->
<script type="module">
  import { initGame } from './game-templates/clock-mission/index.js';

  const questionPayload = {
    questionId: "clk-101",
    prompt: "An Olympiad exam starts at 10:15 AM and lasts 90 minutes. What time does it end?",
    initialTime: { hours: 10, minutes: 15 },
    options: ["11:30 AM", "11:45 AM", "12:00 PM", "12:15 PM"],
    correctAnswer: "11:45 AM",
    explanation: "10:15 AM + 60 mins = 11:15 AM. 11:15 AM + 30 mins = 11:45 AM.",
    hint: "Add 1 hour first, then add the remaining 30 minutes."
  };

  const game = initGame('#math-game-root', questionPayload, {
    soundEnabled: true,
    onAnswer: (result) => {
      console.log('Player answered:', result);
      // fetch('/api/submit-answer', { method: 'POST', body: JSON.stringify(result) });
    }
  });
</script>
```
