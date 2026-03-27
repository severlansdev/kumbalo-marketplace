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

    if(dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());
        
        // --- NUEVA LÓGICA: Manejo de selección y previsualización ---
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            
            // Limpiar contenedor
            if (previewContainer) previewContainer.innerHTML = '';
            
            if (files.length === 0) return;

            // Limitar a 10 fotos como dice la UI
            const filesToPreview = files.slice(0, 10);
            
            filesToPreview.forEach((file, index) => {
                if (!file.type.startsWith('image/')) return;

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
                    
                    if (previewContainer) previewContainer.appendChild(previewItem);
                };
                reader.readAsDataURL(file);
            });
        });

        // Delegación de eventos para eliminar fotos (opcional pero recomendado)
        previewContainer?.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-remove-photo');
            if (btn) {
                const index = parseInt(btn.dataset.index);
                const dt = new DataTransfer();
                const { files } = fileInput;
                
                for (let i = 0; i < files.length; i++) {
                    if (index !== i) dt.items.add(files[i]);
                }
                
                fileInput.files = dt.files; // Update the input
                fileInput.dispatchEvent(new Event('change')); // Trigger re-render
            }
        });
    }

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!fileInput || fileInput.files.length === 0) {
            alert('Por favor sube al menos una foto de la motocicleta.');
            return;
        }

        try {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.innerHTML = 'Subiendo a AWS S3...';
                btn.disabled = true;
            }

            // Construir el FormData para el envío Multipart a FastAPI
            const formData = new FormData();
            formData.append('marca', document.getElementById('brand').value);
            formData.append('modelo', document.getElementById('model').value);
            formData.append('año', document.getElementById('year').value);
            formData.append('precio', document.getElementById('price').value);
            formData.append('kilometraje', document.getElementById('mileage').value || 0);
            formData.append('descripcion', document.getElementById('description').value || 'Sin descripción');
            
            // Adjuntar la primera foto subida
            formData.append('foto', fileInput.files[0]);

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

    // --- Lógica del Tasador IA (Smart Pricing) ---
    const calculatePricing = () => {
        const brand = document.getElementById('brand').value.toLowerCase();
        const year = parseInt(document.getElementById('year').value) || 2015;
        const engine = parseInt(document.getElementById('engine').value) || 150;
        const priceInput = document.getElementById('price').value;
        
        const widget = document.getElementById('pricingWidget');
        const feedbackMsg = document.getElementById('pricingFeedbackMessage');
        
        if(!widget) return;
        
        if(!priceInput || priceInput < 100000) {
            widget.style.borderColor = 'var(--primary)';
            widget.style.backgroundColor = 'var(--gray-light)';
            feedbackMsg.innerHTML = 'Ingresa todos los datos y el precio para calcular la tasación en vivo...';
            return;
        }
        
        const IP = parseInt(priceInput);
        
        // Mock Predicción
        let base = 6000000;
        if(brand.includes('ducati') || brand.includes('bmw') || brand.includes('harley')) base = 35000000;
        else if(brand.includes('yamaha') || brand.includes('honda')) base = 8000000;
        
        // Multipliers
        const currentY = new Date().getFullYear();
        let yearMult = 1 - ((currentY - year) * 0.05);
        if (yearMult < 0.3) yearMult = 0.3;
        
        const engineAdd = (engine / 150) * 2000000;
        
        const estimatedPrice = (base * yearMult) + engineAdd;
        
        // --- Nueva Lógica de Comisión Fija "Adiós al 3%" ---
        const updateCommission = (price) => {
            const commWidget = document.getElementById('commissionWidget');
            const commValueLabel = document.getElementById('commissionValue');
            const savingsMsg = document.getElementById('savingsMessage');
            
            if(!commWidget) return;
            
            if(!price || price < 500000) {
                commWidget.style.display = 'none';
                return;
            }
            
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

        // Análisis del Tasador IA
        if(IP <= estimatedPrice * 0.90) {
            widget.style.borderColor = 'var(--success)';
            widget.style.backgroundColor = '#ecfdf5';
            feedbackMsg.innerHTML = '<strong>¡Precio Excelente! 🔥</strong> Tu moto está tasada por debajo del mercado. ¡Se venderá rapidísimo!';
            feedbackMsg.style.color = 'var(--success-dark)';
        } else if (IP <= estimatedPrice * 1.15) {
            widget.style.borderColor = '#3b82f6';
            widget.style.backgroundColor = '#eff6ff';
            feedbackMsg.innerHTML = '<strong>Precio Justo ✅</strong> El valor está dentro del promedio nacional para esta marca, año y cilindraje.';
            feedbackMsg.style.color = '#1d4ed8';
        } else {
            widget.style.borderColor = 'var(--orange)';
            widget.style.backgroundColor = '#fff7ed';
            feedbackMsg.innerHTML = '<strong>Precio Alto ⚠️</strong> El precio es un poco más alto que el promedio estatal. Esto podría ralentizar la venta. Considera ajustarlo.';
            feedbackMsg.style.color = '#c2410c';
        }
        
        updateCommission(IP);
    };
    
    // Listeners para re-analizar dinámicamente
    document.getElementById('price')?.addEventListener('input', calculatePricing);
    document.getElementById('brand')?.addEventListener('change', calculatePricing);
    document.getElementById('year')?.addEventListener('change', calculatePricing);
    document.getElementById('engine')?.addEventListener('input', calculatePricing);
});
