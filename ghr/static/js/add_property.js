(() => {
  const configEl = document.getElementById('addPropertyConfig');
  const generateUrl = configEl?.dataset.generateUrl;
  const csrfToken = configEl?.dataset.csrfToken;

  const featuredInput = document.getElementById('featuredInput');
  const featuredPreview = document.getElementById('featuredPreview');
  const featuredInner = document.getElementById('featuredInner');
  const featuredZone = document.getElementById('featuredZone');
  const generateBtn = document.getElementById('generateDescBtn');
  const generateStatus = document.getElementById('generateStatus');
  const descriptionField = document.getElementById('descriptionField');
  const progressBar = document.getElementById('progressBar');
  const progressLabel = document.getElementById('progressLabel');

  function updateProgress() {
    const fields = ['title', 'price', 'city', 'area', 'description'];
    let filled = 0;
    fields.forEach(f => {
      const el = document.querySelector(`[name="${f}"]`);
      if (el && el.value.trim()) filled++;
    });
    if (featuredInput && featuredInput.files.length) filled++;
    const pct = Math.round((filled / (fields.length + 1)) * 100);
    if (progressBar) progressBar.style.width = pct + '%';
    if (progressLabel) progressLabel.textContent = pct + '% Complete';
  }

  if (featuredInput) {
    featuredInput.addEventListener('change', function () {
      if (this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          if (featuredPreview) featuredPreview.src = e.target.result;
          if (featuredPreview) featuredPreview.style.display = 'block';
          if (featuredInner) featuredInner.style.display = 'none';
          if (featuredZone) featuredZone.classList.remove('file-zone-error');
        };
        reader.readAsDataURL(this.files[0]);
      }
      updateProgress();
    });
  }

  document.querySelectorAll('.extra-img-input').forEach(input => {
    input.addEventListener('change', function () {
      const zone = this.closest('.file-zone-sm');
      if (!zone) return;
      const inner = zone.querySelector('.fz-inner-sm');
      const preview = zone.querySelector('.fz-preview-sm');
      if (this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          if (preview) preview.src = e.target.result;
          if (preview) preview.style.display = 'block';
          if (inner) inner.style.display = 'none';
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
  });

  if (featuredZone) {
    featuredZone.addEventListener('dragover', e => { e.preventDefault(); featuredZone.classList.add('drag-over'); });
    featuredZone.addEventListener('dragleave', () => featuredZone.classList.remove('drag-over'));
    featuredZone.addEventListener('drop', e => {
      e.preventDefault();
      featuredZone.classList.remove('drag-over');
      if (featuredInput) {
        featuredInput.files = e.dataTransfer.files;
        featuredInput.dispatchEvent(new Event('change'));
      }
    });
  }

  document.querySelectorAll('input, textarea, select').forEach(el => {
    el.addEventListener('input', updateProgress);
    el.addEventListener('change', updateProgress);
  });

  updateProgress();

  window.generateDescription = async function generateDescription() {
    if (!generateUrl || !csrfToken || !generateBtn || !generateStatus || !descriptionField) {
      return;
    }

    const getVal = name => document.querySelector(`[name="${name}"]`)?.value?.trim() || '';

    const rawPrice = getVal('price');
    const formattedPrice = rawPrice
      ? parseInt(rawPrice.replace(/,/g, ''), 10).toLocaleString('en-PK') + ' PKR'
      : 'N/A';

    const propTypeEl = document.querySelector('[name="property_type"]');
    const propertyTypeText = propTypeEl?.options[propTypeEl.selectedIndex]?.text?.trim() || '';
    const furnishingEl = document.querySelector('[name="furnishing"]:checked');
    const furnishingVal = furnishingEl?.value || '';
    const featuresText = [...document.querySelectorAll('.feature-item.selected .fi-name')]
      .map(el => el.textContent.trim())
      .join(', ');

    const data = {
      title: getVal('title'),
      purpose: getVal('purpose') === 'sale' ? 'For Sale' : 'For Rent',
      property_type: propertyTypeText,
      price: formattedPrice,
      city: getVal('city'),
      area: getVal('area'),
      address: getVal('address'),
      bedrooms: getVal('bedrooms'),
      bathrooms: getVal('bathrooms'),
      kitchens: getVal('kitchens'),
      garage: getVal('garages'),
      property_size: getVal('property_size'),
      year_built: getVal('year_built'),
      furnished: furnishingVal,
      features: featuresText,
      description: descriptionField.value || '',
    };

    if (!data.title) {
      generateStatus.textContent = '⚠ Please enter a property title first.';
      generateStatus.style.color = '#e53e3e';
      return;
    }

    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
    generateStatus.style.color = 'var(--text-muted)';
    generateStatus.textContent = 'AI is writing your description...';

    try {
      const res = await fetch(generateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(data),
      });

      const result = await res.json();

      if (result.description) {
        descriptionField.value = result.description;
        generateStatus.textContent = '✓ Description generated successfully!';
        generateStatus.style.color = 'var(--green)';
        updateProgress();
      } else {
        generateStatus.textContent = '✗ Failed to generate. Try again.';
        generateStatus.style.color = '#e53e3e';
      }
    } catch (err) {
      generateStatus.textContent = '✗ Something went wrong. Try again.';
      generateStatus.style.color = '#e53e3e';
    } finally {
      generateBtn.disabled = false;
      generateBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate with AI';
    }
  };
})();