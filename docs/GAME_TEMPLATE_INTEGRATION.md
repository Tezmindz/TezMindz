# TezMindz — Game Template Plugin Architecture & Integration Guide

This guide describes how to build, integrate, and configure plug-and-play game templates for the TezMindz learning platform. 

---

## 1. Architectural Philosophy

TezMindz follows an **inversion-of-control, zero-core-modification plugin architecture**:
- **Game developers NEVER need to edit**:
  - Core routing (`urls.py`, frontend routes)
  - Core views (`views.py`)
  - Core database models
  - Authentication or session handling
  - Central registries
- **A new game template is added simply by dropping a folder into**:
  ```
  frontend/static/games/plugins/<game_slug>/
  ```
- **The platform handles**:
  - Auto-discovery of the plugin manifest (`game.manifest.json`)
  - Dynamic registration in Admin console dropdowns
  - Universal HUD, timer, breadcrumb, and scoring shell (`game_shell.html`)
  - Authoritative, anti-cheat validation and ledger reward distribution (XP & Coins)
  - Seamless propagation across the canonical curriculum mapping:
    $$\text{Grade} \to \text{Subject} \to \text{Topic (Chapter)} \to \text{Concept} \to \text{Game} \to \text{Student UI}$$

---

## 2. Directory Structure

Every game plugin lives inside its own self-contained directory under `frontend/static/games/plugins/<game_slug>/`:

```
frontend/static/games/plugins/<game_slug>/
├── game.manifest.json   # Plugin metadata, supported difficulties, schema
├── index.js             # Standardized entrypoint exposing initGame(...)
└── styles.css           # (Optional) Scoped styling for the game viewport
```

### Example Plugins in Repository:
1. `house-builder/` — Dream House Builder 3D (place value & applied estimation)
2. `number-train/` — Number Train Adventure (Indian number system place-value compartments)
3. `fraction-pizza/` — Pizza Fraction Challenge (visual fraction builder & plate serving)
4. `geometry-challenge/` — Geometry & Shapes Arena (2D/3D polygons, perimeters, symmetry)

---

## 3. `game.manifest.json` Specification

The manifest describes the plugin's capabilities, author, and default configuration:

```json
{
  "id": "geometry-challenge",
  "name": "Geometry & Shapes Arena",
  "version": "1.0.0",
  "description": "Interactive polygon, perimeter, and symmetry exploration challenge.",
  "author": "TezMindz Dev Team",
  "entrypoint": "index.js",
  "styles": "styles.css",
  "category": "geometry",
  "supported_difficulties": ["easy", "medium", "hard"],
  "content_types_supported": ["shape_identify", "perimeter_calc", "symmetry_detect"],
  "default_config": {
    "total_rounds": 3,
    "theme": "geometry_arena"
  }
}
```

---

## 4. Standard Lifecycle Contract

Every plugin must register itself in `window.TezMindzGameRegistry` and implement `initGame`:

```javascript
/**
 * Standard Plugin Entrypoint
 * @param {HTMLElement} container - The DOM element where the game UI/canvas mounts.
 * @param {Object} gameData - Configuration and dynamic content payload.
 * @param {Object} callbacks - Standardized event hooks provided by the Game Shell.
 * @returns {Object} Plugin instance with a destroy() method for cleanup.
 */
function initGame(container, gameData, callbacks) {
  // 1. Mount your UI into container
  // 2. Read dynamic questions from gameData.questions
  // 3. Trigger callbacks on user actions:
  //    callbacks.onProgress({ stage, totalStages, score })
  //    callbacks.onComplete({ score, accuracy, time_spent, gameplay_data })
  //    callbacks.onError(error)

  return {
    destroy: function() {
      // Clean up event listeners, intervals, Three.js or Pixi contexts
      container.innerHTML = '';
    }
  };
}

// Self-registration
window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
window.TezMindzGameRegistry['<game_slug>'] = {
  id: '<game_slug>',
  initGame: initGame
};
```

### `gameData` Payload Shape
```json
{
  "gameId": 12,
  "title": "Geometry & Shapes Arena",
  "slug": "geometry-challenge",
  "difficulty": "medium",
  "config": {
    "total_rounds": 3
  },
  "questions": [
    {
      "id": 101,
      "order": 1,
      "prompt": "Identify the shape with 3 sides and one 90° right angle.",
      "content_type": "shape_identify",
      "data": {
        "options": ["Right-Angled Triangle", "Circle", "Pentagon", "Hexagon"]
      },
      "points": 100,
      "hints": ["Count the sides and check the 90-degree corner."]
    }
  ],
  "student": {
    "name": "Aarav Sharma",
    "grade": "5"
  }
}
```

