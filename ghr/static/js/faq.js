function toggleFaq(item) {
  const answer = item.querySelector('.faq-answer');
  const icon   = item.querySelector('.fa-chevron-down');
  const isOpen = item.classList.contains('open');

  document.querySelectorAll('.faq-item').forEach(el => {
    el.classList.remove('open');
    el.querySelector('.faq-answer').style.display = 'none';
    el.querySelector('.fa-chevron-down').style.transform = 'rotate(0deg)';
  });

  if (!isOpen) {
    item.classList.add('open');
    answer.style.display     = 'block';
    icon.style.transform     = 'rotate(180deg)';
  }
}