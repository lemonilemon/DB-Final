import React, { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, register as apiRegister } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);      
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // ⭐ 改為從 sessionStorage 讀取登入資料（每個 tab 獨立）
  useEffect(() => {
    const savedToken = sessionStorage.getItem("nf_token");
    const savedUser = sessionStorage.getItem("nf_user");

    if (savedToken && savedUser) {
      setToken(savedToken);
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        setUser(null);
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = async (username, password) => {
    const res = await apiLogin({ username, password });

    const accessToken = res.access_token;

    // ⭐ 將後端單一字串 role → 陣列 roles
    const roles = [res.role];

    const userInfo = {
      username: res.user_name,
      user_id: res.user_id,
      roles,
    };

    console.log("🔥 login response in context:", res);
    console.log("🔥 parsed userInfo:", userInfo);

    setToken(accessToken);
    setUser(userInfo);

    // ⭐ 儲存在 sessionStorage（不會跨分頁互相覆蓋）
    sessionStorage.setItem("nf_token", accessToken);
    sessionStorage.setItem("nf_user", JSON.stringify(userInfo));
  };

  const handleRegister = async (data) => {
    await apiRegister(data);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    sessionStorage.removeItem("nf_token");
    sessionStorage.removeItem("nf_user");
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token,
    login: handleLogin,
    register: handleRegister,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
