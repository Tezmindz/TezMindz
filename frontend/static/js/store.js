(function (global) {
  var KEY = "tezmindz_proto_v1";

  var defaults = {
    name: "Aarav",
    age: 11,
    email: "aarav@tezmindz.in",
    classLevel: 5,
    xp: 720,
    xpNext: 1000,
    level: 8,
    coins: 450,
    streak: 7,
    badges: 12,
    fractionsProgress: 80,
    mathProgress: 72,
    scienceProgress: 61,
    englishProgress: 80,
    hintsUsed: 0,
    lastGame: null,
    loggedIn: false,
  };

  function load() {
    if (window.USER_DATA) {
      return Object.assign({}, defaults, window.USER_DATA);
    }
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return Object.assign({}, defaults);
      return Object.assign({}, defaults, JSON.parse(raw));
    } catch (e) {
      return Object.assign({}, defaults);
    }
  }

  function save(state) {
    localStorage.setItem(KEY, JSON.stringify(state));
  }

  var state = load();

  global.TM = {
    get: function () {
      return state;
    },
    set: function (patch) {
      Object.assign(state, patch);
      save(state);
      return state;
    },
    loginDemo: function (extra) {
      state = Object.assign({}, defaults, extra || {}, { loggedIn: true });
      save(state);
      return state;
    },
    requireAuth: function () {
      if (!localStorage.getItem("tm_access")) {
        window.location.href = "/login/";
      }
    },
    greeting: function () {
      var h = new Date().getHours();
      if (h < 12) return "Good morning";
      if (h < 17) return "Good afternoon";
      return "Good evening";
    },
    apiCall: async function (endpoint, options = {}) {
      const targetUrl = (window.TM_CONFIG && window.TM_CONFIG.apiUrl)
        ? window.TM_CONFIG.apiUrl(endpoint)
        : endpoint;
      const access = localStorage.getItem("tm_access");
      const headers = Object.assign({
        "Content-Type": "application/json",
      }, options.headers || {});
      
      if (access) {
        headers["Authorization"] = "Bearer " + access;
      }
      
      const config = Object.assign({}, options, { headers });
      
      let res = await fetch(targetUrl, config);
      
      // If unauthorized, try to refresh
      if (res.status === 401) {
        const refresh = localStorage.getItem("tm_refresh");
        if (refresh) {
          try {
            const refreshUrl = (window.TM_CONFIG && window.TM_CONFIG.apiUrl)
              ? window.TM_CONFIG.apiUrl("/api/auth/jwt/refresh/")
              : "/api/auth/jwt/refresh/";
            const refreshRes = await fetch(refreshUrl, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh })
            });
            
            if (refreshRes.ok) {
              const data = await refreshRes.json();
              localStorage.setItem("tm_access", data.access);
              headers["Authorization"] = "Bearer " + data.access;
              // Retry the original request
              res = await fetch(targetUrl, Object.assign({}, config, { headers }));
            } else {
              // Refresh failed, logout
              localStorage.removeItem("tm_access");
              localStorage.removeItem("tm_refresh");
              window.location.href = "/login/";
            }
          } catch (e) {
            localStorage.removeItem("tm_access");
            localStorage.removeItem("tm_refresh");
            window.location.href = "/login/";
          }
        } else {
          window.location.href = "/login/";
        }
      }
      
      return res;
    }
  };
})(window);
