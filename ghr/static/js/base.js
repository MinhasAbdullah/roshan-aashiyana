  (() => {
    // ── Modal open/close ──
    const modal    = document.getElementById('modal');
    const authBox  = document.getElementById('authBox');
    const openBtn  = document.getElementById('openModal');
    const openBtn2 = document.getElementById('openModal2');
    const closeBtn = document.getElementById('closeModal');
    const openSignupLink = document.getElementById('openSignup');
    const openLoginLink  = document.getElementById('openLogin');
    const openForgotLink = document.getElementById('openForgot');
    const backToLoginLink = document.getElementById('backToLogin');

    function openModal(mode) {
      modal.classList.add('active');
      authBox.classList.toggle('signup-mode', mode === 'signup');
      authBox.classList.toggle('forgot-mode', mode === 'forgot');
    }

    if (openBtn)  openBtn.addEventListener('click',  () => openModal('login'));
    if (openBtn2) openBtn2.addEventListener('click', () => openModal('login'));
    if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    window.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });
    if (openSignupLink) openSignupLink.addEventListener('click', () => openModal('signup'));
    if (openLoginLink)  openLoginLink.addEventListener('click',  () => openModal('login'));
    if (openForgotLink) openForgotLink.addEventListener('click', () => openModal('forgot'));
    if (backToLoginLink) backToLoginLink.addEventListener('click', () => openModal('login'));

    // ── Nav active link ──
    document.querySelectorAll('.nav-links a').forEach(link => {
      if (link.href === window.location.href) link.classList.add('active');
    });

    // ── Hamburger ──
    const hamburger = document.getElementById('hamburger');
    const navLinks  = document.getElementById('navLinks');
    if (hamburger) hamburger.addEventListener('click', () => navLinks.classList.toggle('open'));

    // ── Auto-dismiss Django messages (non-modal ones) ──
    setTimeout(() => {
      document.querySelectorAll('.msg').forEach(msg => {
        msg.style.opacity = '0';
        msg.style.transform = 'translateX(50px)';
        msg.style.transition = '0.4s';
        setTimeout(() => msg.remove(), 500);
      });
    }, 5000);

    // ── URL param error handler — reopen modal with error, restore values ──
    const params    = new URLSearchParams(window.location.search);
    const authError = params.get('auth_error');
    const authForm  = params.get('auth_form');

    if (authError) {
      const forgotSuccessEl = document.getElementById('forgotSuccess');
      const forgotErrorEl = document.getElementById('forgotError');
      if (forgotSuccessEl) forgotSuccessEl.style.display = 'none';
      if (forgotErrorEl) forgotErrorEl.style.display = 'none';

      openModal(authForm || 'login');

      if (authForm === 'signup') {
        const errEl = document.getElementById('signupError');
        errEl.querySelector('span').textContent = authError;
        errEl.style.display = 'flex';
        const u = document.getElementById('suUname');
        const e = document.getElementById('suEmail');
        const p = document.getElementById('suPhone');
        if (u && params.get('auth_uname')) u.value = params.get('auth_uname');
        if (e && params.get('auth_email')) e.value = params.get('auth_email');
        if (p && params.get('auth_phone')) p.value = params.get('auth_phone');
      } else if (authForm === 'forgot') {
        const errEl = document.getElementById('forgotError');
        errEl.querySelector('span').textContent = authError;
        errEl.style.display = 'flex';
        openModal('forgot');
      } else {
        const errEl = document.getElementById('loginError');
        errEl.querySelector('span').textContent = authError;
        errEl.style.display = 'flex';
        const u = document.getElementById('lgUname');
        if (u && params.get('auth_uname')) u.value = params.get('auth_uname');
      }

      // Clean URL without reload
      window.history.replaceState({}, '', window.location.pathname);
    }

    const successMsg = params.get('auth_success');
    if (successMsg) {
      const successEl = document.getElementById('forgotSuccess');
      const errorEl = document.getElementById('forgotError');
      if (successEl) {
        successEl.querySelector('span').textContent = successMsg;
        successEl.style.display = 'flex';
      }
      if (errorEl) errorEl.style.display = 'none';
      openModal('forgot');
      window.history.replaceState({}, '', window.location.pathname);
    }

    // ── Password show/hide toggle ──
    document.querySelectorAll('.pwd-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const input = document.getElementById(btn.dataset.target);
        const icon  = btn.querySelector('i');
        if (input.type === 'password') {
          input.type = 'text';
          icon.className = 'fa-solid fa-eye-slash';
        } else {
          input.type = 'password';
          icon.className = 'fa-solid fa-eye';
        }
      });
    });

    // ════════════════════════════════════════
    // REAL-TIME SIGNUP VALIDATION
    // ════════════════════════════════════════
    const suUname  = document.getElementById('suUname');
    const suEmail  = document.getElementById('suEmail');
    const suPhone  = document.getElementById('suPhone');
    const suPass   = document.getElementById('suPass');
    const suCpass  = document.getElementById('suCpass');
    const submitBtn = document.getElementById('signupSubmitBtn');

    // Track validity state
    const validity = { uname: false, email: true, phone: true, pass: false, cpass: false };

    function setFieldState(groupId, msgId, isValid, msg, isOptional) {
      const group = document.getElementById(groupId);
      const msgEl = document.getElementById(msgId);
      if (!group || !msgEl) return;

      // Remove previous states
      group.classList.remove('field-valid', 'field-invalid');
      msgEl.classList.remove('msg-valid', 'msg-error');

      if (isOptional && !group.querySelector('input').value.trim()) {
        msgEl.textContent = '';
        return; // optional and empty — neutral
      }

      if (isValid) {
        group.classList.add('field-valid');
        msgEl.classList.add('msg-valid');
        msgEl.textContent = msg || '';
      } else {
        group.classList.add('field-invalid');
        msgEl.classList.add('msg-error');
        msgEl.textContent = msg || '';
      }

      // Update submit button
      submitBtn.disabled = !Object.values(validity).every(Boolean);
    }

    // Username
    if (suUname) {
      suUname.addEventListener('input', () => {
        const val = suUname.value.trim();
        if (!val) {
          setFieldState('su-uname-group', 'su-uname-msg', false, 'Username is required.');
          validity.uname = false;
        } else if (val.length < 6) {
          setFieldState('su-uname-group', 'su-uname-msg', false, `${val.length}/6 — needs ${6 - val.length} more character(s).`);
          validity.uname = false;
        } else if (!/^[a-zA-Z0-9_]+$/.test(val)) {
          setFieldState('su-uname-group', 'su-uname-msg', false, 'Only letters, numbers and underscores allowed.');
          validity.uname = false;
        } else {
          setFieldState('su-uname-group', 'su-uname-msg', true, '✓ Username looks good!');
          validity.uname = true;
        }
        submitBtn.disabled = !Object.values(validity).every(Boolean);
      });
    }

    // Email
    if (suEmail) {
      suEmail.addEventListener('input', () => {
        const val = suEmail.value.trim();
        const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!val) {
          setFieldState('su-email-group', 'su-email-msg', false, 'Email is required.');
          validity.email = false;
        } else if (!emailRe.test(val)) {
          setFieldState('su-email-group', 'su-email-msg', false, 'Enter a valid email address.');
          validity.email = false;
        } else {
          setFieldState('su-email-group', 'su-email-msg', true, '✓ Valid email!');
          validity.email = true;
        }
        submitBtn.disabled = !Object.values(validity).every(Boolean);
      });
    }

    // Phone (optional)
    if (suPhone) {
      suPhone.addEventListener('input', () => {
        const val = suPhone.value.trim();
        if (!val) {
          setFieldState('su-phone-group', 'su-phone-msg', true, '', true);
          validity.phone = true;
        } else {
          const digits = val.replace(/\D/g, '');
          if (digits.length < 10) {
            setFieldState('su-phone-group', 'su-phone-msg', false, 'Enter at least 11 digits.');
            validity.phone = false;
          } else {
            setFieldState('su-phone-group', 'su-phone-msg', true, '✓ Valid phone number!');
            validity.phone = true;
          }
        }
        submitBtn.disabled = !Object.values(validity).every(Boolean);
      });
    }

    // Password + strength meter
    if (suPass) {
      suPass.addEventListener('input', () => {
        const val = suPass.value;
        const bar   = document.getElementById('pwdStrengthBar');
        const label = document.getElementById('pwdStrengthLabel');
        const wrap  = document.getElementById('pwdStrengthWrap');

        if (!val) {
          setFieldState('su-pass-group', 'su-pass-msg', false, 'Password is required.');
          validity.pass = false;
          if (wrap) wrap.style.display = 'none';
        } else {
          if (wrap) wrap.style.display = 'block';
          // Strength scoring
          let score = 0;
          if (val.length >= 6)  score++;
          if (val.length >= 10) score++;
          if (/[A-Z]/.test(val))  score++;
          if (/[0-9]/.test(val))  score++;
          if (/[^A-Za-z0-9]/.test(val)) score++;

          const levels = [
            { pct: '20%',  color: '#e53935', text: 'Very Weak' },
            { pct: '40%',  color: '#f97316', text: 'Weak' },
            { pct: '60%',  color: '#eab308', text: 'Fair' },
            { pct: '80%',  color: '#22c55e', text: 'Strong' },
            { pct: '100%', color: '#16a34a', text: 'Very Strong' },
          ];
          const lvl = levels[Math.min(score - 1, 4)] || levels[0];
          if (bar)   { bar.style.width = lvl.pct; bar.style.background = lvl.color; }
          if (label) { label.textContent = lvl.text; label.style.color = lvl.color; }

          if (val.length < 6) {
            setFieldState('su-pass-group', 'su-pass-msg', false, `${val.length}/6 — needs ${6 - val.length} more character(s).`);
            validity.pass = false;
          } else {
            setFieldState('su-pass-group', 'su-pass-msg', true, '✓ Password length is good.');
            validity.pass = true;
          }
        }
        // Re-check confirm password if already filled
        if (suCpass && suCpass.value) suCpass.dispatchEvent(new Event('input'));
        submitBtn.disabled = !Object.values(validity).every(Boolean);
      });
    }

    // Confirm password
    if (suCpass) {
      suCpass.addEventListener('input', () => {
        const val = suCpass.value;
        if (!val) {
          setFieldState('su-cpass-group', 'su-cpass-msg', false, 'Please confirm your password.');
          validity.cpass = false;
        } else if (suPass && val !== suPass.value) {
          setFieldState('su-cpass-group', 'su-cpass-msg', false, 'Passwords do not match.');
          validity.cpass = false;
        } else {
          setFieldState('su-cpass-group', 'su-cpass-msg', true, '✓ Passwords match!');
          validity.cpass = true;
        }
        submitBtn.disabled = !Object.values(validity).every(Boolean);
      });
    }

    // ── LOGIN: basic non-empty check ──
    const lgUname = document.getElementById('lgUname');
    const lgPass  = document.getElementById('lgPass');

    if (lgUname) {
      lgUname.addEventListener('input', () => {
        const g = document.getElementById('lg-uname-group');
        const m = document.getElementById('lg-uname-msg');
        if (!lgUname.value.trim()) {
          g.classList.add('field-invalid'); g.classList.remove('field-valid');
          m.className = 'field-hint-msg msg-error'; m.textContent = 'Username is required.';
        } else {
          g.classList.add('field-valid'); g.classList.remove('field-invalid');
          m.className = 'field-hint-msg'; m.textContent = '';
        }
      });
    }

    if (lgPass) {
      lgPass.addEventListener('input', () => {
        const g = document.getElementById('lg-pass-group');
        const m = document.getElementById('lg-pass-msg');
        if (!lgPass.value) {
          g.classList.add('field-invalid'); g.classList.remove('field-valid');
          m.className = 'field-hint-msg msg-error'; m.textContent = 'Password is required.';
        } else {
          g.classList.add('field-valid'); g.classList.remove('field-invalid');
          m.className = 'field-hint-msg'; m.textContent = '';
        }
      });
    }

    const fgEmail = document.getElementById('fgEmail');
    if (fgEmail) {
      fgEmail.addEventListener('input', () => {
        const group = document.getElementById('fg-email-group');
        const msg = document.getElementById('fg-email-msg');
        const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!fgEmail.value.trim()) {
          group.classList.add('field-invalid'); group.classList.remove('field-valid');
          msg.className = 'field-hint-msg msg-error'; msg.textContent = 'Email is required.';
        } else if (!emailRe.test(fgEmail.value.trim())) {
          group.classList.add('field-invalid'); group.classList.remove('field-valid');
          msg.className = 'field-hint-msg msg-error'; msg.textContent = 'Enter a valid email address.';
        } else {
          group.classList.add('field-valid'); group.classList.remove('field-invalid');
          msg.className = 'field-hint-msg'; msg.textContent = '';
        }
      });
    }

  })();
