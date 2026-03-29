/**
 * KUMBALO - JavaScript con Animaciones Épicas GSAP
 * Inspirado en Ducati, Tesla, Ferrari y Triumph
 */

// GSAP ya está cargado globalmente desde el HTML
const { ScrollTrigger } = window;

// Registrar plugin
gsap.registerPlugin(ScrollTrigger);

// ============================================
// PAGE LOADER - Entrada épica tipo Tesla
// ============================================
const pageLoader = {
    init() {
        const loader = document.createElement('div');
        loader.className = 'page-loader';
        loader.innerHTML = `
            <div class="loader-content">
                <div class="loader-logo">
                    <span class="logo-icon brand-logo-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 48 48" fill="none">
                            <path d="M24 2L44 14V34L24 46L4 34V14Z" fill="#FF2800"/>
                            <path d="M24 6L40 16V32L24 42L8 32V16Z" fill="#0A0A0A"/>
                            <path d="M16 14V34H21V27L28 34H35L26 25L34 14H27L21 23V14Z" fill="#FF2800"/>
                        </svg>
                    </span>
                    <span class="logo-text">KUMBALO</span>
                </div>
                <div class="loader-bar">
                    <div class="loader-progress"></div>
                </div>
                <p class="loader-text">Iniciando experiencia...</p>
            </div>
        `;
        document.body.appendChild(loader);

        const tl = gsap.timeline({
            onComplete: () => {
                gsap.to(loader, {
                    duration: 0.8,
                    y: '-100%',
                    ease: 'power4.inOut',
                    onComplete: () => {
                        loader.style.display = 'none';
                        this.initHeroAnimation();
                    }
                });
            }
        });

        tl.from('.page-loader', {
            duration: 0,
            opacity: 0,
            ease: 'power4.inOut'
        })
        .from('.loader-logo', {
            duration: 1,
            y: -50,
            opacity: 0,
            ease: 'back.out(1.7)'
        })
        .from('.loader-bar', {
            duration: 0.8,
            scaleX: 0,
            transformOrigin: 'left',
            ease: 'power2.inOut'
        }, '-=0.5')
        .to('.loader-progress', {
            duration: 1.2,
            width: '100%',
            ease: 'power2.inOut'
        }, '+=0.2')
        .to('.loader-text', {
            duration: 0.5,
            opacity: 0.5,
            y: -10,
            ease: 'power2.out'
        }, '-=0.3');
    },

    initHeroAnimation() {
        animations.heroReveal();
    }
};

