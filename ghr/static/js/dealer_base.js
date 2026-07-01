(() => {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('dealerSidebar');
  const overlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    if (!sidebar || !overlay) return;
    sidebar.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (!sidebar || !overlay) return;
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  toggle?.addEventListener('click', () => {
    if (!sidebar || !overlay) return;
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
  });

  overlay?.addEventListener('click', closeSidebar);

  window.toggleAvatarDropdown = function () {
    const avatarDropdown = document.getElementById('avatarDropdown');
    if (avatarDropdown) avatarDropdown.classList.toggle('open');
  };

  document.addEventListener('click', function (e) {
    const wrapper = document.querySelector('.dtb-avatar-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
      const avatarDropdown = document.getElementById('avatarDropdown');
      if (avatarDropdown) avatarDropdown.classList.remove('open');
    }
  });
})();