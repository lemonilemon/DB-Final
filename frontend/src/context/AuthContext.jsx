import React, { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, register as apiRegister } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);      // 可以放 username / role 等
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // 初次載入時從 localStorage 讀 token
  useEffect(() => {
    const savedToken = localStorage.getItem("nf_token");
    const savedUser = localStorage.getItem("nf_user");
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

    // ⭐ 將後端的 role:string → 前端 roles:array
    const roles = [res.role]; // 後端永遠是單一字串，所以包成陣列

    const userInfo = {
      username: res.user_name,
      user_id: res.user_id,
      roles,    // ⭐ Dashboard / Navbar 統一使用 roles
    };

    console.log("🔥 login response in context:", res);
    console.log("🔥 parsed userInfo:", userInfo);
    console.log("🔥 RAW roles:", res.role);


    setToken(accessToken);
    setUser(userInfo);

    console.log("🔥 AFTER setUser userInfo =", userInfo);
    console.log("🔥 AFTER setUser localStorage =", localStorage.getItem("nf_user"));


    localStorage.setItem("nf_token", accessToken);
    localStorage.setItem("nf_user", JSON.stringify(userInfo));
  };


  const handleRegister = async (data) => {
    await apiRegister(data);
    // 註冊完可以自動登入或導向 login，這邊先選導向 login，所以不自動 setToken
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("nf_token");
    localStorage.removeItem("nf_user");
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
