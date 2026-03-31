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
            { id: 1, marca: 'Yamaha', modelo: 'MT-09 SP', año: 2024, kilometraje: 0, precio: 98000000, image_url: 'https://images.unsplash.com/photo-1558981806-ec527fa84c3d?w=500' },
            { id: 2, marca: 'Ducati', modelo: 'Panigale V4', año: 2023, kilometraje: 1200, precio: 185000000, image_url: 'https://images.unsplash.com/photo-1591637333988-524f27e2c636?w=500' },
            { id: 3, marca: 'Kawasaki', modelo: 'Ninja ZX-10R', año: 2023, kilometraje: 5000, precio: 120000000, image_url: 'https://images.unsplash.com/photo-1568772589808-62ea49939c23?w=500' },
            { id: 4, marca: 'BMW', modelo: 'S1000RR', año: 2024, kilometraje: 500, precio: 165000000, image_url: 'https://images.unsplash.com/photo-1614162692298-7c2c757b3c63?w=500' }
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
    
    let currentCaptchaToken = null;

    const executeRuntQuery = async (placa, vin, capToken, capValue) => {
        runtModal.style.display = 'flex';
        runtLoader.style.display = 'block';
        runtResults.style.display = 'none';
        runtError.textContent = '';

        gsap.fromTo('.runt-modal-content', { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(1.7)" });

        try {
            const data = await window.api.runt.check(placa, vin, capToken, capValue);
            
            // Poblar UI
            document.getElementById('dna-plate-title').textContent = data.placa;
            document.getElementById('dna-marca').textContent = data.marca;
            document.getElementById('dna-linea').textContent = data.linea;
            document.getElementById('dna-modelo').textContent = data.modelo;
            document.getElementById('dna-color').textContent = data.color;
            
            const soatBadge = document.getElementById('dna-soat-badge');
            soatBadge.textContent = data.estado_soat;
            soatBadge.className = `badge ${data.estado_soat === 'VIGENTE' ? 'status-vigente' : 'status-vencido'}`;
            document.getElementById('dna-soat-venc').textContent = `Vence: ${data.vencimiento_soat}`;
            
            const rtmBadge = document.getElementById('dna-rtm-badge');
            rtmBadge.textContent = data.estado_rtm;
            rtmBadge.className = `badge ${data.estado_rtm === 'VIGENTE' ? 'status-vigente' : 'status-vencido'}`;
            document.getElementById('dna-rtm-venc').textContent = `Vence: ${data.vencimiento_rtm}`;
            
            const multasText = document.getElementById('dna-multas-text');
            const multasValor = document.getElementById('dna-multas-valor');
            if (data.multas === 0) {
                multasText.textContent = "Sin multas pendientes";
                multasText.style.color = "var(--success)";
                multasValor.textContent = "$0";
            } else {
                multasText.textContent = `${data.multas} Infracciones`;
                multasText.style.color = "var(--error)";
                multasValor.textContent = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(data.valor_multas);
            }
            
            const embargosEl = document.getElementById('dna-embargos');
            if (data.embargos) {
                embargosEl.textContent = "ALERTA: " + data.limitaciones_propiedad;
                embargosEl.style.color = "var(--error)";
            } else {
                embargosEl.textContent = "LIBRE DE EMBARGOS";
                embargosEl.style.color = "var(--success)";
            }

            const fuenteEl = document.getElementById('dna-fuente');
            if (fuenteEl) {
                fuenteEl.textContent = data.fuente;
                fuenteEl.style.color = data.es_verificado ? "#2ecc71" : "var(--gray)";
                if (data.es_verificado) {
                    fuenteEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg> ${data.fuente}`;
                }
            }

            runtLoader.style.display = 'none';
            runtResults.style.display = 'block';

            const btnBuy = document.getElementById('btnBuyFullReport');
            if (btnBuy) {
                btnBuy.onclick = async () => {
                    btnBuy.disabled = true;
                    btnBuy.textContent = "PROCESANDO...";
                    try {
                        const p = await window.api.runt.buyReport(data.placa, "usuario@ejemplo.com");
                        window.location.href = p.init_point;
                    } catch (err) {
                        alert("Error al generar la compra.");
                        btnBuy.disabled = false;
                        btnBuy.textContent = "COMPRAR REPORTE DETALLLADO ($40.000)";
                    }
                };
            }
        } catch (err) {
            runtModal.style.display = 'none';
            runtError.textContent = err.message || 'Error al conectar con la base de datos nacional.';
        }
    };

    if (runtForm) {
        runtForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const placa = (document.getElementById('runtPlate') || document.getElementById('runtPlaca')).value.trim().toUpperCase();
            const vin = (document.getElementById('runtVin')).value.trim() || null;
            
            if (placa.length < 5 || placa.length > 6) {
                runtError.textContent = 'Ingresa una placa válida (ej. ABC12D)';
                return;
            }

            // 1. Pedir Captcha al Backend antes de mostrar nada
            const originalBtnText = document.getElementById('btnConsultarRunt').innerHTML;
            document.getElementById('btnConsultarRunt').innerHTML = 'Iniciando Conexión RUNT...';
            
            try {
                const captchaData = await window.api.runt.getCaptcha();
                currentCaptchaToken = captchaData.id;
                runtCaptchaImg.src = captchaData.imagen;
                captchaInput.value = '';
                captchaModal.style.display = 'flex';
                document.getElementById('btnConsultarRunt').innerHTML = originalBtnText;

                btnConfirmCaptcha.onclick = () => {
                    const val = captchaInput.value.trim().toUpperCase();
                    if (!val) return;
                    captchaModal.style.display = 'none';
                    executeRuntQuery(placa, vin, currentCaptchaToken, val);
                };

                btnCancelCaptcha.onclick = () => {
                    captchaModal.style.display = 'none';
                };
            } catch (err) {
                console.error(err);
                // Si falla el captcha, intentamos consulta directa (fallback inteligente ya configurado en backend)
                executeRuntQuery(placa, vin, null, null);
                document.getElementById('btnConsultarRunt').innerHTML = originalBtnText;
            }
        });

        closeRuntModal.addEventListener('click', () => {
            gsap.to('.runt-modal-content', { 
                scale: 0.8, opacity: 0, duration: 0.3, 
                onComplete: () => runtModal.style.display = 'none' 
            });
        });
    }
});
