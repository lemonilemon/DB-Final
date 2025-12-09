import axios from "axios";

// 後端位址
const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
});

// ⭐ 每次 request 動態從 sessionStorage 取 token（每個分頁獨立）
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem("nf_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
