document.addEventListener('DOMContentLoaded', () => {
    // --- Referencias UI ---
    const uploadArea = document.getElementById('uploadArea');
    const imagenInput = document.getElementById('imagenInput');
    const uploadContent = document.getElementById('uploadContent');
    const imagenPreview = document.getElementById('imagenPreview');
    const ubicacionPill = document.getElementById('ubicacionPill');
    const ubicacionTexto = document.getElementById('ubicacionTexto');
    const modeCards = document.querySelectorAll('.mode-card');
    const analizarBtn = document.getElementById('analizarBtn');
    const resultadoCard = document.getElementById('resultadoCard');
    const resultadoContenido = document.getElementById('resultadoContenido');
    const idiomaSelect = document.getElementById('idiomaSelect');
    const historialGrid = document.getElementById('historialGrid');
    const limpiarHistorialBtn = document.getElementById('limpiarHistorialBtn');
    const uploadBtnAux = document.getElementById('uploadBtnAux');

    // --- DICCIONARIO DE TRADUCCIÓN UI ---
    const uiTranslations = {
        es: {
            badge: "👁️ Impulsado por NVIDIA / Tavily", dragText: "Arrastra tu foto o", btnUpload: "Tomar Foto / Subir",
            locBuscando: "Buscando ubicación...", locLista: "Ubicación lista", locSin: "Sin ubicación GPS",
            modoEdu: "Educativo", modoTur: "Turístico", modoExp: "Explorador",
            btnAnalizar: "Analizar Entorno", btnAnalizando: "Analizando con NVIDIA... ⏳",
            resTitulo: "Resultado del Análisis", pasaporteTit: "📔 Mi Pasaporte de Descubrimientos", btnBorrar: "Borrar Historial",
            alertaImg: "Por favor, selecciona una imagen primero.", alertaBorrar: "¿Seguro que quieres vaciar tu pasaporte?",
            descubierto: "✨ Has descubierto"
        },
        en: {
            badge: "👁️ Powered by NVIDIA / Tavily", dragText: "Drag your photo or", btnUpload: "Take Photo / Upload",
            locBuscando: "Finding location...", locLista: "Location ready", locSin: "No GPS location",
            modoEdu: "Educational", modoTur: "Touristic", modoExp: "Explorer",
            btnAnalizar: "Analyze Environment", btnAnalizando: "Analyzing with NVIDIA... ⏳",
            resTitulo: "Analysis Result", pasaporteTit: "📔 My Discovery Passport", btnBorrar: "Clear History",
            alertaImg: "Please select an image first.", alertaBorrar: "Are you sure you want to clear your passport?",
            descubierto: "✨ You discovered"
        },
        fr: {
            badge: "👁️ Propulsé par NVIDIA / Tavily", dragText: "Faites glisser votre photo ou", btnUpload: "Prendre / Télécharger",
            locBuscando: "Recherche de l'emplacement...", locLista: "Emplacement prêt", locSin: "Pas de localisation GPS",
            modoEdu: "Éducatif", modoTur: "Touristique", modoExp: "Explorateur",
            btnAnalizar: "Analyser l'environnement", btnAnalizando: "Analyse avec NVIDIA... ⏳",
            resTitulo: "Résultat de l'analyse", pasaporteTit: "📔 Mon passeport de découvertes", btnBorrar: "Effacer l'historique",
            alertaImg: "Veuillez d'abord sélectionner une image.", alertaBorrar: "Voulez-vous vraiment vider votre passeport ?",
            descubierto: "✨ Vous avez découvert"
        },
        de: {
            badge: "👁️ Unterstützt von NVIDIA / Tavily", dragText: "Ziehe dein Foto hierher oder", btnUpload: "Foto aufnehmen / Hochladen",
            locBuscando: "Standort wird gesucht...", locLista: "Standort bereit", locSin: "Kein GPS-Standort",
            modoEdu: "Lehrreich", modoTur: "Touristisch", modoExp: "Entdecker",
            btnAnalizar: "Umgebung analysieren", btnAnalizando: "Analysieren mit NVIDIA... ⏳",
            resTitulo: "Analyseergebnis", pasaporteTit: "📔 Mein Entdeckerpass", btnBorrar: "Verlauf löschen",
            alertaImg: "Bitte wähle zuerst ein Bild aus.", alertaBorrar: "Möchtest du deinen Pass wirklich leeren?",
            descubierto: "✨ Du hast entdeckt"
        },
        zh: {
            badge: "👁️ 由 NVIDIA / Tavily 提供支持", dragText: "拖放照片或", btnUpload: "拍照 / 上传",
            locBuscando: "正在查找位置...", locLista: "位置已准备好", locSin: "无 GPS 位置",
            modoEdu: "教育", modoTur: "旅游", modoExp: "探索者",
            btnAnalizar: "分析环境", btnAnalizando: "正在用 NVIDIA 分析... ⏳",
            resTitulo: "分析结果", pasaporteTit: "📔 我的探索护照", btnBorrar: "清除历史记录",
            alertaImg: "请先选择一张图片。", alertaBorrar: "您确定要清空护照吗？",
            descubierto: "✨ 您发现了"
        }
    };

    // Función que cambia los textos al vuelo
    function actualizarIdiomaUI() {
        const lang = idiomaSelect.value;
        const textos = uiTranslations[lang];

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (textos[key]) {
                el.textContent = textos[key];
            }
        });
        
        // Actualizar el estado de texto de botones y variables locales
        if (!analizarBtn.disabled) analizarBtn.textContent = textos.btnAnalizar;
        renderizarHistorial(); // Refrescar el historial para traducir la fecha
    }

    idiomaSelect.addEventListener('change', actualizarIdiomaUI);

    // --- Estado de la App ---
    let currentFile = null;
    let modoSeleccionado = 'Educativo';
    let lat = null;
    let lon = null;

    // --- Geolocalización inicial ---
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(pos => {
            lat = pos.coords.latitude;
            lon = pos.coords.longitude;
            const textos = uiTranslations[idiomaSelect.value];
            ubicacionTexto.textContent = textos.locLista;
            ubicacionTexto.setAttribute('data-i18n', 'locLista');
        }, err => {
            const textos = uiTranslations[idiomaSelect.value];
            ubicacionTexto.textContent = textos.locSin;
            ubicacionTexto.setAttribute('data-i18n', 'locSin');
        });
    }

    // --- Lógica del Área de Subida ---
    const abrirSelector = () => imagenInput.click();
    
    uploadArea.addEventListener('click', (e) => {
        if (e.target !== uploadBtnAux) abrirSelector();
    });
    
    if (uploadBtnAux) {
        uploadBtnAux.addEventListener('click', (e) => {
            e.stopPropagation();
            abrirSelector();
        });
    }

    imagenInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) procesarImagen(file);
    });

    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.style.borderColor = "var(--accent)"; });
    uploadArea.addEventListener('dragleave', () => { uploadArea.style.borderColor = "var(--border-color)"; });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = "var(--border-color)";
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) procesarImagen(file);
    });

    function procesarImagen(file) {
        currentFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagenPreview.src = e.target.result;
            imagenPreview.style.display = 'block';
            uploadContent.style.display = 'none';
            ubicacionPill.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    // --- Lógica Selector de Modos ---
    modeCards.forEach(card => {
        card.addEventListener('click', () => {
            modeCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            modoSeleccionado = card.dataset.modo;
        });
    });

    // --- Lógica de Análisis ---
    analizarBtn.addEventListener('click', async () => {
        const textos = uiTranslations[idiomaSelect.value];
        if (!currentFile) {
            alert(textos.alertaImg);
            return;
        }

        analizarBtn.disabled = true;
        analizarBtn.textContent = textos.btnAnalizando;
        resultadoCard.style.display = 'none';

        try {
            const formData = new FormData();
            formData.append('file', currentFile);
            formData.append('modo', modoSeleccionado.toLowerCase()); 
            formData.append('idioma', idiomaSelect.value);
            
            const ubicacionStr = (lat && lon) ? `${lat}, ${lon}` : "Ubicación desconocida";
            formData.append('ubicacion', ubicacionStr);

            const response = await fetch('/api/analizar', {
                method: 'POST',
                body: formData 
            });

            if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
            
            const data = await response.json();
            const textoIA = data.ficha_final; 
            const diagnosticoBreve = data.diagnostico_interno; 

            resultadoContenido.innerHTML = marked.parse(textoIA);
            resultadoCard.style.display = 'block';

            guardarEnPasaporte(modoSeleccionado, textoIA, diagnosticoBreve);

        } catch (error) {
            resultadoContenido.innerHTML = `<p style="color: #ff5e5e;">Error de conexión: ${error.message}</p>`;
            resultadoCard.style.display = 'block';
        } finally {
            analizarBtn.disabled = false;
            analizarBtn.textContent = textos.btnAnalizar;
        }
    });

    // --- Lógica del Pasaporte ---
    function guardarEnPasaporte(modo, texto, diagnosticoBreve) {
        if (!texto) return;
        const fecha = new Date().toLocaleDateString();
        
        let icono = "🧭";
        if(modo === "Educativo") icono = "🔬";
        if(modo === "Turístico") icono = "🗺️";

        const nuevoItem = { modo, texto, fecha, icono, diagnosticoBreve };
        const historial = JSON.parse(localStorage.getItem('historialPasaporte') || '[]');
        historial.unshift(nuevoItem);
        localStorage.setItem('historialPasaporte', JSON.stringify(historial));
        renderizarHistorial();
    }

    function renderizarHistorial() {
        historialGrid.innerHTML = '';
        const historial = JSON.parse(localStorage.getItem('historialPasaporte') || '[]');
        const textos = uiTranslations[idiomaSelect.value];
        
        historial.forEach(item => {
            const card = document.createElement('div');
            card.className = 'history-item';
            
            // Traducir el título dinámicamente ("Has descubierto...")
            const tituloDinamico = item.diagnosticoBreve 
                ? `${textos.descubierto}: ${item.diagnosticoBreve}` 
                : "✨ Descubrimiento...";

            card.innerHTML = `
                <div class="history-header">
                    <span>${item.icono} ${item.modo}</span>
                    <span>${item.fecha}</span>
                </div>
                <div class="history-text" style="margin-top: 10px; font-weight: 500; color: var(--text-primary);">
                    ${tituloDinamico}
                </div>
            `;
            historialGrid.appendChild(card);
        });
    }

    limpiarHistorialBtn.addEventListener('click', () => {
        const textos = uiTranslations[idiomaSelect.value];
        if(confirm(textos.alertaBorrar)) {
            localStorage.removeItem('historialPasaporte');
            renderizarHistorial();
        }
    });

    // Inicializar idioma y pasaporte
    actualizarIdiomaUI();
});