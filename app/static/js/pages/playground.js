/**
 * Playground Page Logic
 * Handles PDF upload and RAG query functionality
 */

const PlaygroundPage = {
    projectId: null,
    apiKey: null,
    collectionName: 'playground-demo',

    // Upload state
    selectedFile: null,
    uploading: false,

    // Collections data
    collectionsData: [],

    async init(projectId) {
        this.projectId = projectId;

        // Get project API key
        try {
            const response = await apiCall(`/api/v1/projects/${this.projectId}/api-key`);
            const data = await response.json();
            this.apiKey = data.api_key;
        } catch (error) {
            showAlert('Error al obtener API Key del proyecto', 'error');
            return;
        }

        // Load collections
        await this.loadCollections();

        // Setup upload zone
        this.setupUploadZone();
    },

    setupUploadZone() {
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('file-input');
        const uploadBtn = document.getElementById('upload-btn');

        uploadZone.addEventListener('click', () => fileInput.click());

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('drag-over');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type === 'application/pdf') {
                this.handleFileSelect(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });
    },

    handleFileSelect(file) {
        this.selectedFile = file;
        document.getElementById('upload-prompt').style.display = 'none';
        document.getElementById('file-selected').style.display = 'block';
        document.getElementById('file-selected').innerHTML = `
            <div class="file-info">
                <div class="file-info-icon">📑</div>
                <div class="file-info-details">
                    <div class="file-info-name">${file.name}</div>
                    <div class="file-info-size">${this.formatFileSize(file.size)}</div>
                </div>
                <button onclick="PlaygroundPage.clearFile(event)" style="background: transparent; border: none; color: var(--text-secondary); cursor: pointer; font-size: 1.5rem;">✕</button>
            </div>
        `;
        document.getElementById('upload-btn').style.display = 'block';
    },

    clearFile(e) {
        e.stopPropagation();
        this.selectedFile = null;
        document.getElementById('file-input').value = '';
        document.getElementById('upload-prompt').style.display = 'block';
        document.getElementById('file-selected').style.display = 'none';
        document.getElementById('upload-btn').style.display = 'none';
        document.getElementById('upload-status').style.display = 'none';
    },

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    async uploadPdf() {
        if (!this.selectedFile || !this.apiKey) return;

        const collection = document.getElementById('upload-collection').value.trim();
        if (!collection) {
            showAlert('Por favor ingresa un nombre de colección', 'error');
            return;
        }

        const uploadBtn = document.getElementById('upload-btn');
        const uploadStatus = document.getElementById('upload-status');

        uploadBtn.disabled = true;
        uploadBtn.textContent = '⏳ Procesando...';
        uploadStatus.style.display = 'none';

        const formData = new FormData();
        formData.append('file', this.selectedFile);

        try {
            const response = await fetch(`/api/v1/collections/${collection}/ingest/files`, {
                method: 'POST',
                headers: {
                    'X-API-Key': this.apiKey
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al subir archivo');
            }

            uploadStatus.className = 'alert alert-success';
            uploadStatus.textContent = '✅ Documento indexado correctamente. Ya puedes consultarlo en la sección RAG.';
            uploadStatus.style.display = 'block';

            // Reload collections
            await this.loadCollections();

            // Clear file
            this.clearFile(new Event('click'));
        } catch (error) {
            uploadStatus.className = 'alert alert-error';
            uploadStatus.textContent = '❌ Error: ' + error.message;
            uploadStatus.style.display = 'block';
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = '📤 Subir e Indexar';
        }
    },

    async loadCollections() {
        try {
            console.log('Loading collections for project:', this.projectId);
            const response = await apiCall(`/api/v1/projects/${this.projectId}/collections`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Collections API response:', data);

            const collectionSelect = document.getElementById('rag-collection');

            if (!data.collections || data.collections.length === 0) {
                collectionSelect.innerHTML = '<option value="">No hay colecciones disponibles</option>';
                collectionSelect.disabled = false;
                return;
            }

            this.collectionsData = data.collections;
            console.log('Total collections:', this.collectionsData.length);

            // Filter only vector collections
            const vectorCollections = this.collectionsData.filter(c => c.name.endsWith('_vectors'));
            console.log('Vector collections found:', vectorCollections.length, vectorCollections);

            if (vectorCollections.length === 0) {
                collectionSelect.innerHTML = '<option value="">No hay colecciones con embeddings</option>';
                collectionSelect.disabled = false;
                return;
            }

            collectionSelect.innerHTML = '<option value="">Selecciona una colección...</option>' +
                vectorCollections.map(c => `<option value="${c.name}">${c.name}</option>`).join('');

            collectionSelect.disabled = false;
            document.getElementById('rag-query').disabled = false;
            document.getElementById('rag-submit-btn').disabled = false;

            console.log('Collections loaded successfully');

        } catch (error) {
            console.error('Error loading collections:', error);
            const collectionSelect = document.getElementById('rag-collection');
            collectionSelect.innerHTML = '<option value="">Error al cargar colecciones</option>';
            collectionSelect.disabled = false;
        }
    },

    async submitRagQuery() {
        const collection = document.getElementById('rag-collection').value;
        const query = document.getElementById('rag-query').value.trim();

        if (!collection || !query) {
            showAlert('Por favor selecciona una colección y escribe una pregunta', 'error');
            return;
        }

        // Hide previous response
        document.getElementById('rag-response').style.display = 'none';

        // Show loading
        document.getElementById('rag-loading').style.display = 'block';
        document.getElementById('rag-submit-btn').disabled = true;

        // Animate loading steps
        this.animateLoadingSteps();

        try {
            const response = await fetch(`/api/v1/collections/${collection}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 5
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error en la consulta');
            }

            const data = await response.json();

            // Display response with markdown formatting
            const formattedAnswer = this.formatMarkdown(data.answer.markdown);
            document.getElementById('response-content').innerHTML = formattedAnswer;

            // Display sources with preview and expand functionality
            const sourcesContainer = document.getElementById('response-sources-container');
            const sourcesList = document.getElementById('response-sources');
            sourcesList.innerHTML = '';

            if (data.sources && data.sources.length > 0) {
                sourcesContainer.style.display = 'block';
                data.sources.forEach((source, index) => {
                    const li = document.createElement('li');
                    li.className = 'source-item';

                    // Create preview (first 150 characters)
                    const preview = source.text.length > 150
                        ? source.text.substring(0, 150) + '...'
                        : source.text;

                    const isLong = source.text.length > 150;

                    // Handle null/undefined score
                    const scoreDisplay = source.score != null
                        ? `${(source.score * 100).toFixed(1)}% relevancia`
                        : 'Relevancia no disponible';

                    li.innerHTML = `
                        <div class="source-header">
                            <strong style="color: var(--accent-primary);">📄 Fuente ${index + 1}</strong>
                            <span class="source-score">${scoreDisplay}</span>
                        </div>
                        <p class="source-preview" id="preview-${index}">${preview}</p>
                        ${isLong ? `
                            <p class="source-full" id="full-${index}" style="display: none;">${source.text}</p>
                            <button class="btn-expand" onclick="PlaygroundPage.toggleSource(${index})" id="btn-${index}">
                                Ver más ▼
                            </button>
                        ` : ''}
                    `;
                    sourcesList.appendChild(li);
                });
            } else {
                sourcesContainer.style.display = 'none';
            }

            document.getElementById('rag-loading').style.display = 'none';
            document.getElementById('rag-response').style.display = 'block';

        } catch (error) {
            document.getElementById('rag-loading').style.display = 'none';
            showAlert('Error: ' + error.message, 'error');
        } finally {
            document.getElementById('rag-submit-btn').disabled = false;
        }
    },

    toggleSource(index) {
        const preview = document.getElementById(`preview-${index}`);
        const full = document.getElementById(`full-${index}`);
        const btn = document.getElementById(`btn-${index}`);

        if (full.style.display === 'none') {
            preview.style.display = 'none';
            full.style.display = 'block';
            btn.textContent = 'Ver menos ▲';
        } else {
            preview.style.display = 'block';
            full.style.display = 'none';
            btn.textContent = 'Ver más ▼';
        }
    },

    animateLoadingSteps() {
        const steps = document.querySelectorAll('.loading-step');
        let currentStep = 0;

        const interval = setInterval(() => {
            steps.forEach(s => s.classList.remove('active'));
            if (currentStep < steps.length) {
                steps[currentStep].classList.add('active');
                currentStep++;
            } else {
                currentStep = 0;
            }
        }, 3000);

        // Store interval to clear it later if needed
        window.loadingInterval = interval;
    },

    formatMarkdown(text) {
        /**
         * Convert markdown to HTML with proper formatting
         * Handles bold text, bullet points, and paragraphs correctly
         */
        if (!text) return '';

        // Split into paragraphs first (double line breaks)
        const paragraphs = text.split(/\n\n+/);

        const formattedParagraphs = paragraphs.map(para => {
            // Check if it's a header (###, ##, #)
            if (/^#{1,3}\s+/.test(para.trim())) {
                const headerMatch = para.trim().match(/^(#{1,3})\s+(.+)$/);
                if (headerMatch) {
                    const level = headerMatch[1].length; // 1, 2, or 3
                    const text = headerMatch[2];
                    const fontSize = level === 1 ? '1.5rem' : level === 2 ? '1.3rem' : '1.1rem';
                    const marginTop = level === 1 ? '20px' : '16px';
                    return `<h${level + 2} style="color: var(--accent-primary); font-size: ${fontSize}; font-weight: 700; margin-top: ${marginTop}; margin-bottom: 12px;">${text}</h${level + 2}>`;
                }
            }

            // Check if paragraph contains bullet points (• or *)
            const hasBullets = para.includes('•') || /^\s*\*\s+/m.test(para);

            if (hasBullets) {
                // Split into lines and process bullets
                const lines = para.split('\n');
                const bulletItems = [];

                lines.forEach(line => {
                    const trimmed = line.trim();
                    if (!trimmed) return; // Skip empty lines

                    // Convert **bold** to styled strong tags
                    let formatted = trimmed.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #00ff88;">$1</strong>');

                    // Check if it's a bullet point (• or * at start)
                    if (formatted.startsWith('•') || /^\*\s+/.test(formatted)) {
                        // Remove bullet marker (• or *)
                        formatted = formatted.replace(/^[•*]\s*/, '');
                        bulletItems.push(`<li style="margin-bottom: 10px; padding-left: 8px;"><span style="color: #00ff88; margin-right: 8px;">•</span>${formatted}</li>`);
                    } else {
                        // It's a regular line within bullet context (like a title or subtitle)
                        bulletItems.push(`<div style="margin-bottom: 8px; font-weight: 600;">${formatted}</div>`);
                    }
                });

                return `<ul style="margin: 12px 0; padding-left: 12px; list-style: none;">${bulletItems.join('')}</ul>`;
            } else {
                // Regular paragraph - convert **bold**
                let formatted = para.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #00ff88;">$1</strong>');
                // Preserve single line breaks within paragraph
                formatted = formatted.replace(/\n/g, '<br>');
                return `<p style="margin: 12px 0; line-height: 1.6;">${formatted}</p>`;
            }
        });

        return formattedParagraphs.join('');
    },

    clearRagResponse() {
        document.getElementById('rag-response').style.display = 'none';
        document.getElementById('rag-query').value = '';
        if (window.loadingInterval) {
            clearInterval(window.loadingInterval);
        }
    }
};

// Make functions globally accessible for onclick handlers
window.PlaygroundPage = PlaygroundPage;
window.uploadPdf = () => PlaygroundPage.uploadPdf();
window.submitRagQuery = () => PlaygroundPage.submitRagQuery();
window.clearRagResponse = () => PlaygroundPage.clearRagResponse();