// ── Dropdown ──
const trigger = document.getElementById('profileTrigger');
const menu    = document.getElementById('dropdownMenu');

trigger.addEventListener('click', e => {
  e.stopPropagation();
  menu.classList.toggle('open');
  if (menu.classList.contains('open')) showPanel('main');
});
document.addEventListener('click', e => {
  if (!menu.contains(e.target)) menu.classList.remove('open');
});

// ── Panel navigation ──
function showPanel(name) {
  document.getElementById('dropdownMain').style.display     = name === 'main'     ? 'block' : 'none';
  document.getElementById('dropdownSettings').style.display = name === 'settings' ? 'block' : 'none';
  document.getElementById('dropdownUsername').style.display = name === 'username' ? 'block' : 'none';
  document.getElementById('dropdownPassword').style.display = name === 'password' ? 'block' : 'none';
}

// ── Toggle password visibility ──
function togglePwd(id, btn) {
  const input = document.getElementById(id);
  const icon  = btn.querySelector('i');
  input.type  = input.type === 'password' ? 'text' : 'password';
  icon.className = input.type === 'password' ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
}

// ── Change username ──
async function changeUsername() {
  const val    = document.getElementById('newUsername').value.trim();
  const err    = document.getElementById('usernameErr');
  const status = document.getElementById('usernameStatus');

  err.textContent    = '';
  status.textContent = '';

  if (val.length < 6) { err.textContent = 'Min 6 characters.'; return; }
  if (!/^[a-zA-Z0-9_]+$/.test(val)) { err.textContent = 'Only letters, numbers and underscores.'; return; }

  try {
    const res = await fetch('/account/change-username/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ username: val }),
    });
    const data = await res.json();
    if (data.success) {
      status.style.color = '#3cb648';
      status.textContent = '✓ Username updated! Reloading...';
      setTimeout(() => location.reload(), 1500);
    } else {
      err.textContent = data.error || 'Something went wrong.';
    }
  } catch { err.textContent = 'Request failed. Try again.'; }
}

