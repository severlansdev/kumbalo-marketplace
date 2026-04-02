document.addEventListener('DOMContentLoaded', async () => {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const content = document.getElementById('motoContent');

    // Get ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const motoId = urlParams.get('id');

    if (!motoId) {
        loadingState.style.display = 'none';
        errorState.style.display = 'block';
        return;
    }

    try {
        const moto = await window.api.motos.getById(motoId);
        
        // Formatear precio y fecha
        const pfo = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(moto.precio);
        const fecha = new Date(moto.created_at).toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });

        // Llenar datos en el DOM
        document.getElementById('pageTitle').textContent = `${moto.marca} ${moto.modelo} - KUMBALO`;
        document.getElementById('ogTitle').content = `${moto.marca} ${moto.modelo} por ${pfo}`;
        
        document.getElementById('motoTitle').textContent = `${moto.marca} ${moto.modelo}`;
        document.getElementById('motoPrice').textContent = pfo;
        document.getElementById('specYear').textContent = moto.año;
        document.getElementById('specKm').textContent = `${new Intl.NumberFormat('es-CO').format(moto.kilometraje)} km`;
        document.getElementById('specBrand').textContent = moto.marca.toUpperCase();
        document.getElementById('motoDate').textContent = fecha;
        document.getElementById('motoDesc').textContent = moto.descripcion;
        
        // --- Calculadora de Crédito ---
        const selectPlazo = document.getElementById('plazoCredito');
        const renderCuotaMensual = () => {
            const n = parseInt(selectPlazo.value) || 48;
            const P = moto.precio;
            // Tasa Efectiva Anual 22% -> Tasa Mes Vencido ~1.67%
            const r = Math.pow(1 + 0.22, 1/12) - 1;
            const cuota = P * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
            
            const cuotaFormat = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(cuota);
            document.getElementById('cuotaMensual').textContent = cuotaFormat + '/mes';
        };
        renderCuotaMensual();
        selectPlazo.addEventListener('change', renderCuotaMensual);
        // ------------------------------
        
        const imageUrl = moto.image_url || 'https://images.unsplash.com/photo-1558981806-ec527fa84c3d?w=500';
        document.getElementById('ogImage').content = imageUrl;

        // Render Swiper Slides (Dynamic local premium assets)
        const wrapper = document.getElementById('swiperWrapper');
        const getBrandImage = (marca) => {
            const m = marca.toLowerCase();
            if (m.includes('yamaha')) return '/assets/motos/yamaha.png';
            if (m.includes('ducati')) return '/assets/motos/ducati.png';
            if (m.includes('bmw')) return '/assets/motos/bmw.png';
            return '/assets/motos/yamaha.png'; // Fallback
        };

        const premiumImg = getBrandImage(moto.marca);
        wrapper.innerHTML = `
            <div class="swiper-slide">
                <img src="${premiumImg}" alt="${moto.marca} ${moto.modelo}">
            </div>
            <div class="swiper-slide">
                <img src="${premiumImg}" alt="Vista lateral Premium" style="filter: brightness(1.1);">
            </div>
            <div class="swiper-slide">
                <img src="${premiumImg}" alt="Detalle Kumbalo" style="filter: saturate(1.2);">
            </div>
        `;

        // Initializes Swiper with Touch Swipes (Robust Initialization)
        const swiperContainer = document.querySelector('.moto-swiper');
        const swiperCount = wrapper.querySelectorAll('.swiper-slide').length;
        
        if (swiperCount > 1) {
            new Swiper('.moto-swiper', {
                loop: true,
                pagination: {
                    el: '.swiper-pagination',
                    clickable: true,
                },
                navigation: {
                    nextEl: '.swiper-button-next',
                    prevEl: '.swiper-button-prev',
                },
                autoplay: {
                    delay: 4000,
                    disableOnInteraction: false,
                },
                effect: 'fade',
                fadeEffect: {
                    crossFade: true
                }
            });
        } else {
            // Display as static image if only one slide
            const nextBtn = document.querySelector('.swiper-button-next');
            const prevBtn = document.querySelector('.swiper-button-prev');
            const pagination = document.querySelector('.swiper-pagination');
            
            if (nextBtn) nextBtn.style.display = 'none';
            if (prevBtn) prevBtn.style.display = 'none';
            if (pagination) pagination.style.display = 'none';
            
            // Ensure visibility without carousel logic
            swiperContainer.style.overflow = 'visible';
        }

        document.getElementById('motoBadge').textContent = moto.kilometraje === 0 ? 'NUEVA' : 'USADA';

        // Lógica Contactar (Whatsapp MOCK)
        document.getElementById('btnContactar').addEventListener('click', () => {
            const mensaje = `Hola, vengo de Kumbalo. Estoy interesado en tu ${moto.marca} ${moto.modelo} listada en ${pfo}.`;
            const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
            window.open(whatsappUrl, '_blank');
        });

        // Mostrar contenido
        loadingState.style.display = 'none';
        content.style.display = 'grid';

        // Lógica Favoritos
        const btnFavorito = document.getElementById('btnFavorito');
        if (btnFavorito) {
            // Al hacer clic
            btnFavorito.addEventListener('click', async () => {
                if (!window.api.isAuthenticated()) {
                    alert('Debes iniciar sesión para guardar favoritos.');
                    window.location.href = 'login.html';
                    return;
                }
                
                try {
                    const res = await window.api.favoritos.toggle(motoId);
                    if (res.status === 'added') {
                        btnFavorito.innerHTML = '<i class="ti ti-heart-filled" style="color: red;"></i> En Favoritos';
                    } else {
                        btnFavorito.innerHTML = '<i class="ti ti-heart"></i> Guardar en Favoritos';
                    }
                } catch (error) {
                    console.error('Error al guardar favorito:', error);
                    alert('No se pudo guardar la moto a favoritos.');
                }
            });
            
            // Si estuviéramos guardando el estado inicial, podríamos chequearlo aquí,
            // pero por simplicidad permitimos que el toggle haga el descubrimiento.
        }

        // Lógica de Mensajería Interna
        const btnContactar = document.getElementById('btnContactar');
        const contactModal = document.getElementById('contactModal');
        const btnCancelContact = document.getElementById('btnCancelContact');
        const contactFormInternal = document.getElementById('contactFormInternal');

        if (btnContactar && contactModal) {
            btnContactar.addEventListener('click', () => {
                if (!window.api.isAuthenticated()) {
                    alert('Debes iniciar sesión para contactar al vendedor.');
                    window.location.href = 'login.html';
                    return;
                }
                contactModal.style.display = 'flex';
                // GSAP Animación simple para el modal
                gsap.fromTo(contactModal.querySelector('.modal-content'), 
                    { y: -50, opacity: 0 }, 
                    { y: 0, opacity: 1, duration: 0.3, ease: 'power2.out' }
                );
            });

            btnCancelContact.addEventListener('click', () => {
                contactModal.style.display = 'none';
            });

            contactFormInternal.addEventListener('submit', async (e) => {
                e.preventDefault();
                const contenido = document.getElementById('mensajeContenido').value;
                
                try {
                    await window.api.mensajes.create({
                        contenido: contenido,
                        moto_id: motoId,
                        destinatario_id: moto.propietario_id
                    });
                    alert('Mensaje enviado con éxito');
                    contactModal.style.display = 'none';
                    contactFormInternal.reset();
                } catch (error) {
                    console.error('Error enviando mensaje:', error);
                    alert('Hubo un error al enviar el mensaje');
                }
            });
        }

        // --- Lógica Fintech y Nuevos Negocios ---
        const btnCreditPreapproval = document.getElementById('btnCreditPreapproval');
        if (btnCreditPreapproval) {
            btnCreditPreapproval.addEventListener('click', async () => {
                if (!window.api.isAuthenticated()) {
                    alert('Debes iniciar sesión para solicitar preaprobación de crédito.');
                    window.location.href = 'login.html';
                    return;
                }
                const originalText = btnCreditPreapproval.innerHTML;
                btnCreditPreapproval.innerHTML = '<i class="ti ti-loader ti-spin"></i> Procesando...';
                try {
                    const plazo = document.getElementById('plazoCredito').value;
                    await window.api.business.solicitarCredito({
                        moto_id: motoId,
                        monto_solicitado: moto.precio,
                        plazo_meses: parseInt(plazo) || 48,
                        ingresos_mensuales: 0 // Mock field since we don't ask in the UI yet
                    });
                    alert('¡Solicitud enviada a Bancolombia Sufi! Un asesor te contactará pronto.');
                } catch (error) {
                    console.error('Error credito:', error);
                    alert('Ocurrió un error al procesar tu solicitud de crédito.');
                } finally {
                    btnCreditPreapproval.innerHTML = originalText;
                }
            });
        }

        const btnCotizarSeguro = document.getElementById('btnCotizarSeguro');
        if (btnCotizarSeguro) {
            btnCotizarSeguro.addEventListener('click', async () => {
                if (!window.api.isAuthenticated()) {
                    alert('Debes iniciar sesión para cotizar tu seguro Todo Riesgo.');
                    window.location.href = 'login.html';
                    return;
                }
                const originalText = btnCotizarSeguro.innerHTML;
                btnCotizarSeguro.innerHTML = '<i class="ti ti-loader ti-spin"></i> Cotizando con Sura...';
                try {
                    await window.api.business.cotizarSeguro({
                        moto_id: motoId,
                        tipo_seguro: "Todo Riesgo"
                    });
                    alert('¡Solicitud de cotización con SURA enviada con éxito! Revisarás la oferta en tu correo.');
                } catch (error) {
                    console.error('Error seguro:', error);
                    alert('Ocurrió un error al cotizar el seguro. Intenta de nuevo.');
                } finally {
                    btnCotizarSeguro.innerHTML = originalText;
                }
            });
        }

        const btnOfrecerPermuta = document.getElementById('btnOfrecerPermuta');
        if (btnOfrecerPermuta) {
            btnOfrecerPermuta.addEventListener('click', async () => {
                if (!window.api.isAuthenticated()) {
                    alert('Debes iniciar sesión para ofrecer un intercambio.');
                    window.location.href = 'login.html';
                    return;
                }
                const ofId = prompt("Ingresa el ID de la moto de TU GARAJE que deseas ofrecer en permuta:");
                if (!ofId) return;
                
                const excedente = prompt("Ingresa el valor (COP) que darás como excedente (0 si es mano a mano):", "0");
                if (excedente === null) return;
                
                const originalText = btnOfrecerPermuta.innerHTML;
                btnOfrecerPermuta.innerHTML = '<i class="ti ti-loader ti-spin"></i> Enviando Oferta...';
                try {
                    await window.api.request('/v1/business/permutas/ofrecer', {
                        method: 'POST',
                        headers: window.api.getHeaders(),
                        body: JSON.stringify({
                            moto_ofrecida_id: parseInt(ofId),
                            moto_objetivo_id: motoId,
                            excedente: parseFloat(excedente)
                        })
                    });
                    alert('¡Oferta de permuta enviada con éxito! El vendedor decidirá si acepta el Smart Trade-In con Escrow Dual.');
                } catch (error) {
                    console.error('Error permutas:', error);
                    alert('Ocurrió un error al enviar tu oferta de permuta: ' + error.message);
                } finally {
                    btnOfrecerPermuta.innerHTML = originalText;
                }
            });
        }

    } catch (error) {
        console.error('Error fetched moto details:', error);
        loadingState.style.display = 'none';
        errorState.style.display = 'block';
    }
});
