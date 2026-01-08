export interface SonqoConfig {
    apiKey: string;
    baseUrl?: string;
}

export interface RagQueryOptions {
    collection: string;
    query: string;
    topK?: number;
}

export interface SearchResult {
    text: string;
    document_id: string;
    metadata: Record<string, any>;
    score?: number;
}

export interface RagResponse {
    answer: string;
    sources: SearchResult[];
}