// ============================================
// HERO ANIMATIONS - Estilo Ferrari/Ducati
// ============================================
const animations = {
    heroReveal() {
        const tl = gsap.timeline();

        // Hero content stagger reveal
        tl.from('.hero-title', {
            duration: 2.5,
            y: 100,
            opacity: 0,
            ease: 'power4.out',
            skewY: 5,
            rotation: 2
        })
        .from('.hero-title .highlight', {
            duration: 0.8,
            scale: 1.5,
            opacity: 0,
            ease: 'back.out(1.7)',
            color: '#fff'
        }, '-=0.5')
        .from('.hero-subtitle', {
            duration: 1.8,
            y: 50,
            opacity: 0,
            ease: 'power3.out'
        }, '-=0.5')
        .from('.hero-buttons .btn', {
            duration: 1.5,
            y: 30,
            opacity: 0,
            stagger: 0.2,
            ease: 'power3.out'
        }, '-=0.8')
        .from('.hero-stats .stat', {
            duration: 1.5,
            y: 50,
            opacity: 0,
            stagger: 0.25,
            ease: 'power2.out',
            rotationX: -45
        }, '-=1');

        // Floating animation for hero title
        gsap.to('.hero-title', {
            y: 10,
            duration: 2,
            repeat: -1,
            yoyo: true,
            ease: 'sine.inOut'
        });

        // Gradient background animation
        gsap.to('.hero', {
            backgroundPosition: '100% 50%',
            duration: 20,
            repeat: -1,
            ease: 'none'
        });
    },

    // Listing cards - Estilo Ducati reveal
    cardsReveal() {
        const cards = document.querySelectorAll('.listing-card');

        cards.forEach((card, i) => {
            const tl = gsap.timeline({
                scrollTrigger: {
                    trigger: card,
                    start: 'top 85%',
                    end: 'top 60%',
                    toggleActions: 'play none none reverse'
                }
            });

            tl.from(card, {
                duration: 1,
                y: 100,
                opacity: 0,
                rotationY: -15,
                ease: 'power4.out',
                delay: i * 0.1
            })
            .from('.badge', {
                duration: 0.6,
                scale: 0,
                rotation: -180,
                ease: 'back.out(1.7)'
            }, '-=0.3');
        });
    },

    // Services section - Tesla style grid reveal
    servicesReveal() {
        const serviceCards = document.querySelectorAll('.service-card');

        serviceCards.forEach((card, i) => {
            gsap.from(card, {
                scrollTrigger: {
                    trigger: card,
                    start: 'top 85%',
                    toggleActions: 'play none none reverse'
                },
                duration: 1.2,
                y: 80,
                opacity: 0,
                rotationZ: i % 2 === 0 ? -5 : 5,
                ease: 'power4.out',
                delay: i * 0.15
            });

            // Icon pulse animation
            gsap.to(card.querySelector('.service-icon'), {
                duration: 2,
                scale: 1.1,
                repeat: -1,
                yoyo: true,
                ease: 'sine.inOut',
                delay: i * 0.3
            });
        });
    },

    // CTA section - Ferrari dramatic reveal
    ctaReveal() {
        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: '.cta',
                start: 'top 80%',
                end: 'top 60%',
                toggleActions: 'play none none reverse'
            }
        });

        tl.from('.cta h2', {
            duration: 1.5,
            y: 100,
            opacity: 0,
            ease: 'power4.out',
            scale: 0.8
        })
        .from('.cta p', {
            duration: 1,
            y: 50,
            opacity: 0,
            ease: 'power3.out'
        }, '-=0.8')
        .from('.cta-buttons .btn', {
            duration: 0.8,
            y: 30,
            opacity: 0,
            stagger: 0.2,
            ease: 'back.out(1.7)'
        }, '-=0.5');
    },

    // Contact form - Smooth reveal
    contactReveal() {
        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: '.contact',
                start: 'top 75%',
                toggleActions: 'play none none reverse'
            }
        });

        tl.from('.contact-info', {
            duration: 1.2,
            x: -100,
            opacity: 0,
            ease: 'power4.out'
        })
        .from('.contact-form', {
            duration: 1.2,
            x: 100,
            opacity: 0,
            ease: 'power4.out'
        }, '-=0.8')
        .from('.form-group', {
            duration: 0.6,
            y: 20,
            opacity: 0,
            stagger: 0.1,
            ease: 'power2.out'
        }, '-=0.5');
    },

    // Parallax images - Ducati style
    parallaxImages() {
        gsap.utils.toArray('.listing-image').forEach(image => {
            gsap.to(image.querySelector('img'), {
                scrollTrigger: {
                    trigger: image,
                    start: 'top bottom',
                    end: 'bottom top',
                    scrub: true
                },
                y: -30,
                ease: 'none'
            });
        });
    },

    // Text reveal animations
    textReveal() {
        const titles = document.querySelectorAll('.section-title');

        titles.forEach(title => {
            const text = title.textContent;
            title.innerHTML = text.split(' ').map(word => `<span class="word">${word}</span>`).join(' ');

            gsap.from(title.querySelectorAll('.word'), {
                scrollTrigger: {
                    trigger: title,
                    start: 'top 80%',
                    toggleActions: 'play none none reverse'
                },
                duration: 1,
                y: 100,
                opacity: 0,
                stagger: 0.1,
                ease: 'power4.out',
                rotationZ: 5
            });
        });
    },

    // Scroll progress indicator
    scrollProgress() {
        const progress = document.createElement('div');
        progress.className = 'scroll-progress';
        document.body.appendChild(progress);

        gsap.set(progress, { width: 0 });

        gsap.to(progress, {
            scrollTrigger: {
                trigger: 'body',
                start: 'top top',
                end: 'bottom bottom',
                scrub: true
            },
            width: '100%',
            ease: 'none'
        });
    },

    // Magnetic buttons - Tesla style
    magneticButtons() {
        const buttons = document.querySelectorAll('.btn, .btn-icon');

        buttons.forEach(btn => {
            btn.addEventListener('mouseenter', function() {
                gsap.to(this, {
                    duration: 0.3,
                    scale: 1.05,
                    ease: 'power2.out'
                });
            });

            btn.addEventListener('mouseleave', function() {
                gsap.to(this, {
                    duration: 0.3,
                    scale: 1,
                    ease: 'power2.out'
                });
            });
        });
    },

    // Logo animation on scroll
    logoAnimation() {
        const logo = document.querySelector('.logo');

        ScrollTrigger.create({
            start: 'top -100',
            end: 99999,
            onUpdate: (self) => {
                if (self.direction === 1) {
                    gsap.to(logo, { duration: 0.3, scale: 0.95, ease: 'power2.out' });
                } else {
                    gsap.to(logo, { duration: 0.3, scale: 1, ease: 'power2.out' });
                }
            }
        });
    },

    // Header Scroll Logic - Native functionality
    headerScroll() {
        const header = document.querySelector('.header');
        if (header) {
            window.addEventListener('scroll', () => {
                if (window.scrollY > 50) {
                    header.classList.add('scrolled');
                } else {
                    header.classList.remove('scrolled');
                }
            });
        }
    },

    // Sincronización de Autenticación en el Header
    syncHeaderAuth() {
        if (!window.api) return;
        
        const navButtons = document.querySelector('.nav-buttons');
        const mobileTabBar = document.querySelector('.mobile-tab-bar');
        
        if (!navButtons) return;

        if (window.api.isAuthenticated()) {
            // 1. Ocultar botones de Auth en el Header (Escritorio)
            const authLinks = navButtons.querySelectorAll('a[href="login.html"], a[href="registro.html"]');
            authLinks.forEach(link => {
                link.style.display = 'none';
                link.classList.add('hidden-auth');
            });

            // 2. Añadir botón de Dashboard si no existe
            if (!document.getElementById('header-dash-btn')) {
                const dashBtn = document.createElement('a');
                dashBtn.id = 'header-dash-btn';
                dashBtn.href = 'dashboard.html';
                dashBtn.className = 'btn btn-primary';
                dashBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px;"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
                    Mi Dashboard
                `;
                navButtons.insertBefore(dashBtn, navButtons.firstChild);
            }

            // 3. Actualizar Tab Bar Móvil (Perfil -> Dashboard)
            if (mobileTabBar) {
                const profileTab = mobileTabBar.querySelector('a[href="login.html"]');
                if (profileTab) {
                    profileTab.href = 'dashboard.html';
                    profileTab.querySelector('span').textContent = 'Dashboard';
                }
            }
        }
    }
};

// ============================================
// MOBILE MENU - Smooth animation
// ============================================
const mobileMenu = {
    init() {
        const btn = document.querySelector('#menuToggle') || document.querySelector('.mobile-menu-toggle');
        const menu = document.querySelector('#navMenu') || document.querySelector('.nav-menu');

        if (!btn || !menu) return;

        btn.addEventListener('click', function() {
            this.classList.toggle('active');
            menu.classList.toggle('active');

            // Animate menu items
            if (menu.classList.contains('active')) {
                gsap.from('#navMenu li', {
                    duration: 0.5,
                    x: 50,
                    opacity: 0,
                    stagger: 0.1,
                    ease: 'power3.out',
                    delay: 0.2
                });
            }
        });

        // Cerrar menú al hacer click en un enlace
        menu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                btn.classList.remove('active');
                menu.classList.remove('active');
            });
        });
    }
};

// ============================================
// SEARCH FORM - Smooth interactions
// ============================================
const searchForm = {
    init() {
        const form = document.querySelector('.search-form');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Animate form on submit
            gsap.to(this, {
                duration: 0.3,
                scale: 0.98,
                ease: 'power2.out',
                onComplete: () => {
                    gsap.to(this, {
                        duration: 0.3,
                        scale: 1,
                        ease: 'elastic.out(1, 0.3)'
                    });
                }
            });

            const params = new URLSearchParams();
            const marca = this.querySelector('#marca').value;
            const modelo = this.querySelector('#modelo').value;
            const precio = this.querySelector('#precio').value;

            if (marca) params.append('marca', marca);
            if (modelo) params.append('modelo', modelo);
            if (precio) params.append('precio', precio);

            window.location.href = '#catalogo?' + params.toString();
            showNotification('Buscando motos disponibles...', 'info');
        });
    }
};

// ============================================
// NOTIFICATION SYSTEM - Epic animations
// ============================================
function showNotification(message, type) {
    const existing = document.querySelector('.notification');
    if (existing) {
        gsap.to(existing, {
            duration: 0.3,
            x: 100,
            opacity: 0,
            onComplete: () => existing.remove()
        });
    }

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
            <span>${message}</span>
        </div>
    `;

    Object.assign(notification.style, {
        position: 'fixed',
        top: '80px',
        right: '20px',
        padding: '18px 30px',
        borderRadius: '12px',
        background: type === 'success' ? 'linear-gradient(135deg, #28a745, #20c997)' :
                    type === 'error' ? 'linear-gradient(135deg, #dc3545, #c82333)' :
                    'linear-gradient(135deg, #17a2b8, #138496)',
        color: 'white',
        zIndex: '9999',
        boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
        backdropFilter: 'blur(10px)',
        fontWeight: '600',
        fontSize: '1rem'
    });

    document.body.appendChild(notification);

    // Epic entrance
    gsap.from(notification, {
        duration: 0.6,
        x: 100,
        opacity: 0,
        rotation: 10,
        ease: 'back.out(1.7)'
    });

    // Exit animation
    gsap.to(notification, {
        delay: 5,
        duration: 0.5,
        x: 100,
        opacity: 0,
        rotation: -10,
        ease: 'power3.in',
        onComplete: () => notification.remove()
    });

    notification.addEventListener('click', () => {
        gsap.to(notification, {
            duration: 0.4,
            scale: 0.8,
            opacity: 0,
            onComplete: () => notification.remove()
        });
    });
}

// ============================================
// INITIALIZE ALL ANIMATIONS
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Page loader with hero reveal
    pageLoader.init();

    // Initialize all animations after a short delay
    setTimeout(() => {
        animations.cardsReveal();
        animations.servicesReveal();
        animations.ctaReveal();
        animations.contactReveal();
        animations.parallaxImages();
        animations.textReveal();
        animations.scrollProgress();
        animations.magneticButtons();
        animations.logoAnimation();
        animations.headerScroll();
        animations.syncHeaderAuth();
    }, 100);

    // Mobile menu
    mobileMenu.init();

    // Search form
    searchForm.init();

    // Contact form
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const nombre = formData.get('nombre');
            const email = formData.get('email');
            const mensaje = formData.get('mensaje');

            if (!nombre || !email || !mensaje) {
                showNotification('Por favor completa todos los campos', 'error');
                return;
            }

            console.log('Form submitted:', { nombre, email, mensaje });
            showNotification('¡Mensaje enviado! Te contactaremos pronto.', 'success');
            this.reset();

            // Form success animation
            gsap.to(this, {
                duration: 0.5,
                scale: 1.02,
                ease: 'elastic.out(1, 0.3)'
            });
        });
    }

    // Floating WhatsApp Button
    const fabButton = document.createElement('a');
    fabButton.href = 'https://wa.me/3001234567?text=Hola,%20necesito%20ayuda%20como%20usuario%20de%20Kumbalo.';
    fabButton.target = '_blank';
    fabButton.title = 'Soporte WhatsApp';
    fabButton.className = 'fab-whatsapp';
    fabButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 21l1.65-3.8a9 9 0 1 1 3.4 2.9L3 21" />
            <path d="M9 10a.5.5 0 0 0 1 0V9a.5.5 0 0 0-1 0v1a5 5 0 0 0 5 5h1a.5.5 0 0 0 0-1h-1a.5.5 0 0 0 0 1" />
        </svg>
    `;
    document.body.appendChild(fabButton);

    const fabStyle = document.createElement('style');
    fabStyle.textContent = `
        .fab-whatsapp {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #25D366;
            color: white;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(37, 211, 102, 0.3);
            z-index: 1000;
            transition: all 0.3s ease;
        }
        .fab-whatsapp:hover {
            transform: scale(1.1);
            background: #1ebc58;
            box-shadow: 0 6px 14px rgba(37, 211, 102, 0.4);
            color: white;
        }
        /* Responsiveness: Overlap prevention */
        @media (max-width: 768px) {
            .fab-whatsapp {
                bottom: 20px;
                right: 20px;
                width: 50px;
                height: 50px;
            }
        }
    `;
    document.head.appendChild(fabStyle);
    
    // Animate FAB entrance
    gsap.from('.fab-whatsapp', {
        scale: 0,
        opacity: 0,
        rotation: 360,
        duration: 1,
        delay: 2,
        ease: 'elastic.out(1, 0.5)'
    });

    // Listing cards interaction
    document.querySelectorAll('.listing-card').forEach(card => {
        card.addEventListener('click', function() {
            const title = this.querySelector('.listing-title').textContent;
            showNotification('Viendo detalles: ' + title, 'info');

            // Card press effect
            gsap.to(this, {
                duration: 0.2,
                scale: 0.98,
                ease: 'power2.out',
                onComplete: () => {
                    gsap.to(this, {
                        duration: 0.3,
                        scale: 1,
                        ease: 'elastic.out(1, 0.3)'
                    });
                }
            });
        });
    });
});
