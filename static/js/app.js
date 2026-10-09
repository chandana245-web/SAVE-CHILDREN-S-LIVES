document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.getElementById('menuToggle');
  const sideDrawer = document.getElementById('sideDrawer');
  const drawerClose = document.getElementById('drawerClose');
  const languageSelect = document.getElementById('languageSelect');

  if (menuToggle && sideDrawer) {
    menuToggle.addEventListener('click', () => {
      const isOpen = sideDrawer.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', String(isOpen));
    });
  }

  if (drawerClose && sideDrawer) {
    drawerClose.addEventListener('click', () => {
      sideDrawer.classList.remove('open');
      if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
    });
  }

  if (languageSelect) {
    languageSelect.addEventListener('change', (event) => {
      const selected = event.target.value;
      const currentUrl = new URL(window.location.href);
      currentUrl.searchParams.set('lang', selected);
      window.location.href = currentUrl.toString();
    });
  }

  document.querySelectorAll('.pill-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const value = button.getAttribute('data-amount');
      const input = document.getElementById('customAmount');
      if (input && value) input.value = value;
    });
  });
});
