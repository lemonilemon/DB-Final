// src/pages/admin/AdminDashboard.jsx
import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import AdminIngredients from "./AdminIngredients";
import AdminPartners from "./AdminPartners";
import AdminOrders from "./AdminOrders";
import AdminUsers from "./AdminUsers";
import AdminAnalytics from "./AdminAnalytics";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("ingredients");

  if (!user) return null; // 理論上會被 ProtectedRoute 擋掉

  return (
    <div className="page">
      <h1>Admin Dashboard</h1>
      <p className="muted">
        Signed in as <strong>{user.username}</strong> ({user.roles?.join(", ")})
      </p>

      {/* 簡單的 tab 切換 */}
      <div className="tabs" style={{ marginBottom: "20px" }}>
        <button
          className={tab === "ingredients" ? "tab active" : "tab"}
          onClick={() => setTab("ingredients")}
        >
          食材管理
        </button>
        <button
          className={tab === "orders" ? "tab active" : "tab"}
          onClick={() => setTab("orders")}
        >
          訂單管理
        </button>
        <button
          className={tab === "partners" ? "tab active" : "tab"}
          onClick={() => setTab("partners")}
        >
          合作夥伴 / 商品
        </button>
        <button
          className={tab === "users" ? "tab active" : "tab"}
          onClick={() => setTab("users")}
        >
          使用者管理
        </button>
        <button
          className={tab === "analytics" ? "tab active" : "tab"}
          onClick={() => setTab("analytics")}
        >
          系統分析 Analytics
        </button>
        {/* <button
          className={tab === "more" ? "tab active" : "tab"}
          onClick={() => setTab("more")}
        >
          其他（使用者 / 食譜 / 統計）
        </button> */}
      </div>

      {tab === "ingredients" && <AdminIngredients />}
      {tab === "orders" && <AdminOrders />}
      {tab === "partners" && <AdminPartners />}
      {tab === "users" && <AdminUsers />}
      {tab === "analytics" && <AdminAnalytics />}

      {/* {tab === "more" && (
        <div className="card">
          <h2>其他 Admin 功能（目前後端未提供 API）</h2>
          <ul>
            <li>查詢所有使用者活動紀錄（需要 /api/admin/users 之類的 API）</li>
            <li>管理所有使用者的食譜與評論（需要 /api/admin/recipes /comments）</li>
            <li>熱銷食材 / 熱門食譜統計（需要報表 / analytics API）</li>
          </ul>
          <p className="muted">
            這些功能前端可以先設計 UI，但沒有對應的後端 endpoint 前，沒辦法真的撈到資料。
          </p>
        </div>
      )} */}
    </div>
  );
}


