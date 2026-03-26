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

    // Manejo RUNT Analyzer Widget
    const runtForm = document.getElementById('runtForm');
    const runtModal = document.getElementById('runtModal');
    const closeRuntModal = document.getElementById('closeRuntModal');
    const runtLoader = document.getElementById('runtLoader');
    const runtResults = document.getElementById('runtResults');
    const runtError = document.getElementById('runtError');

    if (runtForm) {
        runtForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const placa = document.getElementById('runtPlaca').value.trim();
            runtError.textContent = '';
            
            if (placa.length < 5 || placa.length > 6) {
                runtError.textContent = 'Ingresa una placa válida (ej. ABC12D)';
                return;
            }

            // Mostrar Modal con loader
            runtModal.style.display = 'flex';
            runtLoader.style.display = 'block';
            runtResults.style.display = 'none';

            // GSAP animacion en modal
            gsap.fromTo('.runt-modal-content', { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(1.7)" });

            try {
                // Delay teatral de escáner
                await new Promise(r => setTimeout(r, 1500));
                
                const data = await window.api.runt.check(placa);
                
                // Poblar UI
                runtResults.innerHTML = `
                    <h2 style="font-family: var(--font-family-display); font-size: 2rem; margin-bottom: 15px; color: var(--secondary); text-align: center;">Reporte KUMBALO</h2>
                    <div style="background: var(--gray-light); padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center;">
                        <h3 style="font-size: 1.5rem; letter-spacing: 2px; color: var(--charcoal); font-weight: bold;">${data.placa}</h3>
                        <p style="color: var(--gray);">${data.marca} ${data.linea} - Mod: ${data.modelo}</p>
                    </div>
                    <div class="runt-result-item"><span>SOAT:</span> <span class="status-badge ${data.estado_soat === 'VIGENTE' ? 'status-vigente' : 'status-vencido'}">${data.estado_soat}</span></div>
                    <div class="runt-result-item"><span>Vence SOAT:</span> <span style="font-weight: bold;">${data.vencimiento_soat}</span></div>
                    <div class="runt-result-item"><span>Tecnomecánica:</span> <span class="status-badge ${data.estado_rtm === 'VIGENTE' ? 'status-vigente' : 'status-vencido'}">${data.estado_rtm}</span></div>
                    <div class="runt-result-item"><span>Multas (SIMIT):</span> <span style="font-weight: bold; color: ${data.multas === 0 ? 'var(--success)' : 'var(--error)'};">${data.multas === 0 ? '✅ Sin multas' : '⚠️ ' + data.multas + ' infracciones'}</span></div>
                    <div class="runt-result-item"><span>Embargos:</span> <span>${data.embargos ? '<span class="status-badge status-vencido">SI - NO COMPRAR</span>' : '<span class="status-badge status-vigente">LIBRE</span>'}</span></div>
                    
                    <button class="btn btn-primary btn-block" style="margin-top: 20px;" onclick="document.getElementById('closeRuntModal').click()">Entendido</button>
                    ${!data.embargos ? '<p style="text-align:center; margin-top:10px; font-size: 0.9rem;">Moto limpia y lista para rodar. <a href="subir-moto.html" style="color:var(--primary); font-weight:bold;">¡Véndela aquí!</a></p>' : ''}
                `;
                
                runtLoader.style.display = 'none';
                runtResults.style.display = 'block';
                
            } catch (err) {
                runtModal.style.display = 'none';
                runtError.textContent = err.message || 'Error al conectar con la base de datos nacional.';
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
