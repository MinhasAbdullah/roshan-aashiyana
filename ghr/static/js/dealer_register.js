(() => {
  const pictureInput = document.getElementById('pictureInput');
  const filePreview = document.getElementById('filePreview');
  const fileDropInner = document.getElementById('fileDropInner');
  const fileDrop = document.getElementById('fileDrop');

  function showFieldSuccess(wrapId, msgId, message, isFile) {
    const wrap = document.getElementById(wrapId);
    const msgEl = document.getElementById(msgId);
    if (!wrap || !msgEl) return;
    if (isFile) {
      wrap.classList.remove('file-drop-error');
    } else {
      wrap.classList.remove('field-invalid');
      wrap.classList.add('field-valid');
    }
    msgEl.className = 'field-hint-msg msg-valid';
    msgEl.textContent = message;
  }

  function showFieldError(wrapId, msgId, message, isFile) {
    const wrap = document.getElementById(wrapId);
    const msgEl = document.getElementById(msgId);
    if (!wrap || !msgEl) return;
    if (isFile) {
      wrap.classList.add('file-drop-error');
    } else {
      wrap.classList.remove('field-valid');
      wrap.classList.add('field-invalid');
    }
    msgEl.className = 'field-hint-msg msg-error';
    msgEl.textContent = message;
  }

  function clearField(wrapId, msgId) {
    const wrap = document.getElementById(wrapId);
    const msgEl = document.getElementById(msgId);
    if (!wrap || !msgEl) return;
    wrap.classList.remove('field-valid', 'field-invalid');
    msgEl.className = 'field-hint-msg';
    msgEl.textContent = '';
  }

  if (!pictureInput || !filePreview || !fileDropInner || !fileDrop) return;

  pictureInput.addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)) {
      showFieldError('fileDrop', 'dr-pic-msg', 'Only JPG, PNG or WebP images allowed.', true);
      this.value = '';
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      showFieldError('fileDrop', 'dr-pic-msg', 'File too large. Max size is 5MB.', true);
      this.value = '';
      return;
    }
    const reader = new FileReader();
    reader.onload = e => {
      filePreview.src = e.target.result;
      filePreview.style.display = 'block';
      fileDropInner.style.display = 'none';
      fileDrop.classList.remove('file-drop-error');
      showFieldSuccess('fileDrop', 'dr-pic-msg', '✓ Photo selected!', true);
    };
    reader.readAsDataURL(file);
  });

  fileDrop.addEventListener('dragover', e => { e.preventDefault(); fileDrop.classList.add('drag-over'); });
  fileDrop.addEventListener('dragleave', () => fileDrop.classList.remove('drag-over'));
  fileDrop.addEventListener('drop', e => {
    e.preventDefault();
    fileDrop.classList.remove('drag-over');
    pictureInput.files = e.dataTransfer.files;
    pictureInput.dispatchEvent(new Event('change'));
  });
})();