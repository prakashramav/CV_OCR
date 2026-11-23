import axios from 'axios';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_V1 = `${API_BASE_URL}/api/v1`;

const apiClient = axios.create({
  baseURL: API_V1,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Telemetry & Health
  getHealth: () => apiClient.get('/health'),
  getOverview: () => apiClient.get('/analytics/overview'),

  // Detections & Records
  getDetections: (params) => apiClient.get('/detections', { params }),
  getPlates: (params) => apiClient.get('/plates', { params }),
  getPlateById: (id) => apiClient.get(`/plates/${id}`),

  // Violations
  getViolations: (params) => apiClient.get('/violations', { params }),
  updateViolationStatus: (id, verification_status) =>
    apiClient.patch(`/violations/${id}`, { verification_status }),

  // Video Processing
  uploadVideo: (formData, onProgress) =>
    apiClient.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    }),
  getVideoStatus: (jobId) => apiClient.get(`/videos/${jobId}/status`),

  // Single Image Inference
  analyzeImage: (formData) =>
    apiClient.post('/images/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Helpers
  getImageUrl: (relativePath) => {
    if (!relativePath) return null;
    if (relativePath.startsWith('http')) return relativePath;
    return `${API_BASE_URL}/${relativePath.replace(/^\//, '')}`;
  },
  getLiveStreamUrl: () => `${API_V1}/live/stream`,
};

export default api;
