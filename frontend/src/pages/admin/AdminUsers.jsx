// src/pages/admin/AdminUsers.jsx
import React, { useEffect, useState } from "react";
import {
  getAllUsers,
  updateUserStatus,
  setUserRole,
  revokeRole,
} from "../../api/admin";

export default function AdminUsers() {
  const [users, setUsers] = useState([]);

  // 分頁相關 state
  const [pageSize, setPageSize] = useState(5);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    const data = await getAllUsers();
    setUsers(data || []);
    setCurrentPage(1); // 重新載入時回到第一頁
  };

  const toggleRole = async (u) => {
    if (u.role === "Admin") {
      await revokeRole(u.user_id, "Admin");
    } else {
      await setUserRole(u.user_id, "Admin");
    }
    loadUsers();
  };

  const toggleStatus = async (u) => {
    const newStatus = u.status === "Active" ? "Disabled" : "Active";
    await updateUserStatus(u.user_id, newStatus);
    loadUsers();
  };

  // 分頁計算
  const totalPages =
    users.length === 0 ? 1 : Math.ceil(users.length / pageSize);

  const paginatedUsers = users.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div style={{ padding: "20px" }}>
      <h2>👥 Admin - User Management</h2>

      {/* 上方控制列：總數 + 每頁顯示幾筆 */}
      <div
        style={{
          margin: "12px 0 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div>共 {users.length} 位使用者</div>

        <div>
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
      </div>

      {/* 使用者列表（分頁後） */}
      {paginatedUsers.length === 0 ? (
        <p>目前沒有使用者。</p>
      ) : (
        paginatedUsers.map((u) => (
          <div
            key={u.user_id}
            className="card"
            style={{ marginBottom: "16px", paddingBottom: "12px" }}
          >
            <p>
              <b>Name：</b> {u.user_name}
            </p>
            <p>
              <b>Email：</b> {u.email}
            </p>
            <p>
              <b>Status：</b>{" "}
              <span
                style={{
                  fontWeight: "bold",
                  color: u.status === "Active" ? "green" : "red",
                }}
              >
                {u.status}
              </span>
            </p>
            <p>
              <b>Role：</b> {u.role}
            </p>

            <div style={{ marginTop: "8px", display: "flex", gap: "8px" }}>
              <button onClick={() => toggleStatus(u)}>
                {u.status === "Active" ? "Disable" : "Activate"}
              </button>

              <button onClick={() => toggleRole(u)}>
                {u.role === "Admin" ? "Revoke Admin" : "Make Admin"}
              </button>
            </div>
          </div>
        ))
      )}

      {/* 分頁控制列 */}
      {users.length > 0 && (
        <div
          style={{
            marginTop: 12,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
          }}
        >
          <button
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage((p) => p - 1)}
          >
            上一頁
          </button>

          <span>
            第 {currentPage} / {totalPages} 頁
          </span>

          <button
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage((p) => p + 1)}
          >
            下一頁
          </button>
        </div>
      )}
    </div>
  );
}
