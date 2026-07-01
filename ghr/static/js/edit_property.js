(() => {
  document.querySelectorAll('.num-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.target);
      if (!input) return;
      let val = parseInt(input.value) || 0;
      if (btn.dataset.action === 'inc') val++;
      else if (btn.dataset.action === 'dec' && val > 0) val--;
      input.value = val;
    });
  });

  document.querySelectorAll('.fpill input').forEach(r => {
    r.addEventListener('change', () => {
      document.querySelectorAll('.fpill').forEach(p => p.classList.remove('active'));
      r.closest('.fpill')?.classList.add('active');
    });
  });

  document.querySelectorAll('.feature-item input').forEach(cb => {
    cb.addEventListener('change', () => {
      cb.closest('.feature-item')?.classList.toggle('selected', cb.checked);
    });
  });

  const featuredInput = document.getElementById('featuredInput');
  const featuredPreview = document.getElementById('featuredPreview');
  const snapImg = document.getElementById('snapImg');

  if (featuredInput) {
    featuredInput.addEventListener('change', function () {
      if (this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          if (featuredPreview) featuredPreview.src = e.target.result;
          if (snapImg) snapImg.src = e.target.result;
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
  }

  const galleryInput = document.getElementById('galleryInput');
  const newPreviews = document.getElementById('newPreviews');
  if (galleryInput && newPreviews) {
    galleryInput.addEventListener('change', function () {
      newPreviews.innerHTML = '';
      Array.from(this.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = e => {
          const div = document.createElement('div');
          div.className = 'np-thumb';
          div.innerHTML = `<img src="${e.target.result}" alt="New photo"><span>${file.name}</span>`;
          newPreviews.appendChild(div);
        };
        reader.readAsDataURL(file);
      });
    });
  }

  const galleryZone = document.getElementById('galleryZone');
  if (galleryZone && galleryInput) {
    galleryZone.addEventListener('dragover', e => { e.preventDefault(); galleryZone.classList.add('drag-over'); });
    galleryZone.addEventListener('dragleave', () => galleryZone.classList.remove('drag-over'));
    galleryZone.addEventListener('drop', e => {
      e.preventDefault();
      galleryZone.classList.remove('drag-over');
      if (galleryInput) {
        galleryInput.files = e.dataTransfer.files;
        galleryInput.dispatchEvent(new Event('change'));
      }
    });
  }

  const deleteModal = document.getElementById('deleteModal');
  const openBtns = [document.getElementById('openDeleteModal'), document.getElementById('openDeleteModal2')].filter(Boolean);
  const closeBtn = document.getElementById('closeDeleteModal');

  function closeDeleteModal() {
    if (deleteModal) deleteModal.classList.remove('active');
  }

  openBtns.forEach(btn => { if (btn) btn.addEventListener('click', () => deleteModal?.classList.add('active')); });
  if (closeBtn) closeBtn.addEventListener('click', closeDeleteModal);
  if (deleteModal) {
    deleteModal.addEventListener('click', e => { if (e.target === deleteModal) closeDeleteModal(); });
  }
})();