document.addEventListener('DOMContentLoaded', () => {
    // Basic GSAP entrance animation
    gsap.from('.auth-card', {
        y: 30,
        opacity: 0,
        duration: 0.6,
        ease: 'power3.out'
    });

    const form = document.getElementById('recoveryForm');
    
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('button');
            const originalText = btn.innerHTML;
            
            btn.innerHTML = 'Enviando...';
            btn.disabled = true;

            const email = document.getElementById('email').value;

            try {
                // Petición real al backend FastApi
                const response = await fetch(`${window.api.baseUrl}/auth/recover-password`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email: email })
                });

                if (!response.ok) {
                    throw new Error('No se pudo procesar la solicitud. Verifica el correo e intenta de nuevo.');
                }
                
                const data = await response.json();
                alert(data.message || `Si el correo ${email} está registrado, recibirás instrucciones enviadas a tu bandeja de entrada.`);
                
                // Formulate back to login
                btn.innerHTML = 'Instrucciones Enviadas';
                btn.style.background = 'var(--success)';
                btn.style.boxShadow = 'none';
                
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2500);

            } catch (error) {
                console.error(error);
                alert('No se pudo enviar el correo de recuperación.');
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }
});
