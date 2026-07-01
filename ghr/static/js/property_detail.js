(() => {
  const galleryImgs = document.querySelectorAll('.gallery-img');
  const mainPhoto = document.getElementById('mainPhoto');
  const reviewModal = document.getElementById('reviewModal');
  const openReview = document.getElementById('openReview');
  const closeReview = document.getElementById('closeReview');

  galleryImgs.forEach(div => {
    div.addEventListener('click', () => {
      if (mainPhoto) mainPhoto.src = div.dataset.src;
      galleryImgs.forEach(d => d.classList.remove('active'));
      div.classList.add('active');
    });
  });

  if (reviewModal && openReview && closeReview) {
    openReview.addEventListener('click', () => reviewModal.classList.add('active'));
    closeReview.addEventListener('click', () => reviewModal.classList.remove('active'));
    reviewModal.addEventListener('click', e => { if (e.target === reviewModal) reviewModal.classList.remove('active'); });
  }
})();