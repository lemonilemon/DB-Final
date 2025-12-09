// src/pages/admin/AdminAnalytics.jsx

import React, { useEffect, useState } from "react";
import {
  getUserActivity,
  getRecentActions,
  getEndpointStats,
  getSearchTrends,
} from "../../api/analytics";

export default function AdminAnalytics() {
  const [activity, setActivity] = useState(null);
  const [recentActions, setRecentActions] = useState([]);
  const [apiStats, setApiStats] = useState(null);
  const [searchTrends, setSearchTrends] = useState(null);

  const [endpoint, setEndpoint] = useState("/api/recipes");
  const [method, setMethod] = useState("GET");

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    const a1 = await getUserActivity(30);
    const a2 = await getRecentActions(20);
    const a3 = await getEndpointStats(endpoint, method, 7);
    const a4 = await getSearchTrends(30);

    setActivity(a1);
    setRecentActions(a2);
    setApiStats(a3);
    setSearchTrends(a4);
  };

  const refreshEndpointStats = async () => {
    const stats = await getEndpointStats(endpoint, method, 7);
    setApiStats(stats);
  };

  return (
    <div>
      <h2>系統分析 Analytics</h2>

      {/* ============== User Activity ============== */}
      <div className="card">
        <h3>用戶活動統計</h3>
        {activity ? (
          <pre>{JSON.stringify(activity, null, 2)}</pre>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      {/* ============== Recent Actions ============== */}
      <div className="card">
        <h3>最近活動</h3>
        {recentActions.length === 0 ? (
          <p>無紀錄</p>
        ) : (
          <pre>{JSON.stringify(recentActions, null, 2)}</pre>
        )}
      </div>

      {/* ============== Endpoint Stats ============== */}
      <div className="card">
        <h3>API Endpoint Statistics</h3>

        <label>
          Endpoint：
          <input
            type="text"
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            style={{ marginLeft: 8 }}
          />
        </label>

        <label style={{ marginLeft: 20 }}>
          Method：
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            style={{ marginLeft: 8 }}
          >
            <option>GET</option>
            <option>POST</option>
            <option>PUT</option>
            <option>DELETE</option>
          </select>
        </label>

        <button style={{ marginLeft: 20 }} onClick={refreshEndpointStats}>
          Refresh
        </button>

        {apiStats ? (
          <pre style={{ marginTop: 15 }}>
            {JSON.stringify(apiStats, null, 2)}
          </pre>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      {/* ============== Search Trends ============== */}
      <div className="card">
        <h3>搜尋趨勢</h3>

        {searchTrends ? (
          <pre>{JSON.stringify(searchTrends, null, 2)}</pre>
        ) : (
          <p>Loading...</p>
        )}
      </div>
    </div>
  );
}
