// ── Number Steppers ──
document.querySelectorAll('.num-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var input = document.getElementById(btn.dataset.target);
    if (!input) return;
    var val = parseInt(input.value) || 0;
    if (btn.dataset.action === 'inc') val++;
    else if (btn.dataset.action === 'dec' && val > 0) val--;
    input.value = val;
    updateProgress();
  });
});

// ── Furnishing Pills ──
document.querySelectorAll('.fpill').forEach(function(pill) {
  pill.addEventListener('click', function() {
    document.querySelectorAll('.fpill').forEach(function(p) { p.classList.remove('active'); });
    pill.classList.add('active');
  });
});

// ── Feature Checkboxes ──
document.querySelectorAll('.feature-item').forEach(function(item) {
  item.addEventListener('click', function() {
    var checkbox = item.querySelector('input[type="checkbox"]');
    if (!checkbox) return;
    checkbox.checked = !checkbox.checked;
    item.classList.toggle('selected', checkbox.checked);
  });
});

// ── Progress Bar ──
function updateProgress() {
  var fields = ['title', 'price', 'city', 'area', 'description'];
  var filled = 0;
  fields.forEach(function(f) {
    var el = document.querySelector('[name="' + f + '"]');
    if (el && el.value && el.value.trim()) filled++;
  });
  var featuredInput = document.getElementById('featuredInput');
  if (featuredInput && featuredInput.files && featuredInput.files.length) filled++;
  var pct = Math.round((filled / (fields.length + 1)) * 100);
  var bar = document.getElementById('progressBar');
  var label = document.getElementById('progressLabel');
  if (bar) bar.style.width = pct + '%';
  if (label) label.textContent = pct + '% Complete';
}

// ── Featured Image Preview ──
var featuredInput = document.getElementById('featuredInput');
var featuredPreview = document.getElementById('featuredPreview');
var featuredInner = document.getElementById('featuredInner');
var featuredZone = document.getElementById('featuredZone');

if (featuredInput) {
  featuredInput.addEventListener('change', function() {
    if (this.files[0]) {
      var reader = new FileReader();
      reader.onload = function(e) {
        if (featuredPreview) { featuredPreview.src = e.target.result; featuredPreview.style.display = 'block'; }
        if (featuredInner) featuredInner.style.display = 'none';
        if (featuredZone) featuredZone.classList.remove('file-zone-error');
      };
      reader.readAsDataURL(this.files[0]);
    }
    updateProgress();
  });
}

// ── Extra Image Previews ──
document.querySelectorAll('.extra-img-input').forEach(function(input) {
  input.addEventListener('change', function() {
    var zone = this.closest('.file-zone-sm');
    if (!zone) return;
    var inner = zone.querySelector('.fz-inner-sm');
    var preview = zone.querySelector('.fz-preview-sm');
    if (this.files[0]) {
      var reader = new FileReader();
      reader.onload = function(e) {
        if (preview) { preview.src = e.target.result; preview.style.display = 'block'; }
        if (inner) inner.style.display = 'none';
      };
      reader.readAsDataURL(this.files[0]);
    }
  });
});

// ── Drag & Drop ──
if (featuredZone) {
  featuredZone.addEventListener('dragover', function(e) { e.preventDefault(); featuredZone.classList.add('drag-over'); });
  featuredZone.addEventListener('dragleave', function() { featuredZone.classList.remove('drag-over'); });
  featuredZone.addEventListener('drop', function(e) {
    e.preventDefault();
    featuredZone.classList.remove('drag-over');
    if (featuredInput) {
      featuredInput.files = e.dataTransfer.files;
      featuredInput.dispatchEvent(new Event('change'));
    }
  });
}

// ── Track all inputs for progress ──
document.querySelectorAll('input, textarea, select').forEach(function(el) {
  el.addEventListener('input', updateProgress);
  el.addEventListener('change', updateProgress);
});

updateProgress();

// ── AI Description Generator ── (global function, not inside IIFE)
function generateDescription() {
  var configEl = document.getElementById('addPropertyConfig');
  var generateUrl = configEl ? configEl.dataset.generateUrl : null;
  var csrfToken = configEl ? configEl.dataset.csrfToken : null;
  var generateBtn = document.getElementById('generateDescBtn');
  var generateStatus = document.getElementById('generateStatus');
  var descriptionField = document.getElementById('descriptionField');

  if (!generateUrl || !csrfToken || !generateBtn || !generateStatus || !descriptionField) {
    console.error('Missing elements for AI generation');
    return;
  }

  function getVal(name) {
    var el = document.querySelector('[name="' + name + '"]');
    return el && el.value ? el.value.trim() : '';
  }

  var rawPrice = getVal('price');
  var formattedPrice = rawPrice
    ? parseInt(rawPrice.replace(/,/g, ''), 10).toLocaleString('en-PK') + ' PKR'
    : 'N/A';

  var propTypeEl = document.querySelector('[name="property_type"]');
  var propertyTypeText = propTypeEl && propTypeEl.selectedIndex >= 0
    ? propTypeEl.options[propTypeEl.selectedIndex].text.trim()
    : '';

  var furnishingEl = document.querySelector('[name="furnishing"]:checked');
  var furnishingVal = furnishingEl ? furnishingEl.value : '';

  var featureEls = document.querySelectorAll('.feature-item.selected .fi-name');
  var featuresText = Array.from(featureEls).map(function(el) { return el.textContent.trim(); }).join(', ');

  var data = {
    title:         getVal('title'),
    purpose:       getVal('purpose') === 'sale' ? 'For Sale' : 'For Rent',
    property_type: propertyTypeText,
    price:         formattedPrice,
    city:          getVal('city'),
    area:          getVal('area'),
    address:       getVal('address'),
    bedrooms:      getVal('bedrooms'),
    bathrooms:     getVal('bathrooms'),
    kitchens:      getVal('kitchens'),
    garage:        getVal('garages'),
    property_size: getVal('property_size'),
    year_built:    getVal('year_built'),
    furnished:     furnishingVal,
    features:      featuresText,
    description:   descriptionField.value || '',
  };

  if (!data.title) {
    generateStatus.textContent = '⚠ Please enter a property title first.';
    generateStatus.style.color = '#e53e3e';
    return;
  }

  generateBtn.disabled = true;
  generateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
  generateStatus.style.color = '#6b7a90';
  generateStatus.textContent = 'AI is writing your description...';

  fetch(generateUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(data),
  })
  .then(function(res) { return res.json(); })
  .then(function(result) {
    if (result.description) {
      descriptionField.value = result.description;
      generateStatus.textContent = '✓ Description generated successfully!';
      generateStatus.style.color = '#3cb648';
      updateProgress();
    } else {
      generateStatus.textContent = '✗ Failed to generate. Try again.';
      generateStatus.style.color = '#e53e3e';
    }
  })
  .catch(function() {
    generateStatus.textContent = '✗ Something went wrong. Try again.';
    generateStatus.style.color = '#e53e3e';
  })
  .finally(function() {
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate with AI';
  });
}