// ── Change password ──
async function changePassword() {
  const current = document.getElementById('currentPwd').value;
  const newPwd  = document.getElementById('newPwd').value;
  const confirm = document.getElementById('confirmPwd').value;
  const err     = document.getElementById('passwordErr');
  const status  = document.getElementById('passwordStatus');

  err.textContent    = '';
  status.textContent = '';

  if (!current)           { err.textContent = 'Enter current password.'; return; }
  if (newPwd.length < 6)  { err.textContent = 'New password must be at least 6 characters.'; return; }
  if (newPwd !== confirm) { err.textContent = 'Passwords do not match.'; return; }

  try {
    const res = await fetch('/account/change-password/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ current_password: current, new_password: newPwd }),
    });
    const data = await res.json();
    if (data.success) {
      status.style.color = '#3cb648';
      status.textContent = '✓ Password updated!';
      document.getElementById('currentPwd').value = '';
      document.getElementById('newPwd').value      = '';
      document.getElementById('confirmPwd').value  = '';
    } else {
      err.textContent = data.error || 'Something went wrong.';
    }
  } catch { err.textContent = 'Request failed. Try again.'; }
}

function getCookie(name) {
  return document.cookie.split(';').map(c => c.trim())
    .find(c => c.startsWith(name + '='))?.split('=')[1] || '';
}

