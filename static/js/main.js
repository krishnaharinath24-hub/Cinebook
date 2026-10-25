// CineBook General UI Scripts
document.addEventListener('DOMContentLoaded', function () {
  // 1. Alert Dismissal
  const alertCloses = document.querySelectorAll('.alert-close');
  alertCloses.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // Auto-dismiss success alerts after 6 seconds
  setTimeout(function () {
    const successAlerts = document.querySelectorAll('.alert-success');
    successAlerts.forEach(function (alert) {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 250);
    });
  }, 6000);

  // 2. City Selector Auto-reload
  const citySelect = document.getElementById('navbarCitySelect');
  if (citySelect) {
    citySelect.addEventListener('change', function () {
      const selectedCity = this.value;
      const url = new URL(window.location.href);
      url.searchParams.set('city', selectedCity);
      window.location.href = url.toString();
    });
  }

  // 3. Trailer Modal Support
  const openTrailerBtns = document.querySelectorAll('[data-trailer-id]');
  const trailerModal = document.getElementById('trailerModal');
  const trailerIframe = document.getElementById('trailerIframe');
  const closeTrailerBtn = document.getElementById('closeTrailerModal');

  if (trailerModal && trailerIframe) {
    openTrailerBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        const youtubeId = this.getAttribute('data-trailer-id');
        if (youtubeId) {
          trailerIframe.src = `https://www.youtube.com/embed/${youtubeId}?autoplay=1`;
          trailerModal.classList.add('active');
        }
      });
    });

    function closeTrailer() {
      trailerIframe.src = '';
      trailerModal.classList.remove('active');
    }

    if (closeTrailerBtn) {
      closeTrailerBtn.addEventListener('click', closeTrailer);
    }

    trailerModal.addEventListener('click', function (e) {
      if (e.target === trailerModal) {
        closeTrailer();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && trailerModal.classList.contains('active')) {
        closeTrailer();
      }
    });
  }

  // 4. Ticket Print Helper
  const printTicketBtn = document.getElementById('printTicketBtn');
  if (printTicketBtn) {
    printTicketBtn.addEventListener('click', function () {
      window.print();
    });
  }
});
