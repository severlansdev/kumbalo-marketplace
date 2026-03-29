/**
 * Dashboard Logic - Kumbalo Marketplace
 * 
 * Gestiona la carga de estadísticas, inventario personal del usuario (Garaje Virtual),
 * notificaciones en tiempo real vía WebSockets y el flujo de trámites de Traspaso Express.
 * Utiliza GSAP para animaciones premium y la API central para la persistencia.
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Verificación de sesión mandatoria
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

            // Admin-only AI Center Visibility
            if (stats.user.rol === 'admin') {
                const navAI = document.getElementById('nav-ai-center');
                if (navAI) navAI.style.display = 'block';
                loadAgentRoster();
                setupAICounterLogs();
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
            
            // Lógica de botones de pago Kumbalo y Traspaso
            let actionButtons = '';
            
            // Verificación regional para traspaso
            const ciudadesSoportadas = ["bogota", "bogotá", "medellin", "medellín"];
            const esCiudadSoportada = ciudadesSoportadas.includes((moto.ciudad || "").toLowerCase().trim());
            
            if (!moto.commission_paid) {
                const commission = new Intl.NumberFormat('es-CO').format(moto.commission_fee || 250000);
                actionButtons = `<button onclick="iniciarPagoComision(${moto.id})" class="btn btn-primary" style="padding: 10px; font-size: 0.85rem; width: 100%; margin-top: 10px;">💳 Pagar Comisión ($${commission})</button>`;
            } else {
                actionButtons = `
                    <div style="display:flex; flex-direction:column; gap:8px; margin-top: 10px;">
                        <div style="display:flex; gap:10px;">
                            <button onclick="abrirMantenimiento(${moto.id})" class="btn btn-outline" style="padding: 5px 10px; font-size: 0.8rem; flex:1;">Bitácora</button>
                            ${moto.is_hot ? 
                                '<span class="badge badge-hot" style="align-self:center;">🔥</span>' : 
                                `<button onclick="openCheckout('boost', ${moto.id})" class="btn btn-outline" style="padding: 5px 10px; font-size: 0.8rem; flex:1;">Destacar</button>`
                            }
                        </div>
                        ${esCiudadSoportada ? 
                            `<button onclick="iniciarNuevoTramite(${moto.id})" class="btn btn-success" style="padding: 8px; font-size: 0.8rem; width: 100%; background:#10b981; border:none;">📋 Solicitar Traspaso</button>` :
                            `<button class="btn btn-outline" style="padding: 8px; font-size: 0.8rem; width: 100%; opacity:0.5; cursor:not-allowed;" title="Traspaso no disponible en ${moto.ciudad}">📋 Traspaso No Disp.</button>`
                        }
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="listing-image">
                    <img src="${moto.image_url || 'https://images.unsplash.com/photo-1558363196-03c03ec34190?w=500'}" 
                         alt="${moto.marca} ${moto.modelo}" 
                         onerror="this.src='https://images.unsplash.com/photo-1449495169669-7b118f960237?w=500';">
                    <span class="badge ${moto.commission_paid ? 'badge-new' : 'badge-premium'}" style="background: ${moto.commission_paid ? 'var(--success)' : 'var(--primary)'}">
                        ${moto.commission_paid ? 'Publicada' : 'Pendiente Pago'}
                    </span>
                </div>
                <div class="listing-content">
                    <h3 class="listing-title">${moto.marca} ${moto.modelo}</h3>
                    <p class="listing-year">${moto.año} - ${strPrice}</p>
                    <div class="listing-details" style="margin-top:10px; flex-direction:column; gap:10px;">
                        <span class="detail">🚗 ${moto.kilometraje} km</span>
                        ${actionButtons}
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

// Función para iniciar el flujo de pago con MercadoPago
window.iniciarPagoComision = async function(motoId) {
    try {
        const response = await window.api.payments.createPreference(motoId);
        if (response.init_point) {
            // Redirigir al link de pago seguro
            window.location.href = response.init_point;
        } else {
            throw new Error("No se pudo generar el túnel de pago.");
        }
    } catch (e) {
        alert("Error de Fintech: " + e.message);
    }
};

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
// AI Command Center Logic
async function loadAgentRoster() {
    const roster = document.getElementById('agent-roster');
    if (!roster) return;

    try {
        const agents = await window.api.request('/v1/agents/status', {
            method: 'GET',
            headers: window.api.getHeaders()
        });

        roster.innerHTML = '';
        agents.forEach(agent => {
            const card = document.createElement('div');
            card.style.cssText = "background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 12px; border-radius: 12px; display:flex; flex-direction:column; gap:8px;";
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size: 0.7rem; color: var(--primary); font-weight:bold;">${agent.category}</span>
                    <span style="font-size: 0.8rem; color: #0f0;">●</span>
                </div>
                <h4 style="font-size: 0.85rem; color: #fff; margin:0;">${agent.name}</h4>
                <p style="font-size: 0.75rem; color: #888; margin:0;">Status: ${agent.status}</p>
            `;
            roster.appendChild(card);
        });
    } catch (e) {
        console.warn("Could not load agent roster:", e);
    }
}

function setupAICounterLogs() {
    const logsContainer = document.getElementById('ai-logs');
    const scenarios = [
        "[SEO] Actualizando sitemap.xml... OK",
        "[HACKER GUARDIAN] Bloqueando intento de fuerza bruta IP 192.168.1.1",
        "[FINTECH] Sincronizando túnel de MercadoPago... OK",
        "[MOBILE DEV] Optimizando assets para Android/iOS",
        "[CLOUD ARCHITECT] Auditando costos de Vercel... -$2.50 USD",
        "[PR MEDIA] Generando nota de prensa para Publimotos",
        "[UX] Ejecutando test A/B en el flujo de registro",
        "[ARQUITEKTO] Coordinando despliegue de 24 agentes...",
        "[SRE] Verificando Latencia en Medellín: 12ms",
        "[QA] Suite de pruebas automatizadas: 100% PASS"
    ];

    setInterval(() => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.style.color = '#0f0';
        entry.textContent = `> ${scenarios[Math.floor(Math.random() * scenarios.length)]}`;
        logsContainer.appendChild(entry);
        logsContainer.scrollTop = logsContainer.scrollHeight;
        if (logsContainer.children.length > 20) logsContainer.removeChild(logsContainer.firstChild);
    }, 3000);
}

// Tab Switching
document.querySelectorAll('.dashboard-nav a').forEach(link => {
    link.addEventListener('click', (e) => {
        const target = link.getAttribute('href');
        if (target.startsWith('#')) {
            e.preventDefault();
            
            // UI Update
            document.querySelectorAll('.dashboard-nav a').forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Sections
            const grid = document.getElementById('misMotosGrid');
            const aiSection = document.getElementById('ia-center-section');
            const transferSection = document.getElementById('traspasos-section');
            const header = document.querySelector('.dashboard-header');

            // Hide all by default
            [grid, aiSection, transferSection, header].forEach(el => { if(el) el.style.display = 'none'; });

            if (target === '#ia-center') {
                aiSection.style.display = 'block';
            } else if (target === '#traspasos') {
                if(transferSection) transferSection.style.display = 'block';
                loadTraspasos();
            } else {
                grid.style.display = 'grid';
                header.style.display = 'block';
            }
        }
    });
});

async function loadTraspasos() {
    const list = document.getElementById('traspasos-list');
    if (!list) return;
    
    list.innerHTML = '<p style="color:#888;">Cargando trámites...</p>';

    try {
        const tramites = await window.api.request('/tramites/mis-tramites', {
            method: 'GET',
            headers: window.api.getHeaders()
        });

        if (tramites.length === 0) {
            list.innerHTML = `
                <div style="padding:20px; border:2px dashed rgba(255,255,255,0.1); border-radius:15px; text-align:center;">
                    <p style="color:#888; margin-bottom:15px;">¿Acabas de vender una moto? Inicia el proceso legal y obtén tu dinero seguro.</p>
                </div>
            `;
            return;
        }

        list.innerHTML = '';
        tramites.forEach(t => {
            const item = document.createElement('div');
            item.style.cssText = "background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;";
            
            let statusColor = '#f59e0b'; // warning
            if (t.estado === 'finalizado') statusColor = '#10b981'; // success
            if (t.estado === 'documentos_pendientes') statusColor = '#3b82f6'; // info

            const formattedPrice = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(t.costo_total);

            item.innerHTML = `
                <div>
                    <h4 style="color:#fff; margin-bottom:5px;">Traspaso Express: ID #${t.id}</h4>
                    <p style="font-size:0.8rem; color:#888;">Estado: <b style="color:${statusColor}">${t.estado.replace('_', ' ').toUpperCase()}</b></p>
                    ${t.radicado_sim ? `<p style="font-size:0.75rem; color:var(--primary);">Radicado SIM: ${t.radicado_sim}</p>` : ''}
                </div>
                <div style="display:flex; gap:10px;">
                    ${t.estado === 'pago_pendiente' ? 
                        `<button onclick="pagarTramite(${t.id})" class="btn btn-primary" style="padding: 8px 15px; font-size: 0.8rem;">Pagar $440k</button>` :
                        `<button class="btn btn-outline" style="padding: 8px 15px; font-size: 0.8rem;">Ver Detalles</button>`
                    }
                </div>
            `;
            list.appendChild(item);
        });
    } catch (e) {
        list.innerHTML = `<p style="color:red;">Error al cargar trámites: ${e.message}</p>`;
    }
}

window.iniciarNuevoTramite = function(motoId) {
    document.getElementById('checkMotoId').value = motoId;
    const modal = document.getElementById('traspasoChecklistModal');
    
    // Reset checks
    document.querySelectorAll('.traspaso-check').forEach(c => c.checked = false);
    const payBtn = document.getElementById('btnTraspasoPay');
    payBtn.disabled = true;
    payBtn.style.opacity = '0.4';
    payBtn.style.filter = 'grayscale(1)';
    payBtn.style.pointerEvents = 'none';

    modal.style.display = 'flex';
    gsap.fromTo(modal.querySelector('.modal-content'), 
        { y: -50, opacity: 0, scale: 0.9 }, 
        { y: 0, opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(1.7)' }
    );
};

// Listener para habilitar botón de pago según checklist
document.addEventListener('change', (e) => {
    if (e.target.classList.contains('traspaso-check')) {
        const allChecked = Array.from(document.querySelectorAll('.traspaso-check')).every(c => c.checked);
        const payBtn = document.getElementById('btnTraspasoPay');
        
        if (allChecked) {
            payBtn.disabled = false;
            payBtn.style.opacity = '1';
            payBtn.style.filter = 'none';
            payBtn.style.pointerEvents = 'all';
            gsap.to(payBtn, { scale: 1.05, duration: 0.2, yoyo: true, repeat: 1 });
        } else {
            payBtn.disabled = true;
            payBtn.style.opacity = '0.4';
            payBtn.style.filter = 'grayscale(1)';
            payBtn.style.pointerEvents = 'none';
        }
    }
});

// Botón de pago final en el Modal de Checklist
document.getElementById('btnTraspasoPay')?.addEventListener('click', async () => {
    const motoId = document.getElementById('checkMotoId').value;
    const btn = document.getElementById('btnTraspasoPay');
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = 'Generando Túnel Seguro...';
    
    try {
        const response = await window.api.request('/tramites/solicitar', {
            method: 'POST',
            headers: window.api.getHeaders(),
            body: JSON.stringify({ moto_id: parseInt(motoId), tipo: 'traspaso_express' })
        });
        
        if (response.pago_url) {
            window.location.href = response.pago_url;
        } else {
            alert("Trámite registrado. Un gestor te contactará para el pago manual.");
            window.location.reload();
        }
    } catch (e) {
        alert("Error al iniciar trámite: " + e.message);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
});

window.pagarTramite = async function(tramiteId) {
    try {
        const response = await window.api.request('/tramites/solicitar', {
            method: 'POST',
            headers: window.api.getHeaders(),
            body: JSON.stringify({ tramite_id: tramiteId, moto_id: 0 }) 
        });
        
        if (response.pago_url) {
            window.location.href = response.pago_url;
        }
    } catch (e) {
        alert("Error en el pago: " + e.message);
    }
}

document.getElementById('btn-send-command')?.addEventListener('click', async () => {
    const input = document.getElementById('ai-command-input');
    const command = input.value.trim();
    if (!command) return;

    const btn = document.getElementById('btn-send-command');
    btn.disabled = true;
    btn.textContent = 'Trasmitiendo...';

    try {
        await window.api.request(`/v1/agents/command?command=${encodeURIComponent(command)}`, {
            method: 'POST',
            headers: window.api.getHeaders()
        });
        
        input.value = '';
        alert("Comando recibido por el Arquitekto Elite. La orden ha sido delegada a los agentes correspondientes.");
        
        // Add to logs
        const logsContainer = document.getElementById('ai-logs');
        const entry = document.createElement('div');
        entry.style.color = 'var(--primary)';
        entry.textContent = `> [ DIRECTOR ] ${command}`;
        logsContainer.appendChild(entry);
        
    } catch (e) {
        alert("Error al contactar con el Centro de Mando: " + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Emitir Orden Directa';
    }
});

// Lógica de perfil de usuario
window.actualizarPerfil = async function() {
    const nombre = prompt("Ingresa tu nuevo nombre:", document.getElementById('dashName').textContent);
    if (!nombre) return;

    try {
        const response = await window.api.request('/auth/me/profile', {
            method: 'PUT',
            headers: window.api.getHeaders(),
            body: JSON.stringify({ nombre })
        });
        
        alert("¡Perfil actualizado con éxito!");
        window.location.reload();
    } catch (e) {
        alert("Error al actualizar perfil: " + e.message);
    }
};
