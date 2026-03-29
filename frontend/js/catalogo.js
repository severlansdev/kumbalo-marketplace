document.addEventListener('DOMContentLoaded', async () => {
    const grid = document.getElementById('catalogGrid');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const filterForm = document.getElementById('catalogFilterForm');
    const resultsCountText = document.getElementById('resultsCount');
    
    if (!grid) return;

    let currentPage = 0;
    const LIMIT = 9; // Mostrar de 9 en 9 para catalogo
    
    // Estado de filtros
    let currentMarca = '';
    let currentAnio = '';
    let currentPrecio = '';

    const renderMotos = (motos, append = false) => {
        if (!append) grid.innerHTML = '';
        
        if (motos.length === 0 && !append) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 2rem;">No se encontraron motos con los filtros aplicados. Intenta con otros rangos.</p>';
            loadMoreBtn.style.display = 'none';
            resultsCountText.textContent = `(0 encontradas)`;
            return;
        }

        motos.forEach(moto => {
            const article = document.createElement('article');
            article.className = 'listing-card';
            
            // GSAP Animacion Inicial (fade-in up para cada carta)
            article.style.opacity = 0;
            article.style.transform = 'translateY(20px)';
            
            // Formatear precio
            const pfo = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(moto.precio);
            
            article.innerHTML = `
                <div class="listing-image">
                    <img src="${moto.image_url || 'https://images.unsplash.com/photo-1558981806-ec527fa84c3d?w=500'}" alt="${moto.marca} ${moto.modelo}">
                    <span class="badge badge-new">${moto.kilometraje === 0 ? 'Nueva' : 'Usada'}</span>
                </div>
                <div class="listing-content">
                    <h3 class="listing-title">${moto.marca} ${moto.modelo}</h3>
                    <p class="listing-year">${moto.año} · ${new Intl.NumberFormat('es-CO').format(moto.kilometraje)} km</p>
                    <p class="listing-price">${pfo}</p>
                    <div class="listing-details">
                        <span class="detail">📍 Moto listada</span>
                        <span class="detail">✅ Verificada</span>
                    </div>
                    <a href="moto.html?id=${moto.id}" class="btn btn-primary btn-block">Ver Detalles</a>
                </div>
            `;
            grid.appendChild(article);

            // Animar la carta insertada
            gsap.to(article, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" });
        });

        // Ocultar botón "Ver más" si trajo menos del límite (asume que ya no hay más)
        if (motos.length < LIMIT) {
            loadMoreBtn.style.display = 'none';
        } else {
            loadMoreBtn.style.display = 'block';
        }
        
        resultsCountText.textContent = ''; // Limpiamos "Cargando..."
    };

    const renderSkeletons = () => {
        grid.innerHTML = '';
        for (let i = 0; i < LIMIT; i++) {
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

    const fetchPage = async (append = false) => {
        try {
            if (!append) {
                resultsCountText.textContent = '(Cargando...)';
                renderSkeletons();
            }
            
            const motos = await window.api.motos.getAll(currentPage * LIMIT, LIMIT, currentMarca, currentAnio, currentPrecio);
            renderMotos(motos, append);
        } catch (error) {
            console.error('Error fetching motos catalog:', error);
            if (!append) grid.innerHTML = '<p style="color:red; text-align:center; grid-column:1/-1;">Error de conexión con el servidor.</p>';
        }
    };

    // Filtros de barra lateral
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Leer filtros
            currentMarca = document.getElementById('marcaFilter').value;
            currentAnio = document.getElementById('anioFilter').value;
            currentPrecio = document.getElementById('precioFilter').value;
            
            // Resetear paginación
            currentPage = 0;
            const btnSubmit = filterForm.querySelector('button[type="submit"]');
            const originalText = btnSubmit.innerHTML;
            btnSubmit.innerHTML = 'Filtrando...';
            
            fetchPage(false).then(() => {
                btnSubmit.innerHTML = originalText;
            });
        });
    }

    // Botón Ver Más
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            currentPage++;
            loadMoreBtn.innerHTML = 'Cargando...';
            loadMoreBtn.disabled = true;
            
            fetchPage(true).then(() => {
                loadMoreBtn.innerHTML = 'Ver Más Motos';
                loadMoreBtn.disabled = false;
            });
        });
    }

    // Inicializar Catalog
    fetchPage(false);
});