### Standard Callbacks
- **`callbacks.onProgress({ stage, totalStages, score })`**:
  Updates the Universal Game Shell's top HUD (stage badge and score pill).
- **`callbacks.onComplete({ score, accuracy, time_spent, gameplay_data })`**:
  Invoked when the player finishes all stages/levels. Triggers the secure backend submission.
- **`callbacks.onError(error)`**:
  Displays non-blocking user feedback in the Game Shell.

---

## 5. Security & Anti-Cheat: Authoritative Reward Granting

> [!IMPORTANT]
> **Client code is NEVER allowed to mutate or award XP or Coins directly.**

1. The client only reports performance metrics:
   ```json
   {
     "game_id": 12,
     "score": 100,
     "accuracy": 1.0,
     "time_spent": 42,
     "gameplay_data": { "stages_completed": 3 }
   }
   ```
2. The request is authenticated via Django session cookie or JWT and submitted to:
   ```http
   POST /api/game/submit/
   ```
3. The backend calculates rewards, records the transaction in `XPTransaction` (ledger), updates `StudentProfile`, increments attempts/best score in `TopicProgress`, and responds with authoritative totals:
   ```json
   {
     "success": true,
     "is_correct": true,
     "current_score": 100,
     "xp_awarded": 15,
     "coins_awarded": 5,
     "total_xp": 340
   }
   ```
4. The Game Shell renders the verified celebration modal with confetti and earned badges.

---

## 6. Dynamic Content via `GameContent` Model

To support rich multi-question games or teacher-configured questions without modifying code:
- Administrators add `GameContent` inline items under `Game` in Django Admin.
- Fields available:
  - `prompt`: Question or mission description.
  - `content_type`: String key identifying question format (e.g., `shape_identify`, `drag_slots`, `laser_scanner`).
  - `data`: Extensible JSON object containing options, layouts, or assets.
  - `correct_answer`: Authoritative answer for verification.
  - `points`: Marks awarded for this specific stage.
  - `hints`: Array of string hints.
  - `order`: Stage ordering.

---

## 7. Admin Dependent Selectors & Canonical Mapping

The canonical curriculum mapping is preserved end-to-end:
$$\text{Grade} \to \text{Subject} \to \text{Topic (Chapter)} \to \text{Concept} \to \text{Game} \to \text{Student UI}$$

### Admin Cascading Selectors:
- In `ConceptAdmin`:
  1. Select **Grade** (e.g. Class 5).
  2. **Subject** dropdown automatically filters to subjects taught in Class 5.
  3. **Chapter** dropdown automatically filters to chapters in that Grade & Subject.
- In `GameAdmin`:
  1. Select **Grade** $\to$ **Subject** $\to$ **Chapter** $\to$ **Concept**.
  2. Select **Game Template / Plugin** from auto-discovered choices.
  3. Enter title, difficulty, and optional stage content.
- **Server-Side Validation**:
  Both `ConceptAdminForm.clean()` and `GameAdminForm.clean()` strictly reject any mismatched or tampered IDs.
- **Edit Pre-population**:
  Editing an existing Game or Concept automatically resolves and pre-selects the full upstream hierarchy.

---

## 8. 5-Minute Tutorial: Adding a New Game Template

1. **Create the folder**:
   ```powershell
   mkdir frontend/static/games/plugins/space-runner
   ```
2. **Add `game.manifest.json`**:
   ```json
   {
     "id": "space-runner",
     "name": "Space Math Runner",
     "version": "1.0.0",
     "entrypoint": "index.js",
     "styles": "styles.css"
   }
   ```
3. **Add `styles.css` and `index.js`**:
   ```javascript
   (function() {
     function initGame(container, gameData, callbacks) {
       container.innerHTML = `
         <div style="text-align:center; padding: 40px;">
           <h2>🚀 Space Math Runner</h2>
           <button id="btn-win" style="padding:12px 24px; font-size:1.2rem; cursor:pointer;">Complete Mission</button>
         </div>
       `;
       container.querySelector('#btn-win').addEventListener('click', () => {
         callbacks.onComplete({ score: 100, accuracy: 1.0, time_spent: 10 });
       });
       return { destroy: () => { container.innerHTML = ''; } };
     }
     window.TezMindzGameRegistry = window.TezMindzGameRegistry || {};
     window.TezMindzGameRegistry['space-runner'] = { id: 'space-runner', initGame };
   })();
   ```
4. **Link in Admin**:
   - Open Django Admin $\to$ **Games** $\to$ **Add Game**.
   - Pick Grade $\to$ Subject $\to$ Chapter $\to$ Concept.
   - Choose **Space Math Runner (space-runner)** from the dropdown.
   - Click **Save**.
5. **Play as Student**:
   - Navigate to the Concept in the Student UI.
   - The game immediately launches in the Universal Game Shell!
