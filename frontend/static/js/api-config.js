/**
 * TezMindz Centralized API Configuration (api-config.js)
 *
 * Single source of truth for API base URL and endpoints.
 * Compatible with Vanilla JS, Django Templates, and standalone development.
 *
 * Resolution Order:
 * 1. window.TEZMINDZ_API_BASE (explicit JavaScript runtime override)
 * 2. <meta name="api-base-url" content="..."> (injected by Django templates)
 * 3. Same-origin detection:
 *    - Running under Django locally (port 8000) or on Render (*.onrender.com):
 *      Uses window.location.origin so requests are always relative/same-origin.
 * 4. Standalone dev server fallback (e.g. Live Server on port 5500, 3000, etc.):
 *    - Defaults to "http://127.0.0.1:8000".
 * 5. Production standalone fallback:
 *    - Configurable single constant PROD_API_URL.
 */
(function (global) {
  // Production Render Backend URL (single configurable fallback)
  var PROD_API_URL = "https://tezmindz.onrender.com";
  var LOCAL_API_URL = "http://127.0.0.1:8000";

  function determineApiBaseUrl() {
    // 1. Explicit window override
    if (global.TEZMINDZ_API_BASE && typeof global.TEZMINDZ_API_BASE === "string") {
      return global.TEZMINDZ_API_BASE.replace(/\/+$/, "");
    }

    // 2. Meta tag from HTML template
    if (typeof document !== "undefined") {
      var metaEl = document.querySelector('meta[name="api-base-url"]');
      if (metaEl && metaEl.content && metaEl.content.trim()) {
        return metaEl.content.trim().replace(/\/+$/, "");
      }
    }

    // 3. Browser Location Inspection
    if (typeof window !== "undefined" && window.location) {
      var host = window.location.hostname;
      var port = window.location.port;

      // If running through Django directly (same origin):
      // e.g. http://127.0.0.1:8000 or http://localhost:8000
      if ((host === "127.0.0.1" || host === "localhost") && (port === "8000" || port === "")) {
        return window.location.origin;
      }

      // If running on Render (*.onrender.com)
      if (host.endsWith(".onrender.com")) {
        return window.location.origin;
      }

      // If running on a local frontend static dev server (Live Server, VSCode, Vite, etc.)
      if (host === "127.0.0.1" || host === "localhost") {
        return LOCAL_API_URL;
      }
    }

    // 4. Default fallback for production external clients
    return PROD_API_URL;
  }

  var API_BASE = determineApiBaseUrl();

  /**
   * Helper to format an endpoint path with the centralized base URL.
   * If the input path is already an absolute URL (http:// or https://), returns it as-is.
   */
  function apiUrl(path) {
    if (!path) return API_BASE;
    if (path.indexOf("http://") === 0 || path.indexOf("https://") === 0) {
      return path;
    }
    var cleanPath = path.charAt(0) === "/" ? path : "/" + path;
    return API_BASE + cleanPath;
  }

  global.TM_CONFIG = {
    LOCAL_API_URL: LOCAL_API_URL,
    PROD_API_URL: PROD_API_URL,
    API_BASE_URL: API_BASE,
    apiUrl: apiUrl,
  };
})(window);
