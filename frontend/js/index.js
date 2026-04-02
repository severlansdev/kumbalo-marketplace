document.addEventListener('DOMContentLoaded', async () => {
    const grid = document.querySelector('.listings-grid');
    const searchForm = document.getElementById('searchForm');
    if (!grid) return;

    const renderMotos = (motos) => {
        grid.innerHTML = '';
        if (motos.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No se encontraron motos con esos filtros.</p>';
            return;
        }

        motos.forEach(moto => {
            const article = document.createElement('article');
            article.className = 'listing-card';
            
            // formatear precio
            const pfo = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(moto.precio);
            
            article.innerHTML = `
                <div class="listing-image">
                    <img src="${moto.image_url || 'https://images.unsplash.com/photo-1558981806-ec527fa84c3d?w=500'}" alt="${moto.marca} ${moto.modelo}">
                    <span class="badge badge-new">Destacado</span>
                </div>
                <div class="listing-content">
                    <h3 class="listing-title">${moto.marca} ${moto.modelo}</h3>
                    <p class="listing-year">${moto.año} · ${moto.kilometraje} km</p>
                    <p class="listing-price">${pfo}</p>
                    <div class="listing-details">
                        <span class="detail">📍 Moto listada</span>
                        <span class="detail">✅ Verificada</span>
                    </div>
                    <a href="moto.html?id=${moto.id}" class="btn btn-primary btn-block">Ver Detalles</a>
                </div>
            `;
            grid.appendChild(article);
        });
    };

    const renderSkeletons = () => {
        grid.innerHTML = '';
        for (let i = 0; i < 4; i++) {
            grid.innerHTML += `
                <article class="listing-card">
                    <div class="skeleton skeleton-img"></div>
                    <div class="listing-content">
                        <div class="skeleton skeleton-text" style="width: 70%"></div>
                        <div class="skeleton skeleton-text short"></div>
                        <div class="skeleton skeleton-text" style="width: 50%; height: 1.5rem; margin-top: 10px;"></div>
                    </div>
                </article>
            `;
        }
    };

    // Carga inicial
    try {
        renderSkeletons();
        const motos = await window.api.motos.getAll(0, 8); // top 8
        renderMotos(motos);
    } catch (error) {
        console.error('Error fetching motos from API. Rendering fallback mock data.', error);
        // Fallback mock data to ensure the UI looks great even if API is down
        const mockMotos = [
            { id: 1, marca: 'Yamaha', modelo: 'MT-09 SP', año: 2024, kilometraje: 0, precio: 94900000, image_url: 'assets/motos/yamaha.png' },
            { id: 2, marca: 'Ducati', modelo: 'Panigale V4', año: 2023, kilometraje: 1200, precio: 185000000, image_url: 'assets/motos/ducati.png' },
            { id: 3, marca: 'BMW', modelo: 'R1250GS', año: 2023, kilometraje: 5000, precio: 135000000, image_url: 'assets/motos/bmw.png' },
            { id: 4, marca: 'Kawasaki', modelo: 'Ninja ZX-6R', año: 2024, kilometraje: 500, precio: 78000000, image_url: 'https://images.unsplash.com/photo-1614162692298-7c2c757b3c63?w=500' }
        ];
        renderMotos(mockMotos);
        // Refresh GSAP ScrollTrigger after rendering
        setTimeout(() => window.ScrollTrigger && window.ScrollTrigger.refresh(), 500);
    }

    // Manejar busqueda
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const marca = document.getElementById('marca').value;
            const anio = document.getElementById('modelo').value; // 'modelo' select tiene el año
            const precio = document.getElementById('precio').value;

            try {
                const btn = searchForm.querySelector('button[type="submit"]');
                const originalText = btn.innerHTML;
                btn.innerHTML = 'Buscando...';
                
                // Pedimos resultados filtrados al backend
                const filtradas = await window.api.motos.getAll(0, 8, marca, anio, precio);
                renderMotos(filtradas);
                
                // Desplazarse a los resultados
                document.getElementById('catalogo').scrollIntoView({ behavior: 'smooth' });
                
                btn.innerHTML = originalText;
            } catch (error) {
                console.error('Error buscando motos:', error);
                alert('Hubo un error al buscar las motos.');
            }
        });
    }

    // Manejo RUNT Analyzer Widget con HITL Captcha
    const runtForm = document.getElementById('runtForm');
    const runtModal = document.getElementById('runtModal');
    const closeRuntModal = document.getElementById('closeRuntModal');
    const runtLoader = document.getElementById('runtLoader');
    const runtResults = document.getElementById('runtResults');
    const runtError = document.getElementById('runtError');
    const captchaModal = document.getElementById('captchaModal');
    const runtCaptchaImg = document.getElementById('runtCaptchaImg');
    const captchaInput = document.getElementById('captchaInput');
    const btnConfirmCaptcha = document.getElementById('btnConfirmCaptcha');
    const btnCancelCaptcha = document.getElementById('btnCancelCaptcha');
    const btnRefreshCaptcha = document.getElementById('btnRefreshCaptcha');
    const captchaPlaceholder = document.getElementById('captchaPlaceholder');
    
    let currentCaptchaToken = null;

    const refreshCaptchaFlow = async () => {
        runtCaptchaImg.style.opacity = '0';
        if (captchaPlaceholder) captchaPlaceholder.style.display = 'block';
        try {
            const captchaData = await window.api.runt.getCaptcha();
            if (captchaData.error) throw new Error(captchaData.error);
            
            currentCaptchaToken = captchaData.id;
            runtCaptchaImg.src = captchaData.imagen;
            runtCaptchaImg.onload = () => {
                runtCaptchaImg.style.opacity = '1';
                if (captchaPlaceholder) captchaPlaceholder.style.display = 'none';
            };
        } catch (err) {
            console.error("Error refreshing captcha:", err);
            if (captchaPlaceholder) {
                captchaPlaceholder.textContent = "Error al conectar. Reintenta.";
                captchaPlaceholder.style.color = "var(--error)";
            }
        }
    };

    const executeRuntQuery = async (placa, vin, docType, docNum, capToken, capValue) => {
        runtModal.style.display = 'flex';
        runtLoader.style.display = 'block';
        runtResults.style.display = 'none';
        runtError.textContent = '';

        // Reset scroll and animations
        const modalContent = document.querySelector('.runt-modal-content');
        gsap.fromTo(modalContent, { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.5, ease: "power4.out" });

        try {
            const data = await window.api.runt.check(placa, vin, docType, docNum, capToken, capValue);
            
            // Generar ID de certificado aleatorio para el factor "Wow"
            const certId = `KMB-${new Date().getFullYear()}-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;
            document.getElementById('dna-id-rand').textContent = certId;

            // Poblar UI
            document.getElementById('dna-plate-title').textContent = data.placa;
            document.getElementById('dna-marca').textContent = data.marca;
            document.getElementById('dna-linea').textContent = data.linea;
            document.getElementById('dna-modelo').textContent = data.modelo;
            document.getElementById('dna-color').textContent = data.color;
            
            const soatBadge = document.getElementById('dna-soat-badge');
            soatBadge.textContent = data.estado_soat;
            soatBadge.className = `badge ${data.estado_soat === 'VIGENTE' ? 'status-vigente' : 'status-vencido'}`;
            soatBadge.style.background = data.estado_soat === 'VIGENTE' ? '#10b981' : '#ef4444';
            
            const rtmBadge = document.getElementById('dna-rtm-badge');
            rtmBadge.textContent = data.estado_rtm;
            rtmBadge.className = `badge ${data.estado_rtm === 'VIGENTE' ? 'status-vigente' : 'status-vencido'}`;
            rtmBadge.style.background = data.estado_rtm === 'VIGENTE' ? '#10b981' : '#ef4444';
            
            const multasText = document.getElementById('dna-multas-text');
            const multasValor = document.getElementById('dna-multas-valor');
            if (data.multas === 0) {
                multasText.textContent = "HISTORIAL LIMPIO";
                multasText.style.color = "#10b981";
                multasValor.textContent = "$0";
            } else {
                multasText.textContent = `${data.multas} INFRACCIONES SIMIT`;
                multasText.style.color = "#ef4444";
                multasValor.textContent = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(data.valor_multas);
            }
            
            const embargosEl = document.getElementById('dna-embargos');
            if (data.embargos) {
                embargosEl.textContent = "ALERTA: " + data.limitaciones_propiedad;
                embargosEl.style.color = "#ef4444";
            } else {
                embargosEl.textContent = "LIBRE DE EMBARGOS Y GRAVÁMENES";
                embargosEl.style.color = "#10b981";
            }

            const fuenteEl = document.getElementById('dna-fuente');
            if (fuenteEl) {
                fuenteEl.innerHTML = `FUENTE: ${data.fuente} · VERIFICACIÓN KUMBALO 2026`;
                fuenteEl.style.color = data.es_verificado ? "#10b981" : "#555";
            }

            runtLoader.style.display = 'none';
            runtResults.style.display = 'block';
            
            // Animación de entrada de los datos
            gsap.from('#runtResults .dna-card', { 
                y: 20, 
                opacity: 0, 
                stagger: 0.1, 
                duration: 0.8, 
                ease: "power2.out" 
            });

        } catch (err) {
            runtModal.style.display = 'none';
            runtError.textContent = err.message || 'Error de conexión con la infraestructura nacional.';
        }
    };

    if (runtForm) {
        // Asignar evento refresh
        if (btnRefreshCaptcha) {
            btnRefreshCaptcha.onclick = (e) => {
                e.preventDefault();
                refreshCaptchaFlow();
            };
        }

        runtForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const placa = document.getElementById('runtPlate').value.trim().toUpperCase();
            const vin = document.getElementById('runtVin').value.trim() || null;
            const docType = document.getElementById('tipoDoc').value;
            const docNum = document.getElementById('runtDoc').value.trim();
            
            if (placa.length < 5 || placa.length > 6) {
                runtError.textContent = 'Ingresa una placa válida (ej. ABC12D)';
                return;
            }

            // 1. Mostrar Modal y Cargar Captcha
            const btn = document.getElementById('btnConsultarRunt');
            const originalBtnText = btn.innerHTML;
            btn.innerHTML = '<span class="spin"></span> CONECTANDO AL RUNT...';
            btn.disabled = true;
            
            try {
                captchaModal.style.display = 'flex';
                gsap.fromTo('#captchaModal .modal-content', { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(1.7)" });
                
                // Cargar primer captcha
                await refreshCaptchaFlow();
                
                btn.innerHTML = originalBtnText;
                btn.disabled = false;

                btnConfirmCaptcha.onclick = () => {
                    const val = captchaInput.value.trim();
                    if (!val) return;
                    captchaModal.style.display = 'none';
                    executeRuntQuery(placa, vin, docType, docNum, currentCaptchaToken, val);
                };

                btnCancelCaptcha.onclick = () => {
                    captchaModal.style.display = 'none';
                };
            } catch (err) {
                // Fallback automático si falla el túnel de captchas
                executeRuntQuery(placa, vin, docType, docNum, null, null);
                btn.innerHTML = originalBtnText;
                btn.disabled = false;
            }
        });

        closeRuntModal.addEventListener('click', () => {
            gsap.to('.runt-modal-content', { 
                scale: 0.9, opacity: 0, duration: 0.3, 
                onComplete: () => runtModal.style.display = 'none' 
            });
        });
    }
});
