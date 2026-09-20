/**
 * TezMindz Universal Dark / Light Mode Theme Controller (theme-toggle.js)
 * Supports persistent localStorage preference and system color scheme fallback.
 */

(function (global) {
  'use strict';

  function applyTheme(theme) {
    var isDark = theme === 'dark';
    if (isDark) {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.add('dark-theme');
      if (document.body) document.body.classList.add('dark-theme');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.classList.remove('dark-theme');
      if (document.body) document.body.classList.remove('dark-theme');
    }

    // Synchronize all toggle button icons on screen
    var buttons = document.querySelectorAll('.tm-theme-toggle-btn');
    buttons.forEach(function (btn) {
      btn.setAttribute('data-current-theme', isDark ? 'dark' : 'light');
      btn.setAttribute('aria-label', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
      btn.setAttribute('title', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
    });
  }

  function getStoredTheme() {
    var stored = localStorage.getItem('tm_theme');
    if (stored === 'dark' || stored === 'light') return stored;
    return 'light';
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('tm_theme', next);
    applyTheme(next);
  }

  // Initial immediate execution
  var initialTheme = getStoredTheme();
  applyTheme(initialTheme);

  // Auto initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      applyTheme(getStoredTheme());
    });
  } else {
    applyTheme(getStoredTheme());
  }

  // Expose to window
  global.toggleTheme = toggleTheme;
  global.applyTheme = applyTheme;

})(window);
