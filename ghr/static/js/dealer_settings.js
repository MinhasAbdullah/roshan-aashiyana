(() => {
  const config = window.dealerSettingsConfig || {};

  if (config.openSecurityTab) {
    const securityTab = document.querySelector('[data-tab="security"]');
    if (securityTab) securityTab.click();
  }

  const tabs = document.querySelectorAll('.stab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('tab-' + tab.dataset.tab)?.classList.add('active');
    });
  });

  const avatarInput = document.getElementById('avatarInput');
  const avatarImg = document.getElementById('avatarImg');
  if (avatarInput && avatarImg) {
    avatarImg.parentElement?.addEventListener('click', () => avatarInput.click());
    avatarInput.addEventListener('change', function () {
      const file = this.files[0];
      if (!file) return;
      if (file.size > 5 * 1024 * 1024) {
        const avatarHint = document.getElementById('avatarHint');
        if (avatarHint) {
          avatarHint.textContent = '✗ File too large (max 5MB)';
          avatarHint.style.color = '#e53935';
        }
        this.value = '';
        return;
      }
      const reader = new FileReader();
      reader.onload = e => {
        document.getElementById('avatarImg').src = e.target.result;
        const previewAvatar = document.getElementById('previewAvatar');
        if (previewAvatar) previewAvatar.src = e.target.result;
        const avatarHint = document.getElementById('avatarHint');
        if (avatarHint) {
          avatarHint.textContent = '✓ Ready to save';
          avatarHint.style.color = '#16a34a';
        }
      };
      reader.readAsDataURL(file);
    });
  }

  const fullNameInput = document.querySelector('[name="full_name"]');
  if (fullNameInput) {
    fullNameInput.addEventListener('input', function () {
      const previewName = document.getElementById('previewName');
      if (previewName) previewName.textContent = this.value || previewName.textContent;
    });
  }

  document.querySelectorAll('.sg-eye').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.target);
      const icon = btn.querySelector('i');
      if (!input || !icon) return;
      input.type = input.type === 'password' ? 'text' : 'password';
      icon.className = input.type === 'password' ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
    });
  });

  const newPwd = document.getElementById('newPwd');
  const confirmPwd = document.getElementById('confirmPwd');
  const matchMsg = document.getElementById('matchMsg');

  if (newPwd) {
    newPwd.addEventListener('input', () => {
      const val = newPwd.value;
      const wrap = document.getElementById('strengthWrap');
      const bar = document.getElementById('strengthBar');
      const lbl = document.getElementById('strengthLabel');
      if (wrap) wrap.style.display = val ? 'block' : 'none';
      let score = 0;
      if (val.length >= 6) score++;
      if (val.length >= 10) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;
      const lvs = [
        { w: '20%', c: '#e53935', t: 'Very Weak' },
        { w: '40%', c: '#f97316', t: 'Weak' },
        { w: '60%', c: '#eab308', t: 'Fair' },
        { w: '80%', c: '#22c55e', t: 'Strong' },
        { w: '100%', c: '#16a34a', t: 'Very Strong' },
      ];
      const lv = lvs[Math.min(score - 1, 4)] || lvs[0];
      if (bar) {
        bar.style.width = lv.w;
        bar.style.background = lv.c;
      }
      if (lbl) {
        lbl.textContent = lv.t;
        lbl.style.color = lv.c;
      }
      if (confirmPwd) confirmPwd.dispatchEvent(new Event('input'));
    });
  }

  if (confirmPwd && newPwd && matchMsg) {
    confirmPwd.addEventListener('input', () => {
      if (!confirmPwd.value) {
        matchMsg.textContent = '';
        return;
      }
      if (confirmPwd.value === newPwd.value) {
        matchMsg.textContent = '✓ Passwords match!';
        matchMsg.className = 'sg-match-msg match-ok';
      } else {
        matchMsg.textContent = '✗ Passwords do not match.';
        matchMsg.className = 'sg-match-msg match-err';
      }
    });
  }

  const delModal = document.getElementById('deleteAccModal');
  const openDeleteAccount = document.getElementById('openDeleteAccount');
  const closeDeleteAccount = document.getElementById('closeDeleteAccount');

  if (delModal && openDeleteAccount && closeDeleteAccount) {
    openDeleteAccount.addEventListener('click', () => delModal.classList.add('active'));
    closeDeleteAccount.addEventListener('click', () => delModal.classList.remove('active'));
    delModal.addEventListener('click', e => { if (e.target === delModal) delModal.classList.remove('active'); });
  }
})();