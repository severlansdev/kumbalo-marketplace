/**
 * KUMBALO Sanitizer - XSS Prevention Utility
 * Provides safe DOM manipulation helpers to replace raw innerHTML usage.
 */
const sanitizer = {
    /**
     * Escape HTML special characters to prevent XSS
     * @param {string} str - Raw string to escape
     * @returns {string} - HTML-safe string
     */
    escapeHTML(str) {
        if (typeof str !== 'string') return String(str);
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
            '/': '&#x2F;'
        };
        return str.replace(/[&<>"'/]/g, char => map[char]);
    },

    /**
     * Create a text node (inherently safe from XSS)
     * @param {string} text - Text content
     * @returns {Text} - DOM text node
     */
    textNode(text) {
        return document.createTextNode(text);
    },

    /**
     * Safely set text content of an element (no HTML parsing)
     * @param {HTMLElement} element - Target element
     * @param {string} text - Text to set
     */
    setText(element, text) {
        if (element) element.textContent = text;
    },

    /**
     * Create an element with safe attributes and text
     * @param {string} tag - HTML tag name
     * @param {Object} attrs - Attributes to set
     * @param {string} textContent - Optional text content
     * @returns {HTMLElement}
     */
    createElement(tag, attrs = {}, textContent = '') {
        const el = document.createElement(tag);
        for (const [key, value] of Object.entries(attrs)) {
            if (key === 'style' && typeof value === 'object') {
                Object.assign(el.style, value);
            } else if (key === 'className') {
                el.className = value;
            } else if (key === 'dataset') {
                for (const [dataKey, dataVal] of Object.entries(value)) {
                    el.dataset[dataKey] = dataVal;
                }
            } else if (key.startsWith('on')) {
                // Skip event handlers in attrs for security
                continue;
            } else {
                el.setAttribute(key, value);
            }
        }
        if (textContent) el.textContent = textContent;
        return el;
    },

    /**
     * Safely render a moto card template using DOM APIs.
     * Use this instead of raw innerHTML for user-generated content.
     * @param {Object} moto - Moto data object
     * @returns {string} - Sanitized HTML string
     */
    motoCardHTML(moto) {
        const marca = this.escapeHTML(moto.marca || '');
        const modelo = this.escapeHTML(moto.modelo || '');
        const desc = this.escapeHTML(moto.descripcion || '');
        const imageUrl = this.escapeHTML(moto.image_url || 'https://images.unsplash.com/photo-1558981806-ec527fa84c3d?w=500');
        const year = parseInt(moto.año) || 'N/A';
        const km = parseInt(moto.kilometraje) || 0;
        const precio = new Intl.NumberFormat('es-CO', {
            style: 'currency', currency: 'COP', maximumFractionDigits: 0
        }).format(moto.precio || 0);

        return `
            <div class="listing-image">
                <img src="${imageUrl}" alt="${marca} ${modelo}" loading="lazy">
                ${moto.is_hot ? '<span class="badge badge-hot">🔥 HOT</span>' : ''}
            </div>
            <div class="listing-content">
                <h3 class="listing-title">${marca} ${modelo}</h3>
                <p class="listing-year">${year}</p>
                <div class="listing-details">
                    <span class="detail">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;">
                            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                        </svg>
                        ${km.toLocaleString()} km
                    </span>
                    <span class="detail listing-price">${precio}</span>
                </div>
            </div>
        `;
    },

    /**
     * Format user-friendly error messages
     * @param {Error|string} error - Error object or message
     * @returns {string} - User-friendly error message
     */
    friendlyError(error) {
        const msg = typeof error === 'string' ? error : (error?.message || '');
        
        const errorMap = {
            'Failed to fetch': '🔌 No pudimos conectar con el servidor. Verifica tu conexión a internet.',
            'NetworkError': '🌐 Problema de conexión. Intenta de nuevo en unos segundos.',
            'credenciales': '🔑 Tu sesión ha expirado. Por favor inicia sesión nuevamente.',
            '404': '🔍 No encontramos lo que buscabas. Intenta con otros filtros.',
            '500': '⚠️ Nuestro servidor tuvo un problema. Estamos trabajando en ello.',
            '429': '⏳ Demasiadas solicitudes. Espera un momento e intenta de nuevo.',
            '403': '🚫 No tienes permiso para realizar esta acción.',
        };

        for (const [key, friendlyMsg] of Object.entries(errorMap)) {
            if (msg.toLowerCase().includes(key.toLowerCase())) {
                return friendlyMsg;
            }
        }

        return '😕 Algo salió mal. Intenta de nuevo o contacta soporte por WhatsApp.';
    }
};

window.sanitizer = sanitizer;
