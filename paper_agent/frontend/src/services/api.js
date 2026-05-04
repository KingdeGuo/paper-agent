import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
    return Promise.reject(error);
  }
);

// Get selected model
const getSelectedModel = () => {
  return localStorage.getItem('selectedModel') || 'openai';
};

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export const login = async (credentials) => {
  const response = await api.post('/users/login', credentials);
  return response.data;
};

export const register = async (userData) => {
  const response = await api.post('/users/register', userData);
  return response.data;
};

export const getMe = async () => {
  const response = await api.get('/users/me');
  return response.data;
};

export const updateMe = async (data) => {
  const response = await api.put('/users/me', data);
  return response.data;
};

export const createApiKey = async (data) => {
  const response = await api.post('/users/api-keys', data);
  return response.data;
};

export const listApiKeys = async () => {
  const response = await api.get('/users/api-keys');
  return response.data;
};

export const deleteApiKey = async (keyId) => {
  const response = await api.delete(`/users/api-keys/${keyId}`);
  return response.data;
};

// ---------------------------------------------------------------------------
// Documents API
// ---------------------------------------------------------------------------

export const documentsAPI = {
  upload: async (file, metadata = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata.title) formData.append('title', metadata.title);
    if (metadata.authors) formData.append('authors', Array.isArray(metadata.authors) ? metadata.authors.join(', ') : metadata.authors);
    if (metadata.year) formData.append('year', metadata.year.toString());
    if (metadata.keywords) formData.append('keywords', Array.isArray(metadata.keywords) ? metadata.keywords.join(', ') : metadata.keywords);
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: { model: getSelectedModel() },
    });
    return response.data;
  },

  getAll: async (params = {}) => {
    const response = await api.get('/documents', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/documents/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/documents/${id}`);
    return response.data;
  },

  download: async (id) => {
    const response = await api.get(`/documents/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  getText: async (id) => {
    const response = await api.get(`/documents/${id}/text`);
    return response.data;
  },

  getChunks: async (id) => {
    const response = await api.get(`/documents/${id}/chunks`);
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Search API
// ---------------------------------------------------------------------------

export const searchAPI = {
  search: async (query) => {
    const response = await api.post('/search', { ...query, model: getSelectedModel() });
    return response.data;
  },

  simpleSearch: async (query, params = {}) => {
    const response = await api.get('/search/simple', {
      params: { q: query, model: getSelectedModel(), ...params },
    });
    return response.data;
  },

  advancedSearch: async (query, params = {}) => {
    const response = await api.get('/search/advanced', {
      params: { q: query, model: getSelectedModel(), ...params },
    });
    return response.data;
  },

  similar: async (documentId, limit = 5) => {
    const response = await api.get(`/search/similar/${documentId}`, {
      params: { limit, model: getSelectedModel() },
    });
    return response.data;
  },

  recommendations: async (limit = 5) => {
    const response = await api.get('/search/recommendations', {
      params: { limit, model: getSelectedModel() },
    });
    return response.data;
  },

  trending: async (limit = 10) => {
    const response = await api.get('/search/trending', {
      params: { limit, model: getSelectedModel() },
    });
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Summary API
// ---------------------------------------------------------------------------

export const summaryAPI = {
  generate: async (documentId, maxLength = 300, style = 'academic') => {
    const response = await api.post('/summary/generate', {
      document_id: documentId,
      max_length: maxLength,
      style: style,
      model: getSelectedModel(),
    });
    return response.data;
  },

  get: async (documentId) => {
    const response = await api.get(`/summary/${documentId}`);
    return response.data;
  },

  regenerate: async (documentId, maxLength = 300, style = 'academic') => {
    const response = await api.post('/summary/regenerate', {
      document_id: documentId,
      max_length: maxLength,
      style: style,
      model: getSelectedModel(),
    });
    return response.data;
  },

  answerQuestion: async (documentId, question) => {
    const response = await api.post('/summary/question', {
      document_id: documentId,
      question: question,
      model: getSelectedModel(),
    });
    return response.data;
  },

  // Streaming versions
  generateStreaming: async function* (documentId, maxLength = 300, style = 'academic') {
    const response = await fetch(`${API_BASE_URL}/summary/generate-streaming`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify({
        document_id: documentId,
        max_length: maxLength,
        style: style,
        model: getSelectedModel(),
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        yield chunk;
      }
    } finally {
      reader.releaseLock();
    }
  },

  answerQuestionStreaming: async function* (documentId, question) {
    const response = await fetch(`${API_BASE_URL}/summary/question-streaming`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify({
        document_id: documentId,
        question: question,
        model: getSelectedModel(),
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        yield chunk;
      }
    } finally {
      reader.releaseLock();
    }
  },
};

// ---------------------------------------------------------------------------
// Knowledge Graph API
// ---------------------------------------------------------------------------

export const knowledgeAPI = {
  getDocumentGraph: async (documentId, depth = 1) => {
    const response = await api.get(`/knowledge/graph/${documentId}`, {
      params: { depth },
    });
    return response.data;
  },

  getGlobalGraph: async (limit = 100) => {
    const response = await api.get('/knowledge/graph/global', {
      params: { limit },
    });
    return response.data;
  },

  getVisualization: async (documentId = null) => {
    const params = documentId ? { document_id: documentId } : {};
    const response = await api.get('/knowledge/graph/visualization', { params });
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/knowledge/graph/stats');
    return response.data;
  },

  analyzeDocument: async (documentId) => {
    const response = await api.post(`/knowledge/analyze/${documentId}`);
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// arXiv API
// ---------------------------------------------------------------------------

export const arxivAPI = {
  search: async (query, maxResults = 10) => {
    const response = await api.get('/arxiv/search', {
      params: { query, max_results: maxResults }
    });
    return response.data;
  },

  searchByAuthor: async (author, maxResults = 10) => {
    const response = await api.get('/arxiv/author/' + author, {
      params: { max_results: maxResults }
    });
    return response.data;
  },

  searchByTitle: async (title, maxResults = 5) => {
    const response = await api.get('/arxiv/search', {
      params: { query: `ti:"${title}"`, max_results: maxResults }
    });
    return response.data;
  },

  searchByCategory: async (category, maxResults = 20) => {
    const response = await api.get('/arxiv/category/' + category, {
      params: { max_results: maxResults }
    });
    return response.data;
  },

  getPaper: async (arxivId) => {
    const response = await api.get('/arxiv/paper/' + arxivId);
    return response.data;
  },

  getPdfUrl: async (arxivId) => {
    const response = await api.get('/arxiv/pdf/' + arxivId);
    return response.data;
  },

  getDailyPapers: async (category = 'cs.AI', maxResults = 50) => {
    const response = await api.get('/arxiv/daily/' + category, {
      params: { max_results: maxResults }
    });
    return response.data;
  },

  importPaper: async (arxivId) => {
    const response = await api.post('/arxiv/import/' + arxivId);
    return response.data;
  }
};

// ---------------------------------------------------------------------------
// System API
// ---------------------------------------------------------------------------

export const systemAPI = {
  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },  
  getSupportedModels: async () => {
    try {
      const response = await api.get('/system/models');
      return response.data?.models || [];
    } catch {
      return [
        { id: 'openai', name: 'OpenAI GPT' },
        { id: 'qwen', name: 'Qwen (通义千问)' },
        { id: 'deepseek', name: 'DeepSeek' },
        { id: 'ollama', name: 'Ollama' },
        { id: 'anthropic', name: 'Anthropic Claude' },
        { id: 'huggingface', name: 'HuggingFace Transformers' }
      ];
    }
  }
};

export const annotationsAPI = {
  getAnnotations: async (documentId, page = null) => {
    const response = await api.get(`/annotations/${documentId}`, { params: { page } });
    return response.data;
  },

  createAnnotation: async (documentId, data) => {
    const response = await api.post(`/annotations/${documentId}`, data);
    return response.data;
  },

  updateAnnotation: async (annotationId, data) => {
    const response = await api.put(`/annotations/${annotationId}`, data);
    return response.data;
  },

  deleteAnnotation: async (annotationId) => {
    const response = await api.delete(`/annotations/${annotationId}`);
    return response.data;
  },

  getNotes: async (documentId) => {
    const response = await api.get(`/annotations/${documentId}/notes`);
    return response.data;
  },

  createNote: async (documentId, data) => {
    const response = await api.post(`/annotations/${documentId}/notes`, data);
    return response.data;
  },
};

export default api;
