/**
 * Backend API Client Configuration
 * Direct HTTP calls to FastAPI server running on localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    "Accept": "application/json",
  };

  // Do not set Content-Type if options.body is FormData (browser will set multipart boundary automatically)
  if (!(options.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

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
