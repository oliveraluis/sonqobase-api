/**
 * Project Detail Page Logic
 * Handles project stats, API key management, and collections display
 */

const ProjectDetailPage = {
    projectId: null,
    apiKey: null,

    async init(projectId) {
        this.projectId = projectId;

        // Load project details
        await this.loadProjectDetails();

        // Load project stats
        await this.loadProjectStats();

        // Load API key
        await this.loadApiKey();

        // Load collections
        await this.loadCollections();
    },

    async loadProjectDetails() {
        try {
            const response = await apiCall(`/api/v1/projects/${this.projectId}`);
            const project = await response.json();

            // Update breadcrumb
            document.getElementById('breadcrumb-project').textContent = project.name;

            // Update header
            document.getElementById('project-header').innerHTML = `
                <div class="project-title-row">
                    <h1 class="project-title">${project.name}</h1>
                    <span class="project-status-badge ${project.status}">${project.status}</span>
                </div>
                <p class="project-description">${project.description || 'Sin descripción'}</p>
                <div class="project-meta">
                    <div class="meta-item">
                        <span>📅 Creado:</span>
                        <span>${new Date(project.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="meta-item">
                        <span>⏰ Expira:</span>
                        <span>${new Date(project.expires_at).toLocaleDateString()}</span>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading project:', error);
            showAlert('Error al cargar detalles del proyecto', 'error');
        }
    },

    async loadProjectStats() {
        try {
            const response = await apiCall(`/api/v1/projects/${this.projectId}/stats`);
            const stats = await response.json();

            document.getElementById('stats-grid').innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">Lecturas</div>
                    <div class="stat-value">${stats.reads || 0}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Escrituras</div>
                    <div class="stat-value">${stats.writes || 0}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Consultas RAG</div>
                    <div class="stat-value">${stats.rag_queries || 0}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Colecciones</div>
                    <div class="stat-value">${stats.collections_count || 0}</div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    },

    async loadApiKey() {
        try {
            const response = await apiCall(`/api/v1/projects/${this.projectId}/api-key`);
            const data = await response.json();
            this.apiKey = data.api_key;

            document.getElementById('api-key-value').textContent = this.apiKey;
        } catch (error) {
            console.error('Error loading API key:', error);
            document.getElementById('api-key-value').textContent = 'Error al cargar';
        }
    },

    async copyApiKey() {
        const copyBtn = document.getElementById('copy-key-btn');
        const success = await copyToClipboard(this.apiKey);

        if (success) {
            copyBtn.textContent = '✅ ¡Copiado!';
            copyBtn.classList.add('copied');

            setTimeout(() => {
                copyBtn.textContent = '📋 Copiar';
                copyBtn.classList.remove('copied');
            }, 2000);
        } else {
            showAlert('Error al copiar. Por favor copia manualmente.', 'error');
        }
    },

    async loadCollections() {
        try {
            const response = await apiCall(`/api/v1/projects/${this.projectId}/collections`);
            const data = await response.json();

            const collectionsGrid = document.getElementById('collections-grid');

            if (data.collections.length === 0) {
                collectionsGrid.innerHTML = `
                    <div class="empty-collections">
                        <p>Aún no hay colecciones. Crea una insertando documentos vía API.</p>
                    </div>
                `;
                return;
            }

            collectionsGrid.innerHTML = data.collections.map(col => `
                <div class="collection-card">
                    <div class="collection-name">${col.name}</div>
                    <div class="collection-count">${col.document_count || 0} documentos</div>
                </div>
            `).join('');

        } catch (error) {
            console.error('Error loading collections:', error);
        }
    }
};

// Make functions globally accessible
window.ProjectDetailPage = ProjectDetailPage;
window.copyApiKey = () => ProjectDetailPage.copyApiKey();
