// Manejo del Theme Switcher (Modo Claro / Modo Oscuro)
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    const root = document.documentElement;
    
    // Iconos
    const moonIcon = document.getElementById('moon-icon');
    const sunIcon = document.getElementById('sun-icon');
    
    if (!toggleBtn) return; // Si algún archivo HTML aún no lo tiene

    // 1. Revisar si ya había preferencia en LocalStorage
    const savedTheme = localStorage.getItem('kumbalo_theme');
    
    // 2. Revisar preferencia de sistema operativo si no hay guardada
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        setTheme('dark');
    } else {
        setTheme('light');
    }

    // 3. Listener del botón
    toggleBtn.addEventListener('click', () => {
        const currentTheme = root.getAttribute('data-theme');
        if (currentTheme === 'dark') {
            setTheme('light');
        } else {
            setTheme('dark');
        }
    });

    function setTheme(theme) {
        if (theme === 'dark') {
            root.setAttribute('data-theme', 'dark');
            localStorage.setItem('kumbalo_theme', 'dark');
            if (moonIcon && sunIcon) {
                moonIcon.style.display = 'none';
                sunIcon.style.display = 'block';
            }
        } else {
            root.removeAttribute('data-theme');
            localStorage.setItem('kumbalo_theme', 'light');
            if (moonIcon && sunIcon) {
                moonIcon.style.display = 'block';
                sunIcon.style.display = 'none';
            }
        }
    }
});
