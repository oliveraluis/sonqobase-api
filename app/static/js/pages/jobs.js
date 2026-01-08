/**
 * Jobs Page Logic
 * Handles job tracking and monitoring for document ingestion
 */

const JobsPage = {
    projectId: null,
    jobs: [],
    filteredJobs: [],

    async init(projectId) {
        this.projectId = projectId;
        await this.loadJobs();
    },

    async loadJobs() {
        try {
            const response = await apiCall(`/api/v1/projects/${this.projectId}/jobs`);
            const data = await response.json();

            this.jobs = data.jobs || [];
            this.applyFilters();
        } catch (error) {
            console.error('Error loading jobs:', error);
            document.getElementById('jobs-container').innerHTML = `
                <div class="alert alert-error">
                    Error al cargar jobs. Por favor intenta de nuevo.
                </div>
            `;
        }
    },

    applyFilters() {
        const statusFilter = document.getElementById('filter-status').value;

        this.filteredJobs = this.jobs.filter(job => {
            if (statusFilter && job.status !== statusFilter) return false;
            return true;
        });

        this.renderJobs();
    },

    renderJobs() {
        const container = document.getElementById('jobs-container');

        if (this.filteredJobs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">📭</div>
                    <h3>No hay jobs</h3>
                    <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                        Los jobs de ingesta aparecerán aquí cuando subas documentos.
                    </p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="jobs-table">
                <div class="jobs-table-header">
                    <div class="job-col-id">Job ID</div>
                    <div class="job-col-collection">Colección</div>
                    <div class="job-col-status">Estado</div>
                    <div class="job-col-created">Creado</div>
                    <div class="job-col-duration">Duración</div>
                    <div class="job-col-actions">Acciones</div>
                </div>
                ${this.filteredJobs.map(job => this.renderJobRow(job)).join('')}
            </div>
        `;
    },

    renderJobRow(job) {
        const statusClass = this.getStatusClass(job.status);
        const statusIcon = this.getStatusIcon(job.status);
        const statusLabel = this.getStatusLabel(job.status);
        const duration = this.calculateDuration(job);

        return `
            <div class="job-row" id="job-${job.job_id}">
                <div>
                    <div><code>${job.job_id.substring(0, 8)}...</code></div>
                    <div>${job.collection || 'N/A'}</div>
                    <div>
                        <span class="status-badge ${statusClass}">
                            ${statusIcon} ${statusLabel}
                        </span>
                    </div>
                    <div>${this.formatDate(job.created_at)}</div>
                    <div>${duration}</div>
                    <div>
                        <button class="btn-icon" onclick="JobsPage.toggleDetails('${job.job_id}')" title="Ver detalles">
                            👁️
                        </button>
                    </div>
                </div>
                <div class="job-details" id="details-${job.job_id}" style="display: none;">
                    <div class="details-content">
                        <h4>Detalles del Job</h4>
                        <div class="details-grid">
                            <div class="detail-item">
                                <span class="detail-label">Job ID:</span>
                                <span class="detail-value"><code>${job.job_id}</code></span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Colección:</span>
                                <span class="detail-value">${job.collection || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Archivo:</span>
                                <span class="detail-value">${job.metadata?.filename || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Documentos procesados:</span>
                                <span class="detail-value">${job.result?.documents_processed || 0}</span>
                            </div>
                            ${job.error_message ? `
                            <div class="detail-item full-width">
                                <span class="detail-label">Error:</span>
                                <span class="detail-value error-text">${job.error_message}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    toggleDetails(jobId) {
        const details = document.getElementById(`details-${jobId}`);
        if (details.style.display === 'none') {
            details.style.display = 'block';
        } else {
            details.style.display = 'none';
        }
    },

    getStatusClass(status) {
        const classes = {
            'queued': 'status-pending',
            'extracting_text': 'status-processing',
            'generating_embeddings': 'status-processing',
            'completed': 'status-completed',
            'failed': 'status-failed'
        };
        return classes[status] || 'status-pending';
    },

    getStatusIcon(status) {
        const icons = {
            'queued': '⏳',
            'extracting_text': '📄',
            'generating_embeddings': '🧠',
            'completed': '✅',
            'failed': '❌'
        };
        return icons[status] || '❓';
    },

    getStatusLabel(status) {
        const labels = {
            'queued': 'En cola',
            'extracting_text': 'Extrayendo',
            'generating_embeddings': 'Embeddings',
            'completed': 'Completado',
            'failed': 'Fallido'
        };
        return labels[status] || status;
    },

    calculateDuration(job) {
        if (!job.completed_at) {
            if (job.status === 'extracting_text' || job.status === 'generating_embeddings') return 'En proceso...';
            return '-';
        }

        const start = new Date(job.created_at);
        const end = new Date(job.completed_at);
        const diff = Math.floor((end - start) / 1000); // seconds

        if (diff < 60) return `${diff}s`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
        return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
    },

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // seconds

        if (diff < 60) return 'Hace un momento';
        if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
        if (diff < 86400) return `Hace ${Math.floor(diff / 3600)} h`;

        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    async refreshJobs() {
        document.getElementById('jobs-container').innerHTML = `
            <div class="loading-spinner"></div>
            <p style="text-align: center; color: var(--text-secondary);">Actualizando...</p>
        `;
        await this.loadJobs();
    }
};

// Make globally accessible
window.JobsPage = JobsPage;
