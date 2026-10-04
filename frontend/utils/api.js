/**
 * Backend API Client Configuration
 * Direct HTTP calls to FastAPI server running on localhost:8000
 */

export function getApiBaseUrl() {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined" && window.location.hostname) {
    return `http://${window.location.hostname}:8000/api`;
  }
  return "http://127.0.0.1:8000/api";
}

const API_BASE_URL = getApiBaseUrl();

export async function fetchApi(endpoint, options = {}) {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  const defaultHeaders = {
    "Accept": "application/json",
  };

  // Attach JWT Bearer token if present in browser storage
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("smartcity_auth_token");
    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  // Do not set Content-Type if options.body is FormData (browser will set multipart boundary automatically)
  if (!(options.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
  } catch (networkError) {
    console.error(`[API Network Error] ${url}:`, networkError);
    throw new Error(
      `Cannot connect to backend server at ${baseUrl}. Please ensure the FastAPI backend is running on port 8000.`
    );
  }

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch (e) {
      // response wasn't JSON
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export default API_BASE_URL;
