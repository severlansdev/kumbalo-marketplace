const API_URL = '/api';

const api = {
    baseUrl: window.location.origin + API_URL,
    // Manejo de tokens JWT
    getToken: () => localStorage.getItem('kumbalo_token'),
    setToken: (token) => localStorage.setItem('kumbalo_token', token),
    removeToken: () => localStorage.removeItem('kumbalo_token'),
    isAuthenticated: () => !!localStorage.getItem('kumbalo_token'),

    // Cabeceras base
    getHeaders: (isMultipart = false) => {
        const headers = {};
        if (!isMultipart) {
            headers['Content-Type'] = 'application/json';
        }
        const token = api.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },

    // Petición genérica
    request: async (endpoint, options = {}) => {
        try {
            const response = await fetch(`${API_URL}${endpoint}`, options);
            if (!response.ok) {
                let errorData = { detail: 'Error de conexión o recurso no encontrado' };
                try {
                    errorData = await response.json();
                } catch(e) {
                    console.warn("Server response was not JSON:", response.status);
                }
                throw new Error(errorData.detail || 'Error en la solicitud');
            }
            try {
                return await response.json();
            } catch(e) {
                return { status: 'ok' }; // Fallback for success without body
            }
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Endpoints Autenticación
    auth: {
        login: async (email, password) => {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);
            
            // Enviamos sin cabeceras manuales para que el navegador gestione el Content-Type de FormData
            const data = await api.request('/auth/login', {
                method: 'POST',
                body: formData,
                headers: {} 
            });
            api.setToken(data.access_token);
            return data;
        },
        register: async (nombre, email, password) => {
            return await api.request('/auth/register', {
                method: 'POST',
                headers: api.getHeaders(),
                body: JSON.stringify({ nombre, email, password })
            });
        }
    },

    // Endpoints Motos
    motos: {
        getAll: async (skip = 0, limit = 100, marca = '', anio = '', precio_max = '') => {
            let url = `/motos/?skip=${skip}&limit=${limit}`;
            if (marca) url += `&marca=${encodeURIComponent(marca)}`;
            if (anio) url += `&anio=${anio}`;
            if (precio_max) url += `&precio_max=${precio_max}`;
            return await api.request(url, {
                method: 'GET',
                headers: api.getHeaders()
            });
        },
        getById: async (id) => {
            return await api.request(`/motos/${id}`, {
                method: 'GET',
                headers: api.getHeaders()
            });
        },
        create: async (motoFormData) => {
            // Se envía FormData con archivos
            return await api.request('/motos/', {
                method: 'POST',
                headers: api.getHeaders(true),
                body: motoFormData
            });
        }
    },

    // Endpoints Favoritos
    favoritos: {
        toggle: async (motoId) => {
            return await api.request(`/motos/${motoId}/favorito`, {
                method: 'POST',
                headers: api.getHeaders()
            });
        },
        getAll: async () => {
            return await api.request('/motos/list/favoritas', {
                method: 'GET',
                headers: api.getHeaders()
            });
        }
    },

    // Endpoints Mensajes
    mensajes: {
        create: async (data) => {
            return await api.request('/mensajes/', {
                method: 'POST',
                headers: api.getHeaders(),
                body: JSON.stringify(data)
            });
        },
        getMyMessages: async () => {
            return await api.request('/mensajes/me', {
                method: 'GET',
                headers: api.getHeaders()
            });
        },
        markAsRead: async (mensajeId) => {
            return await api.request(`/mensajes/${mensajeId}/leido`, {
                method: 'PUT',
                headers: api.getHeaders()
            });
        }
    },

    // Endpoints Pagos (MercadoPago)
    payments: {
        createPreference: async (motoId) => {
            return await api.request(`/payments/create-preference/${motoId}`, {
                method: 'POST',
                headers: api.getHeaders()
            });
        }
    },
    // Endpoints RUNT
    runt: {
        getCaptcha: async () => {
            return await api.request('/v1/runt/get-captcha', {
                method: 'GET'
            });
        },
        check: async (placa, vin = null, docType = null, docNum = null, captchaToken = null, captchaValue = null) => {
            let url = `/v1/runt/consulta/${placa}?v=1`;
            if (vin) url += `&vin=${encodeURIComponent(vin)}`;
            if (docType) url += `&doc_type=${encodeURIComponent(docType)}`;
            if (docNum) url += `&doc_num=${encodeURIComponent(docNum)}`;
            if (captchaToken) url += `&captcha_token=${encodeURIComponent(captchaToken)}`;
            if (captchaValue) url += `&captcha_value=${encodeURIComponent(captchaValue)}`;
            return await api.request(url, {
                method: 'GET'
            });
        },
        buyReport: async (placa, email) => {
            return await api.request('/v1/runt/comprar-reporte', {
                method: 'POST',
                headers: api.getHeaders(),
                body: JSON.stringify({ placa, email })
            });
        }
    }
};

window.api = api;
