document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registroForm = document.getElementById('registroForm');

    // Manejar Login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                const btn = loginForm.querySelector('button[type="submit"]');
                const originalText = btn.innerHTML;
                btn.innerHTML = 'Iniciando...';
                btn.disabled = true;

                await window.api.auth.login(email, password);
                
                // Redirigir al dashboard
                window.location.href = 'dashboard.html';
            } catch (error) {
                document.getElementById('passwordError').textContent = error.message;
            } finally {
                const btn = loginForm.querySelector('button[type="submit"]');
                btn.innerHTML = 'Iniciar Sesión';
                btn.disabled = false;
            }
        });
    }

    // Manejar Registro
    if (registroForm) {
        registroForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const nombre = document.getElementById('nombre').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            if (password !== confirmPassword) {
                document.getElementById('confirmPasswordError').textContent = 'Las contraseñas no coinciden';
                return;
            }

            try {
                const btn = registroForm.querySelector('button[type="submit"]');
                const originalText = btn.innerHTML;
                btn.innerHTML = 'Creando cuenta...';
                btn.disabled = true;

                // 1. Registrar usuario
                await window.api.auth.register(nombre, email, password);
                
                // 2. Iniciar sesión automáticamente
                await window.api.auth.login(email, password);
                
                // 3. Redirigir al dashboard
                window.location.href = 'dashboard.html';
            } catch (error) {
                document.getElementById('emailError').textContent = error.message;
            } finally {
                const btn = registroForm.querySelector('button[type="submit"]');
                btn.innerHTML = 'Crear Cuenta';
                btn.disabled = false;
            }
        });
    }
});
