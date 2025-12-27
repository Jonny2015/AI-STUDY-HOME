/** API service client for backend communication. */

import axios from "axios";

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60 seconds
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("[API] Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);
