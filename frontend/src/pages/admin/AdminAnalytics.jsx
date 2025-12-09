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

  // ⭐ 分頁 state
  const [pageSize, setPageSize] = useState(5);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setActivity(await getUserActivity(30));
    setRecentActions(await getRecentActions(20));
    setApiStats(await getEndpointStats(endpoint, method, 7));
    setSearchTrends(await getSearchTrends(30));
  };

  const refreshEndpointStats = async () => {
    const stats = await getEndpointStats(endpoint, method, 7);
    setApiStats(stats);
  };

  const formatDate = (t) =>
    new Date(t).toLocaleString("zh-TW", { hour12: false });

  // ⭐ 分頁計算
  const totalPages = Math.ceil(recentActions.length / pageSize);
  const paginatedActions = recentActions.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div style={{ padding: "20px" }}>
      <h2>📊 系統分析 Analytics</h2>

      {/* ================== 用戶活動統計 ================== */}
      <div className="card">
        <h3>👤 用戶活動統計</h3>

        {!activity ? (
          <p>Loading...</p>
        ) : (
          <table className="table">
            <tbody>
              <tr>
                <th>期間</th>
                <td>
                  {formatDate(activity.period_start)} —{" "}
                  {formatDate(activity.period_end)}
                </td>
              </tr>
              <tr>
                <th>總活動次數</th>
                <td>{activity.total_actions}</td>
              </tr>
              <tr>
                <th>活動類型統計</th>
                <td>
                  {Object.entries(activity.actions_by_type).length === 0
                    ? "無資料"
                    : Object.entries(activity.actions_by_type).map(([k, v]) => (
                        <div key={k}>
                          {k}：{v}
                        </div>
                      ))}
                </td>
              </tr>
              <tr>
                <th>最常查看的食譜</th>
                <td>
                  {activity.most_viewed_recipes.length === 0 ? (
                    "無資料"
                  ) : (
                    <ul>
                      {activity.most_viewed_recipes.map((r) => (
                        <li key={r.recipe_id}>
                          {r.recipe_name}（{r.view_count} 次）
                        </li>
                      ))}
                    </ul>
                  )}
                </td>
              </tr>
              <tr>
                <th>最常烹飪的食譜</th>
                <td>
                  {activity.most_cooked_recipes.length === 0 ? (
                    "無資料"
                  ) : (
                    <ul>
                      {activity.most_cooked_recipes.map((r) => (
                        <li key={r.recipe_id}>
                          {r.recipe_name}（{r.cook_count} 次）
                        </li>
                      ))}
                    </ul>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        )}
      </div>

      {/* ================== 最近活動紀錄（含分頁 + 分隔線） ================== */}
      <div className="card">
        <h3>🕒 最近活動紀錄</h3>

        {recentActions.length === 0 ? (
          <p>無活動紀錄</p>
        ) : (
          <>
            {/* PageSize 選擇器 */}
            <div style={{ marginBottom: 12 }}>
              <label>
                每頁顯示：
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  style={{ marginLeft: 8 }}
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                </select>
                筆
              </label>
            </div>

            {/* ⭐ 美化過的分隔卡片列表 */}
            <div className="list">
              {paginatedActions.map((log, index) => (
                <div key={log._id} style={{ marginBottom: "16px" }}>
                  <div className="log-card">
                    <div>
                      <strong>類型：</strong> {log.action_type}
                    </div>
                    <div>
                      <strong>時間：</strong> {formatDate(log.timestamp)}
                    </div>
                    <div>
                      <strong>使用者：</strong> {log.metadata?.user_name}（
                      {log.metadata?.role}）
                    </div>
                  </div>

                  {/* ⭐ 自動加入分隔線（最後一筆不加入） */}
                  {index !== paginatedActions.length - 1 && (
                    <hr style={{ border: "0.5px solid #ccc", marginTop: 12 }} />
                  )}
                </div>
              ))}
            </div>

            {/* ⭐ 分頁按鈕 */}
            <div style={{ marginTop: 12, display: "flex", alignItems: "center" }}>
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => p - 1)}
              >
                上一頁
              </button>

              <span style={{ margin: "0 12px" }}>
                第 {currentPage} / {totalPages} 頁
              </span>

              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
              >
                下一頁
              </button>
            </div>
          </>
        )}
      </div>

      {/* ================== API 統計 ================== */}
      <div className="card">
        <h3>🔌 API Endpoint Statistics</h3>

        <div style={{ marginBottom: 10 }}>
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
            重新整理
          </button>
        </div>

        {!apiStats ? (
          <p>Loading...</p>
        ) : (
          <table className="table">
            <tbody>
              <tr>
                <th>期間</th>
                <td>
                  {formatDate(apiStats.period_start)} —{" "}
                  {formatDate(apiStats.period_end)}
                </td>
              </tr>
              <tr>
                <th>總請求數</th>
                <td>{apiStats.total_requests}</td>
              </tr>
              <tr>
                <th>平均回應時間</th>
                <td>{apiStats.avg_response_time_ms} ms</td>
              </tr>
              <tr>
                <th>成功率</th>
                <td>{(apiStats.success_rate * 100).toFixed(1)}%</td>
              </tr>
              <tr>
                <th>Status Code 分佈</th>
                <td>
                  {Object.entries(apiStats.status_code_distribution).length === 0
                    ? "無資料"
                    : Object.entries(apiStats.status_code_distribution).map(
                        ([code, count]) => (
                          <div key={code}>
                            {code}：{count} 次
                          </div>
                        )
                      )}
                </td>
              </tr>
            </tbody>
          </table>
        )}
      </div>

      {/* ================== 搜尋趨勢 ================== */}
      <div className="card">
        <h3>🔍 搜尋趨勢</h3>

        {!searchTrends ? (
          <p>Loading...</p>
        ) : (
          <>
            <p>
              期間：{formatDate(searchTrends.period_start)} —{" "}
              {formatDate(searchTrends.period_end)}
            </p>

            <h4>熱門搜尋</h4>
            {searchTrends.top_queries.length === 0 ? (
              <p>無熱門搜尋</p>
            ) : (
              <ul>
                {searchTrends.top_queries.map((q, i) => (
                  <li key={i}>
                    {q.query}（{q.count} 次）
                  </li>
                ))}
              </ul>
            )}

            <h4>依類型統計</h4>
            {Object.entries(searchTrends.queries_by_type).length === 0 ? (
              <p>無搜尋紀錄</p>
            ) : (
              Object.entries(searchTrends.queries_by_type).map(([k, v]) => (
                <div key={k}>
                  {k}：{v}
                </div>
              ))
            )}

            <p style={{ marginTop: 10 }}>
              平均回傳數量：{searchTrends.avg_results_per_query}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
