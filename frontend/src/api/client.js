import axios from "axios";

// 後端位址
const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
});

// 自動帶入 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("nf_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
