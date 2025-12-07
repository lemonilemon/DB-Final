// src/api/auth.js
import api from "./client";

export const login = async ({ username, password }) => {
  const res = await api.post("/auth/login", {
    user_name: username,   // ★ 後端需要 user_name 不是 username
    password,
  });
  console.log("[login api response]", res.data);   // ★ 加這行
  return res.data;
};

export const register = async ({ username, email, password }) => {
  const res = await api.post("/auth/register", {
    user_name: username,   // ★ 後端欄位
    email: email,          // ★ 後端必填欄位
    password: password,
  });
  return res.data;
};

export const getMe = async () => {
  const res = await api.get("/api/me");
  return res.data;
};
