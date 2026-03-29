document.addEventListener('DOMContentLoaded', () => {
  const html = document.documentElement;
  const toggle = document.querySelector('.theme-toggle');
  
  // Load saved theme
  const savedTheme = localStorage.getItem('theme') || 
    (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  html.setAttribute('data-theme', savedTheme);
  
  if (toggle) {
    // Set initial icon
    toggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    
    toggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      // Update icon
      toggle.textContent = next === 'dark' ? '☀️' : '🌙';
    });
  }
});

