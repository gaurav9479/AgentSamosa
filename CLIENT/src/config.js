// API Configuration
export const API_URL = import.meta.env.VITE_API_URL || '';
export const WS_URL = import.meta.env.VITE_WS_URL || '';

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  
  if (API_URL) {
    // Ensure API_URL doesn't end with slash
    const baseUrl = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
    return `${baseUrl}/${cleanEndpoint}`;
  }
  
  // Fallback to relative URL for development
  return `/${endpoint}`;
};

// Helper function to get WebSocket URL
export const getWebSocketUrl = (endpoint) => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  
  if (WS_URL) {
    const baseUrl = WS_URL.endsWith('/') ? WS_URL.slice(0, -1) : WS_URL;
    return `${baseUrl}/${cleanEndpoint}`;
  }
  
  // Fallback to localhost for development
  return `ws://${window.location.hostname}:8000/${cleanEndpoint}`;
};

