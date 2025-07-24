import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 获取选中的模型
const getSelectedModel = () => {
  return localStorage.getItem('selectedModel') || 'openai';
};

// Documents API
export const documentsAPI = {
  upload: async (file, metadata = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata.title) formData.append('title', metadata.title);
    if (metadata.authors) formData.append('authors', metadata.authors.join(', '));
    if (metadata.year) formData.append('year', metadata.year.toString());
    if (metadata.keywords) formData.append('keywords', metadata.keywords.join(', '));
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
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

// Search API
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

// Summary API
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

  batchGenerate: async (documentIds, maxLength = 300, style = 'academic') => {
    const response = await api.post('/summary/batch', documentIds, {
      params: { max_length: maxLength, style: style, model: getSelectedModel() },
    });
    return response.data;
  },

  getStyles: async () => {
    const response = await api.get('/summary/styles');
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

// System API
export const systemAPI = {
  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
  
  // 获取支持的模型列表
  getSupportedModels: async () => {
    return [
      { id: 'openai', name: 'OpenAI GPT' },
      { id: 'qwen', name: 'Qwen (通义千问)' },
      { id: 'deepseek', name: 'DeepSeek' },
      { id: 'ollama', name: 'Ollama' },
      { id: 'anthropic', name: 'Anthropic Claude' },
      { id: 'huggingface', name: 'HuggingFace Transformers' }
    ];
  }
};

export default api;