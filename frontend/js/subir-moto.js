document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.api !== 'undefined' && !window.api.isAuthenticated()) {
        alert("Debes iniciar sesión para publicar una moto.");
        window.location.href = 'login.html';
        return;
    }

    const form = document.getElementById('uploadMotoForm');
    const fileInput = document.getElementById('photoInput');
    
    // Si la zona existe, permitimos click para abrir el browser de archivos
    const dropzone = document.getElementById('photoDropzone');
    const previewContainer = document.getElementById('photoPreviewContainer');

    let selectedFiles = [];

    const updatePreviews = () => {
        if (!previewContainer) return;
        previewContainer.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (event) => {
                const previewItem = document.createElement('div');
                previewItem.className = `photo-preview-item ${index === 0 ? 'main-photo' : ''}`;
                
                previewItem.innerHTML = `
                    <img src="${event.target.result}" alt="Preview ${index + 1}">
                    ${index === 0 ? '<span class="main-badge">Principal</span>' : ''}
                    <div class="photo-order">${index + 1}</div>
                    <div class="photo-actions">
                        <button type="button" class="btn-remove-photo" data-index="${index}" title="Eliminar">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        </button>
                    </div>
                `;
                previewContainer.appendChild(previewItem);
            };
            reader.readAsDataURL(file);
        });
    };

    const handleFiles = (files) => {
        const validFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
        if (selectedFiles.length + validFiles.length > 10) {
            alert('Máximo 10 fotos permitidas.');
            selectedFiles = [...selectedFiles, ...validFiles].slice(0, 10);
        } else {
            selectedFiles = [...selectedFiles, ...validFiles];
        }
        updatePreviews();
    };

    if(dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());
        
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
            // Reset input so the same file can be selected again if removed
            fileInput.value = '';
        });

        // Delegación de eventos para eliminar fotos
        previewContainer?.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-remove-photo');
            if (btn) {
                const index = parseInt(btn.dataset.index);
                selectedFiles.splice(index, 1);
                updatePreviews();
            }
        });
    }

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (selectedFiles.length === 0) {
            alert('Por favor sube al menos una foto de la motocicleta.');
            return;
        }

        try {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.innerHTML = 'Subiendo información...';
                btn.disabled = true;
            }

            // Construir el FormData para el envío Multipart a FastAPI
            const formData = new FormData();
            formData.append('marca', document.getElementById('brand').value);
            formData.append('modelo', document.getElementById('model').value);
            formData.append('año', document.getElementById('year').value);
            formData.append('precio', document.getElementById('price').value);
            formData.append('kilometraje', document.getElementById('mileage').value || 0);
            formData.append('cilindraje', document.getElementById('engine').value || 0);
            formData.append('color', document.getElementById('color').value || '');
            formData.append('transmision', document.getElementById('transmission').value || '');
            formData.append('combustible', document.getElementById('fuel').value || '');
            formData.append('ciudad', document.getElementById('city').value || '');
            formData.append('descripcion', document.getElementById('description').value || 'Sin descripción');
            
            // Adjuntar todas las fotos seleccionadas
            selectedFiles.forEach(file => {
                formData.append('fotos', file);
            });

            // Enviar petición POST
            await window.api.motos.create(formData);
            
            alert('¡Moto publicada exitosamente!');
            window.location.href = 'dashboard.html';

        } catch (error) {
            console.error(error);
            alert(`Error al publicar la moto: ${error.message}`);
        } finally {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.innerHTML = 'Publicar Moto';
                btn.disabled = false;
            }
        }
    });

    // Llenar selector de años
    const yearSelect = document.getElementById('year');
    if (yearSelect) {
        const currentYear = new Date().getFullYear();
        for (let y = currentYear + 1; y >= 1990; y--) {
            const option = document.createElement('option');
            option.value = y;
            option.textContent = y;
            yearSelect.appendChild(option);
        }
    }

    // --- Lógica del Tasador IA REAL (Smart Pricing con MercadoLibre API) ---
    let lastSuggestedPrice = null;
    let debounceTimer;

    const fetchRealSuggestion = async () => {
        const brand = document.getElementById('brand').value;
        const model = document.getElementById('model').value;
        
        if (!brand || model.length < 2) return;

        const widget = document.getElementById('pricingWidget');
        const feedbackMsg = document.getElementById('pricingFeedbackMessage');
        feedbackMsg.innerHTML = '<span class="loading-spinner"></span> Consultando mercado real en Colombia...';

        try {
            const data = await window.api.request(`/analytics/price-suggestion/${encodeURIComponent(brand)}/${encodeURIComponent(model)}`, {
                method: 'GET'
            });

            if (data && data.suggested_price) {
                lastSuggestedPrice = data.suggested_price;
                updatePricingUI();
            } else {
                feedbackMsg.innerHTML = 'No hay suficientes datos recientes para este modelo exacto. Basándonos en la marca, usa un precio competitivo.';
            }
        } catch (e) {
            console.error("Error fetching price suggestion:", e);
        }
    };

    const updatePricingUI = () => {
        const priceInput = document.getElementById('price').value;
        const widget = document.getElementById('pricingWidget');
        const feedbackMsg = document.getElementById('pricingFeedbackMessage');
        
        if(!widget || !lastSuggestedPrice) return;
        
        if(!priceInput || priceInput < 100000) {
            widget.style.borderLeftColor = 'var(--primary)';
            widget.style.backgroundColor = 'var(--gray-light)';
            feedbackMsg.innerHTML = `<strong>Sugerencia IA:</strong> El precio promedio en Colombia para este modelo es de <b>${lastSuggestedPrice.toLocaleString()} COP</b>.`;
            return;
        }
        
        const userPrice = parseInt(priceInput);
        const diff = ((userPrice - lastSuggestedPrice) / lastSuggestedPrice) * 100;

        if (diff <= -5) {
            widget.style.backgroundColor = '#ecfdf5';
            widget.style.borderLeftColor = 'var(--success)';
            feedbackMsg.innerHTML = `<strong>¡Precio de Oferta! 🔥</strong> Estás un ${Math.abs(diff).toFixed(1)}% abajo del mercado (${lastSuggestedPrice.toLocaleString()} COP). ¡Se venderá hoy mismo!`;
            feedbackMsg.style.color = 'var(--success-dark)';
        } else if (diff <= 10) {
            widget.style.backgroundColor = '#eff6ff';
            widget.style.borderLeftColor = '#3b82f6';
            feedbackMsg.innerHTML = `<strong>Precio de Mercado ✅</strong> Estás en el rango justo (${lastSuggestedPrice.toLocaleString()} COP prom). Es un valor competitivo para Bogotá/Medellín.`;
            feedbackMsg.style.color = '#1d4ed8';
        } else {
            widget.style.backgroundColor = '#fff7ed';
            widget.style.borderLeftColor = 'var(--orange)';
            feedbackMsg.innerHTML = `<strong>Precio Elevado ⚠️</strong> Tu precio es un ${diff.toFixed(1)}% mayor al promedio real (${lastSuggestedPrice.toLocaleString()} COP). Considera ajustarlo para atraer más compradores.`;
            feedbackMsg.style.color = '#c2410c';
        }

        // Actualizar comisión también
        updateCommission(userPrice);
    };

    const updateCommission = (price) => {
        const commWidget = document.getElementById('commissionWidget');
        const commValueLabel = document.getElementById('commissionValue');
        const savingsMsg = document.getElementById('savingsMessage');
        
        if(!commWidget) return;
        if(!price || price < 500000) { commWidget.style.display = 'none'; return; }
        
        commWidget.style.display = 'block';
        let fee = 150000;
        if(price >= 20000000) fee = 500000;
        else if(price >= 10000000) fee = 250000;
        
        const traditional3Percent = price * 0.03;
        const savings = traditional3Percent - fee;
        
        commValueLabel.innerText = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(fee);
        if(savings > 0) {
            savingsMsg.style.display = 'block';
            savingsMsg.innerText = `📉 Ahorras ${new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(savings)} frente al 3% tradicional`;
        } else {
            savingsMsg.style.display = 'none';
        }
    };

    // Listeners con Debounce para no saturar la API
    document.getElementById('brand')?.addEventListener('change', fetchRealSuggestion);
    document.getElementById('model')?.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchRealSuggestion, 800);
    });
    document.getElementById('price')?.addEventListener('input', updatePricingUI);
});
