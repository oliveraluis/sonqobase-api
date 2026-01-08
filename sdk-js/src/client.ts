import { SonqoConfig, RagQueryOptions, RagResponse } from './types';

export class SonqoError extends Error {
    public statusCode: number;
    public detail: any;

    constructor(message: string, statusCode: number, detail: any) {
        super(message);
        this.name = 'SonqoError';
        this.statusCode = statusCode;
        this.detail = detail;
    }
}

export class SonqoClient {
    private apiKey: string;
    private baseUrl: string;

    constructor(config: SonqoConfig) {
        this.apiKey = config.apiKey;
        this.baseUrl = config.baseUrl || 'https://sonqobase-api.onrender.com/api/v1';
    }

    private async request<T>(path: string, options: RequestInit): Promise<T> {
        const url = `${this.baseUrl}${path}`;
        const headers = new Headers(options.headers);
        headers.set('X-API-Key', this.apiKey);

        // Default fetch timeout is usually browser dependent, but for RAG we need patience.
        // Fetch doesn't have a simple timeout option, but we trust the browser/node default (usually long enough).

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            let errorMessage = response.statusText;
            let errorDetail = null;

            try {
                const errorData = await response.json();
                errorDetail = errorData.detail;

                // Handle FastAPI string detail vs list detail (validation error)
                if (typeof errorDetail === 'string') {
                    errorMessage = errorDetail;
                } else if (Array.isArray(errorDetail)) {
                    // Pydantic validation error
                    errorMessage = errorDetail.map((e: any) => `${e.loc.join('.')}: ${e.msg}`).join(', ');
                } else {
                    errorMessage = JSON.stringify(errorDetail);
                }
            } catch (e) {
                // Ignore JSON parse error if response is not JSON
            }

            throw new SonqoError(errorMessage, response.status, errorDetail);
        }

        return response.json();
    }

    /**
     * Perform a RAG query (Retrieval-Augmented Generation)
     */
    async query(options: RagQueryOptions): Promise<RagResponse> {
        const { collection, query, topK = 5 } = options;

        return this.request<RagResponse>(`/collections/${collection}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                top_k: topK,
            }),
        });
    }

    /**
     * Upload a PDF file for ingestion
     */
    async uploadPdf(collection: string, file: File | Blob, metadata?: Record<string, any>): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);
        if (metadata) {
            formData.append('metadata', JSON.stringify(metadata));
        }

        // Note: Do NOT set Content-Type header for FormData, fetch sets boundary automatically
        return this.request<any>(`/collections/${collection}/ingest/files`, {
            method: 'POST',
            body: formData,
        });
    }
}
