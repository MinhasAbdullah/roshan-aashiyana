(() => {
  const grid = document.getElementById('listingGrid');
  const gridBtn = document.getElementById('gridViewBtn');
  const listBtn = document.getElementById('listViewBtn');

  if (grid && gridBtn && listBtn) {
    gridBtn.addEventListener('click', () => {
      grid.classList.remove('list-view');
      gridBtn.classList.add('active');
      listBtn.classList.remove('active');
      localStorage.setItem('mlView', 'grid');
    });

    listBtn.addEventListener('click', () => {
      grid.classList.add('list-view');
      listBtn.classList.add('active');
      gridBtn.classList.remove('active');
      localStorage.setItem('mlView', 'list');
    });

    if (localStorage.getItem('mlView') === 'list') {
      grid.classList.add('list-view');
      listBtn.classList.add('active');
      gridBtn.classList.remove('active');
    }
  }

  function openDeleteModal(url, title, img, loc) {
    const dmTitle = document.getElementById('dmTitle');
    const dmTitle2 = document.getElementById('dmTitle2');
    const dmImg = document.getElementById('dmImg');
    const dmLoc = document.getElementById('dmLoc');
    const dmConfirmBtn = document.getElementById('dmConfirmBtn');
    const deleteModal = document.getElementById('deleteModal');
    if (!deleteModal || !dmTitle || !dmTitle2 || !dmImg || !dmLoc || !dmConfirmBtn) return;

    dmTitle.textContent = title;
    dmTitle2.textContent = title;
    dmImg.src = img;
    dmLoc.textContent = loc;
    dmConfirmBtn.href = url;
    deleteModal.classList.add('active');
  }

  function closeDeleteModal() {
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) deleteModal.classList.remove('active');
  }

  const deleteModal = document.getElementById('deleteModal');
  if (deleteModal) {
    deleteModal.addEventListener('click', function (e) {
      if (e.target === this) closeDeleteModal();
    });
  }

  window.openDeleteModal = openDeleteModal;
  window.closeDeleteModal = closeDeleteModal;
})();