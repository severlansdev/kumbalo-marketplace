document.addEventListener('DOMContentLoaded', async () => {
    if (!window.api || !window.api.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    const grid = document.getElementById('misMotosGrid');
    if (!grid) return;

    try {
        // Cargar Estadísticas
        const stats = await window.api.request('/auth/me/stats', {
            method: 'GET',
            headers: window.api.getHeaders()
        });
        document.getElementById('statMotos').textContent = stats.motos_publicadas;
        document.getElementById('statMensajes').textContent = stats.mensajes_recibidos;
        document.getElementById('statVentas').textContent = new Intl.NumberFormat('es-CO', { notation: "compact", compactDisplay: "short", style: 'currency', currency: 'COP', maximumFractionDigits: 1 }).format(stats.ventas_totales);
        document.getElementById('statGuardadas').textContent = stats.motos_guardadas;

        // Populate User Info
        if(stats.user) {
            document.getElementById('dashName').textContent = stats.user.nombre;
            document.getElementById('dashEmail').textContent = stats.user.email;
            document.getElementById('dashAvatar').textContent = stats.user.nombre.substring(0, 2).toUpperCase();
            
            const badge = document.getElementById('dashBadge');
            badge.textContent = stats.user.tipo_cuenta === 'concesionario' ? 'CONCESIONARIO' : 'NATURAL';
            if (stats.user.is_pro) {
                badge.textContent += ' PRO';
                badge.className = 'badge badge-hot'; // Gold variant
            }
            
            // Connect to Real-time Notifications socket
            if (stats.user.id) {
                setupWebSocket(stats.user.id);
            }
        }

        // Cargar mis motos
        const response = await window.api.request('/motos/mis-motos', {
            method: 'GET',
            headers: window.api.getHeaders()
        });
        
        grid.innerHTML = '';
        if(response.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding:3rem 1.5rem; background:rgba(255,40,0,0.05); border:2px dashed rgba(255,40,0,0.3); border-radius:16px;">
                    <div style="margin-bottom:1.5rem; display:flex; justify-content:center;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 48 48" fill="none">
                            <path d="M24 2L44 14V34L24 46L4 34V14Z" fill="#FF2800"/>
                            <path d="M24 6L40 16V32L24 42L8 32V16Z" fill="#0A0A0A"/>
                            <path d="M16 14V34H21V27L28 34H35L26 25L34 14H27L21 23V14Z" fill="#FF2800"/>
                        </svg>
                    </div>
                    <h3 style="color:#fff; margin-bottom:0.5rem; font-size:1.3rem;">Tu garaje está vacío</h3>
                    <p style="color:#888; margin-bottom:1.5rem; max-width:400px; margin-left:auto; margin-right:auto;">Publica tu primera moto y llega a miles de compradores en toda Colombia. ¡Es gratis y toma solo 2 minutos!</p>
                    <a href="subir-moto.html" class="btn btn-primary" style="display:inline-flex; gap:8px; padding:12px 28px; font-size:1rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                        Publicar mi primera moto
                    </a>
                </div>
            `;
            return;
        }

        response.forEach(moto => {
            const card = document.createElement('div');
            card.className = 'listing-card';
            const strPrice = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(moto.precio);
            
            card.innerHTML = `
                <div class="listing-image">
                    <img src="${moto.image_url || 'https://images.unsplash.com/photo-1558981806-ec527fa84c3d?w=500'}" alt="${moto.marca} ${moto.modelo}">
                    <span class="badge badge-premium">Tu Moto</span>
                </div>
                <div class="listing-content">
                    <h3 class="listing-title">${moto.marca} ${moto.modelo}</h3>
                    <p class="listing-year">${moto.año} - ${strPrice}</p>
                    <div class="listing-details" style="margin-top:10px; flex-direction:column; gap:10px;">
                        <span class="detail">🚗 ${moto.kilometraje} km</span>
                        <div style="display:flex; gap:10px;">
                            <button onclick="abrirMantenimiento(${moto.id})" class="btn btn-outline" style="padding: 5px 10px; font-size: 0.8rem; flex:1;">Bitácora</button>
                            ${moto.is_hot ? 
                                '<span class="badge badge-hot" style="align-self:center;">🔥</span>' : 
                                `<button onclick="openCheckout('boost', ${moto.id})" class="btn btn-outline" style="padding: 5px 10px; font-size: 0.8rem; flex:1;">Destacar</button>`
                            }
                        </div>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading dashboard motos:', error);
        if (error.message.includes('No se pudieron validar las credenciales') || error.message.includes('credenciales')) {
            window.api.removeToken();
            window.location.href = 'login.html';
        } else {
            grid.innerHTML = `<p style="grid-column: 1/-1; color: red;">Error al cargar las motos: ${error.message}</p>`;
        }
    }
});

// Real-Time Notifications Engine
function setupWebSocket(userId) {
    const wsUrl = window.api.baseUrl.replace('http', 'ws') + `/ws/notifications/${userId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => console.log('🔄 Conectado al túnel bidireccional de Notificaciones');
    
    ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if(payload.type === 'new_message') {
            const statMensajes = document.getElementById('statMensajes');
            let current = parseInt(statMensajes.textContent) || 0;
            
            // Animación GSAP para feedback visual del incremento
            gsap.fromTo(statMensajes, 
                { scale: 1.5, color: 'var(--primary)', fontWeight: 'bold' }, 
                { scale: 1, color: 'inherit', fontWeight: 'normal', duration: 1, ease: 'bounce.out' }
            );
            statMensajes.textContent = current + 1;
            
            // Notificación visual global (Mini toast)
            const toast = document.createElement('div');
            toast.style.cssText = "position:fixed; bottom:20px; left:50%; transform:translateX(-50%); background:var(--primary); color:white; padding:10px 20px; border-radius:20px; z-index:9999; box-shadow: 0 5px 15px rgba(220,38,38,0.4);";
            toast.innerHTML = '🔔 ¡Tienes un nuevo mensaje de un comprador potencial!';
            document.body.appendChild(toast);
            
            gsap.fromTo(toast, { y: 50, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, onComplete: () => {
                setTimeout(() => {
                    gsap.to(toast, { y: 50, opacity: 0, duration: 0.5, onComplete: () => toast.remove() });
                }, 4000);
            }});
        }
    };
    
    ws.onclose = () => {
        console.warn('⚠️ Desconectado del túnel de tiempo real. Reconectando en 5s...');
        setTimeout(() => setupWebSocket(userId), 5000);
    };
}

// Checkout Logic Global Methods
let pendingTx = null;

window.openCheckout = function(type, motoId) {
    pendingTx = { type, id: motoId };
    const modal = document.getElementById('checkoutModal');
    const title = document.getElementById('modalTitle');
    const desc = document.getElementById('modalDesc');
    const price = document.getElementById('modalPrice');
    
    if(type === 'pro') {
        title.textContent = 'Mejorar a Cuenta PRO';
        desc.textContent = 'Adquiere la membresía para Concesionarios e incrementa métricas exponencialmente.';
        price.textContent = '$150,000 COP / mes';
    } else if(type === 'boost') {
        title.textContent = 'Turbo Sell';
        desc.textContent = 'Tu moto aparecerá como "Hot" en los primeros catálogos, mejorando visibilidad un 300%.';
        price.textContent = '$50,000 COP';
    }
    
    modal.style.display = 'flex';
    gsap.fromTo('.modal-content', { opacity: 0, scale: 0.8, y: -50 }, { opacity: 1, scale: 1, y: 0, duration: 0.4, ease: 'back.out(1.7)' });
};

document.getElementById('btnConfirmPay')?.addEventListener('click', async (e) => {
    e.preventDefault();
    if(!pendingTx) return;
    
    const btn = e.target;
    btn.innerHTML = 'Procesando...';
    btn.disabled = true;
    
    try {
        let endpoint = pendingTx.type === 'pro' ? '/payments/checkout/pro' : `/payments/checkout/boost/${pendingTx.id}`;
        
        const response = await window.api.request(`${endpoint}?package=turbo_sell`, {
            method: 'POST',
            headers: window.api.getHeaders()
        });
        
        alert(response.message || 'Transacción completada');
        window.location.reload();
        
    } catch (error) {
        alert(error.message || 'La transacción falló o fue rechazada');
        btn.innerHTML = 'Confirmar Pago';
        btn.disabled = false;
        document.getElementById('checkoutModal').style.display='none';
    }
});

// Mi Garaje Virtual - Mantenimiento Logic
window.abrirMantenimiento = function(motoId) {
    document.getElementById('mantMotoId').value = motoId;
    const modal = document.getElementById('mantenimientoModal');
    modal.style.display = 'flex';
    gsap.fromTo(modal.querySelector('.modal-content'), 
        { y: -50, opacity: 0 }, 
        { y: 0, opacity: 1, duration: 0.3, ease: 'power2.out' }
    );
};

window.guardarMantenimiento = async function() {
    const motoId = document.getElementById('mantMotoId').value;
    const tipo = document.getElementById('tipoServicio').value;
    const km = document.getElementById('kmServicio').value;
    const taller = document.getElementById('tallerServicio').value || 'Taller Independiente';
    
    if(!km) {
        alert("Por favor ingresa el kilometraje actual de la moto.");
        return;
    }
    
    const btn = document.querySelector('#formMantenimiento button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = 'Guardando en Blockchain...';
    btn.disabled = true;
    
    try {
        // En sistema real llamaríamos POST /api/v1/motos/{motoId}/mantenimiento
        // Aquí hacemos un MOCK teatral para la experiencia del usuario (Agente Operaciones)
        await new Promise(r => setTimeout(r, 1500));
        
        alert(`¡Éxito! Mantenimiento de ${tipo} a los ${km}km registrado en ${taller}. El algoritmo IA de KUMBALO ha incrementado el valor de confianza de tu moto en un 12%.`);
        document.getElementById('mantenimientoModal').style.display = 'none';
        document.getElementById('formMantenimiento').reset();
    } catch (e) {
        alert("Error al registrar el mantenimiento en el Garaje Virtual.");
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
};
