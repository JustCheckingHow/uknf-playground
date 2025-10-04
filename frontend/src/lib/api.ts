import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8123/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true
});

export function setAuthToken(token?: string) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Token ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
}
