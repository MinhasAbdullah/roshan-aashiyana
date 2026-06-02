  // Live search filter
  const searchInput  = document.getElementById('dealerSearch');
  const dealerCards  = document.querySelectorAll('.dealer-card');
  const dealerCount  = document.getElementById('dealerCount');

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase().trim();
    let visible = 0;
    dealerCards.forEach(card => {
      const name = card.dataset.name || '';
      const city = card.dataset.city || '';
      const match = name.includes(q) || city.includes(q);
      card.style.display = match ? '' : 'none';
      if (match) visible++;
    });
    dealerCount.textContent = visible;
  });