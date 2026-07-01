(() => {
  const deleteModal = document.getElementById('deleteModal');
  const closeDeleteBtn = document.getElementById('closeDeleteModal');

  function openDeleteModal(url, title, img, loc) {
    const dmTitle = document.getElementById('dmTitle');
    const dmTitle2 = document.getElementById('dmTitle2');
    const dmImg = document.getElementById('dmImg');
    const dmLoc = document.getElementById('dmLoc');
    const dmConfirmBtn = document.getElementById('dmConfirmBtn');
    if (!deleteModal || !dmTitle || !dmTitle2 || !dmImg || !dmLoc || !dmConfirmBtn) return;

    dmTitle.textContent = title;
    dmTitle2.textContent = title;
    dmImg.src = img;
    dmLoc.textContent = loc;
    dmConfirmBtn.href = url;
    deleteModal.classList.add('active');
  }

  function closeDeleteModal() {
    if (deleteModal) deleteModal.classList.remove('active');
  }

  document.querySelectorAll('button.act-delete[data-delete-url]').forEach(button => {
    button.addEventListener('click', () => {
      openDeleteModal(
        button.dataset.deleteUrl || '',
        button.dataset.deleteTitle || '',
        button.dataset.deleteImg || '',
        button.dataset.deleteLoc || ''
      );
    });
  });

  if (closeDeleteBtn) {
    closeDeleteBtn.addEventListener('click', closeDeleteModal);
  }

  if (deleteModal) {
    deleteModal.addEventListener('click', function (e) {
      if (e.target === this) closeDeleteModal();
    });
  }
})();