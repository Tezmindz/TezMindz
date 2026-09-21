/**
 * TezMindz Centralized Authentication Modal Controller (auth-modal.js)
 *
 * Handles centered popup modals for:
 * - Student Login
 * - Student Registration
 * - Password Reset (OTP flow)
 * - Seamless switching without page refreshes
 * - Subscription Plan selection preservation
 * - Keyboard navigation (Esc to close, Enter to submit)
 * - Outside click backdrop dismissal
 * - Token management & session updates
 */

(function (global) {
  'use strict';

  function getCsrfToken() {
    var hiddenInput = document.getElementById('tmCsrfCarrier');
    if (hiddenInput && hiddenInput.value) return hiddenInput.value;

    // Fallback: Read CSRF cookie
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === 'csrftoken=') {
          cookieValue = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return cookieValue || '';
  }

  function getApiUrl(path) {
    if (global.TM_CONFIG && typeof global.TM_CONFIG.apiUrl === 'function') {
      return global.TM_CONFIG.apiUrl(path);
    }
    return path;
  }

  var TMAuthModal = {
    activeModal: null,
    pendingPlanId: null,

    init: function () {
      var self = this;

      // Check URL query parameters for plan preservation
      var urlParams = new URLSearchParams(window.location.search);
      var planFromUrl = urlParams.get('plan') || urlParams.get('plan_id');
      if (planFromUrl) {
        self.pendingPlanId = planFromUrl;
        localStorage.setItem('tm_pending_plan_id', planFromUrl);
      } else {
        self.pendingPlanId = localStorage.getItem('tm_pending_plan_id');
      }

      var nextParam = urlParams.get('next');
      if (nextParam) {
        localStorage.setItem('tm_auth_next_url', nextParam);
      }

      // Check URL query parameters for auto-opening modal (e.g. ?auth=login, ?auth=register, ?modal=login, ?modal=register)
      var authAction = (urlParams.get('auth') || urlParams.get('modal') || '').toLowerCase();
      if (authAction === 'login') {
        setTimeout(function () { self.openLogin(); }, 120);
      } else if (authAction === 'register') {
        setTimeout(function () { self.openRegister(); }, 120);
      } else if (authAction === 'forgot') {
        setTimeout(function () { self.openForgot(); }, 120);
      }

      // Close on Backdrop Click
      var backdrop = document.getElementById('tmAuthBackdrop');
      if (backdrop) {
        backdrop.addEventListener('click', function (e) {
          if (e.target === backdrop) {
            self.close();
          }
        });
      }

      // Close on Escape Key
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && self.activeModal) {
          self.close();
        }
      });

      // Bind all declarative triggers on the page
      self.bindTriggers();
    },

    bindTriggers: function () {
      var self = this;
      document.querySelectorAll('[data-open-modal]').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          var target = btn.getAttribute('data-open-modal');
          var planId = btn.getAttribute('data-plan-id') || btn.getAttribute('data-plan');
          if (target === 'login') {
            self.openLogin(planId);
          } else if (target === 'register') {
            self.openRegister(planId);
          }
        });
      });
    },

    openLogin: function (planId) {
      if (planId) {
        this.pendingPlanId = planId;
        localStorage.setItem('tm_pending_plan_id', planId);
      }
      this._showModal('tmLoginModal');
      this.clearErrors();
      setTimeout(function () {
        var emailInput = document.getElementById('tmLoginEmail');
        if (emailInput) emailInput.focus();
      }, 100);
    },

    openRegister: function (planId) {
      if (planId) {
        this.pendingPlanId = planId;
        localStorage.setItem('tm_pending_plan_id', planId);
      }

      this._showModal('tmRegisterModal');
      this.clearErrors();
      setTimeout(function () {
        var nameInput = document.getElementById('tmRegFullName');
        if (nameInput) nameInput.focus();
      }, 100);
    },

    openForgot: function () {
      this._showModal('tmForgotModal');
      this.openForgotStep1();
    },

    openForgotStep1: function () {
      var step1 = document.getElementById('tmForgotStep1');
      var step2 = document.getElementById('tmForgotStep2');
      if (step1) step1.style.display = 'block';
      if (step2) step2.style.display = 'none';
      var errBox = document.getElementById('tmForgotError1');
      if (errBox) errBox.style.display = 'none';
      setTimeout(function () {
        var emailInput = document.getElementById('tmForgotEmail');
        if (emailInput) emailInput.focus();
      }, 100);
    },

    openForgotStep2: function () {
      var step1 = document.getElementById('tmForgotStep1');
      var step2 = document.getElementById('tmForgotStep2');
      if (step1) step1.style.display = 'none';
      if (step2) step2.style.display = 'block';
      var errBox = document.getElementById('tmForgotError2');
      if (errBox) errBox.style.display = 'none';
      setTimeout(function () {
        var otpInput = document.getElementById('tmForgotOTP');
        if (otpInput) otpInput.focus();
      }, 100);
    },

    switchToRegister: function () {
      this.openRegister(this.pendingPlanId);
    },

    switchToLogin: function () {
      this.openLogin(this.pendingPlanId);
    },

    _showModal: function (modalId) {
      var backdrop = document.getElementById('tmAuthBackdrop');
      if (!backdrop) return;

      var loginCard = document.getElementById('tmLoginModal');
      var regCard = document.getElementById('tmRegisterModal');
      var forgotCard = document.getElementById('tmForgotModal');

      if (loginCard) loginCard.style.display = 'none';
      if (regCard) regCard.style.display = 'none';
      if (forgotCard) forgotCard.style.display = 'none';

      var targetCard = document.getElementById(modalId);
      if (targetCard) {
        targetCard.style.display = 'block';
        targetCard.classList.remove('tm-modal-enter');
        void targetCard.offsetWidth; // Force reflow
        targetCard.classList.add('tm-modal-enter');
      }

      backdrop.style.display = 'flex';
      backdrop.classList.add('active');
      backdrop.setAttribute('aria-hidden', 'false');
      document.body.classList.add('tm-modal-open');
      this.activeModal = modalId;
    },

    close: function () {
      var backdrop = document.getElementById('tmAuthBackdrop');
      if (backdrop) {
        backdrop.classList.remove('active');
        backdrop.setAttribute('aria-hidden', 'true');
        setTimeout(function () {
          backdrop.style.display = 'none';
          var loginCard = document.getElementById('tmLoginModal');
          var regCard = document.getElementById('tmRegisterModal');
          var forgotCard = document.getElementById('tmForgotModal');
          if (loginCard) loginCard.style.display = 'none';
          if (regCard) regCard.style.display = 'none';
          if (forgotCard) forgotCard.style.display = 'none';
        }, 220);
      }
      document.body.classList.remove('tm-modal-open');
      this.activeModal = null;
      this.clearErrors();
    },

    showError: function (modalType, message) {
      var boxId = modalType === 'register' ? 'tmRegisterError' : 'tmLoginError';
      var msgId = modalType === 'register' ? 'tmRegisterErrorMsg' : 'tmLoginErrorMsg';

      var box = document.getElementById(boxId);
      var msg = document.getElementById(msgId);
      if (box && msg) {
        msg.textContent = message;
        box.style.display = 'flex';
      }
    },

    clearErrors: function () {
      var lBox = document.getElementById('tmLoginError');
      var rBox = document.getElementById('tmRegisterError');
      var fBox1 = document.getElementById('tmForgotError1');
      var fBox2 = document.getElementById('tmForgotError2');

      if (lBox) lBox.style.display = 'none';
      if (rBox) rBox.style.display = 'none';
      if (fBox1) fBox1.style.display = 'none';
      if (fBox2) fBox2.style.display = 'none';
    },

    togglePasswordVisibility: function (inputId, btn) {
      var input = document.getElementById(inputId);
      if (!input) return;

      if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML =
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
          '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>' +
          '<path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path>' +
          '<path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path>' +
          '<line x1="2" y1="2" x2="22" y2="22"></line>' +
          '</svg>';
      } else {
        input.type = 'password';
        btn.innerHTML =
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
          '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>' +
          '<circle cx="12" cy="12" r="3"></circle>' +
          '</svg>';
      }
    },

    handleLogin: function (e) {
      if (e) e.preventDefault();
      var self = this;
      self.clearErrors();

      var email = (document.getElementById('tmLoginEmail').value || '').trim();
      var password = document.getElementById('tmLoginPassword').value || '';

      if (!email) {
        self.showError('login', 'Please enter your email or phone number.');
        return;
      }
      if (!password) {
        self.showError('login', 'Please enter your password.');
        return;
      }

      var btn = document.getElementById('tmLoginBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="tm-auth-spinner"></span> <span>Signing in…</span>';

      var loginUrl = getApiUrl('/login/');
      fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ email: email, password: password })
      })
      .then(function (res) {
        if (res.ok) return res.json();
        return res.json().then(function (err) { throw err; });
      })
      .then(function (data) {
        if (data.success) {
          if (data.access) localStorage.setItem('tm_access', data.access);
          if (data.refresh) localStorage.setItem('tm_refresh', data.refresh);

          var nextUrl = localStorage.getItem('tm_auth_next_url');
          if (nextUrl) {
            localStorage.removeItem('tm_auth_next_url');
            window.location.href = nextUrl;
            return;
          }

          var pendingPlan = self.pendingPlanId || localStorage.getItem('tm_pending_plan_id');
          if (pendingPlan) {
            window.location.href = '/subscription/checkout/?plan=' + pendingPlan;
          } else {
            window.location.href = data.redirect_url || '/dashboard/';
          }
        } else {
          btn.disabled = false;
          btn.innerHTML = '<span>Login</span> <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>';
          self.showError('login', data.message || 'Invalid email/phone or password.');
        }
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.innerHTML = '<span>Login</span> <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>';
        self.showError('login', err.message || 'Incorrect email/phone or password. Please try again.');
      });
    },

    handleDemoLogin: function () {
      var self = this;
      self.clearErrors();

      var btn = document.getElementById('tmLoginBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="tm-auth-spinner"></span> <span>Entering Demo…</span>';

      var demoUrl = getApiUrl('/login/');
      fetch(demoUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ email: 'student', password: 'student123' })
      })
      .then(function (res) {
        if (res.ok) return res.json();
        return fetch(demoUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({ email: 'student', password: 'password123' })
        }).then(function (r) {
          if (r.ok) return r.json();
          throw new Error('Demo login failed');
        });
      })
      .then(function (data) {
        if (data.success) {
          if (data.access) localStorage.setItem('tm_access', data.access);
          if (data.refresh) localStorage.setItem('tm_refresh', data.refresh);
          var nextUrl = localStorage.getItem('tm_auth_next_url');
          if (nextUrl) {
            localStorage.removeItem('tm_auth_next_url');
            window.location.href = nextUrl;
            return;
          }
          window.location.href = data.redirect_url || '/dashboard/';
        } else {
          btn.disabled = false;
          btn.innerHTML = '<span>Login</span>';
          self.showError('login', 'Demo login unavailable. Please create an account.');
        }
      })
      .catch(function () {
        btn.disabled = false;
        btn.innerHTML = '<span>Login</span>';
        self.showError('login', 'Demo student profile currently unavailable.');
      });
    },

    handleRegister: function (e) {
      if (e) e.preventDefault();
      var self = this;
      self.clearErrors();

      var name = (document.getElementById('tmRegFullName').value || '').trim();
      var phone = (document.getElementById('tmRegPhone').value || '').trim();
      var email = (document.getElementById('tmRegEmail').value || '').trim().toLowerCase();
      var classLevel = document.getElementById('tmRegClassLevel').value;
      var password = document.getElementById('tmRegPassword').value || '';
      var confirmPassword = document.getElementById('tmRegConfirmPassword').value || '';
      var agree = document.getElementById('tmRegAgree').checked;

      if (!name) { self.showError('register', 'Please enter your full name.'); return; }
      var cleanPhone = phone.replace(/[\s\-\(\)\.]/g, '');
      if (!cleanPhone || cleanPhone.length < 10) { self.showError('register', 'Please enter a valid 10-digit phone number.'); return; }
      if (!email || !email.includes('@')) { self.showError('register', 'Please enter a valid email address.'); return; }
      if (!classLevel) { self.showError('register', 'Please select your class / grade level.'); return; }
      if (!password || password.length < 6) { self.showError('register', 'Password must be at least 6 characters long.'); return; }
      if (password !== confirmPassword) { self.showError('register', 'Passwords do not match.'); return; }
      if (!agree) { self.showError('register', 'You must agree to the Terms of Service & Privacy Policy.'); return; }

      var btn = document.getElementById('tmRegisterBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="tm-auth-spinner"></span> <span>Creating Account…</span>';

      var regUrl = getApiUrl('/register/');
      fetch(regUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          name: name,
          phone: phone,
          email: email,
          classLevel: parseInt(classLevel, 10),
          password: password
        })
      })
      .then(function (res) {
        if (res.ok) return res.json();
        return res.json().then(function (err) { throw err; });
      })
      .then(function (data) {
        if (data.success) {
          if (data.access) localStorage.setItem('tm_access', data.access);
          if (data.refresh) localStorage.setItem('tm_refresh', data.refresh);

          var nextUrl = localStorage.getItem('tm_auth_next_url');
          if (nextUrl) {
            localStorage.removeItem('tm_auth_next_url');
            window.location.href = nextUrl;
            return;
          }

          var pendingPlan = self.pendingPlanId || localStorage.getItem('tm_pending_plan_id');
          if (pendingPlan) {
            window.location.href = '/subscription/checkout/?plan=' + pendingPlan;
          } else {
            window.location.href = data.redirect_url || '/dashboard/';
          }
        } else {
          btn.disabled = false;
          btn.innerHTML = '<span>Create Account</span> <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4-4-4"></path><path d="M3 10h13"></path><path d="M21 20V4"></path></svg>';
          self.showError('register', data.message || 'Registration failed. Email or phone number may already exist.');
        }
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.innerHTML = '<span>Create Account</span> <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4-4-4"></path><path d="M3 10h13"></path><path d="M21 20V4"></path></svg>';
        self.showError('register', err.message || 'That email or phone number is already registered. Please try logging in.');
      });
    },

    handleRequestOTP: function (e) {
      if (e) e.preventDefault();
      var self = this;
      var email = (document.getElementById('tmForgotEmail').value || '').trim();
      var errBox = document.getElementById('tmForgotError1');
      var errMsg = document.getElementById('tmForgotErrorMsg1');

      if (!email || !email.includes('@')) {
        errMsg.textContent = 'Please enter a valid email address.';
        errBox.style.display = 'flex';
        return;
      }
      errBox.style.display = 'none';

      var btn = document.getElementById('tmBtnRequestOTP');
      btn.disabled = true;
      btn.innerHTML = '<span class="tm-auth-spinner"></span> <span>Sending OTP…</span>';

      var otpUrl = getApiUrl('/api/auth/forgot-password/');
      fetch(otpUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ email: email })
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        btn.disabled = false;
        btn.innerHTML = '<span>Send OTP</span>';
        if (data.success) {
          self.openForgotStep2();
        } else {
          errMsg.textContent = data.message || 'Unable to find an account with that email.';
          errBox.style.display = 'flex';
        }
      })
      .catch(function () {
        btn.disabled = false;
        btn.innerHTML = '<span>Send OTP</span>';
        errMsg.textContent = 'Network error requesting OTP. Please try again.';
        errBox.style.display = 'flex';
      });
    },

    handleVerifyOTP: function (e) {
      if (e) e.preventDefault();
      var self = this;
      var email = (document.getElementById('tmForgotEmail').value || '').trim();
      var otp = (document.getElementById('tmForgotOTP').value || '').trim();
      var newPass = document.getElementById('tmForgotNewPass').value || '';
      var errBox = document.getElementById('tmForgotError2');
      var errMsg = document.getElementById('tmForgotErrorMsg2');

      if (!otp || otp.length < 4) {
        errMsg.textContent = 'Please enter the verification OTP code.';
        errBox.style.display = 'flex';
        return;
      }
      if (!newPass || newPass.length < 6) {
        errMsg.textContent = 'New password must be at least 6 characters.';
        errBox.style.display = 'flex';
        return;
      }
      errBox.style.display = 'none';

      var btn = document.getElementById('tmBtnVerifyOTP');
      btn.disabled = true;
      btn.innerHTML = '<span class="tm-auth-spinner"></span> <span>Resetting Password…</span>';

      var verifyUrl = getApiUrl('/api/auth/forgot-password/verify/');
      fetch(verifyUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ email: email, otp: otp, new_password: newPass })
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        btn.disabled = false;
        btn.innerHTML = '<span>Reset Password &amp; Login</span>';
        if (data.success) {
          alert('Password successfully reset! You can now log in with your new password.');
          self.openLogin();
        } else {
          errMsg.textContent = data.message || 'Invalid or expired OTP code.';
          errBox.style.display = 'flex';
        }
      })
      .catch(function () {
        btn.disabled = false;
        btn.innerHTML = '<span>Reset Password &amp; Login</span>';
        errMsg.textContent = 'Network error resetting password. Please try again.';
        errBox.style.display = 'flex';
      });
    }
  };

  // Expose globally
  global.TMAuthModal = TMAuthModal;

  // Auto-initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { TMAuthModal.init(); });
  } else {
    TMAuthModal.init();
  }

})(window);
