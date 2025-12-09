// src/pages/admin/AdminOrders.jsx

import React, { useEffect, useState } from "react";
import { getAllOrders, updateOrderStatus } from "../../api/admin";

// 金額字串格式化（後端是 Decimal very long string）
const formatPrice = (value) => {
  if (!value) return "0";
  try {
    return Number(value).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  } catch {
    return value; // 如果轉換失敗就原樣輸出
  }
};

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  // pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10); // 可調整每頁顯示筆數

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const data = await getAllOrders();
      setOrders(data || []);
      setCurrentPage(1); // 重新載入時回到第一頁
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (orderId, newStatus) => {
    await updateOrderStatus(orderId, newStatus);
    alert("Order status updated!");
    loadOrders();
  };

  // pagination calculation
  const totalPages =
    orders.length === 0 ? 1 : Math.ceil(orders.length / pageSize);

  const currentItems = orders.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const formatDateTime = (t) =>
    t ? new Date(t).toLocaleString("zh-TW", { hour12: false }) : "—";

  return (
    <div style={{ padding: "20px" }}>
      <h2>🧾 訂單管理</h2>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
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
            <div>共 {orders.length} 筆訂單</div>

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

          {/* 訂單列表（分頁後） */}
          {currentItems.length === 0 ? (
            <p>目前沒有訂單。</p>
          ) : (
            currentItems.map((o) => (
              <div
                key={o.order_id}
                className="card"
                style={{ marginBottom: 20, paddingBottom: 12 }}
              >
                <h3>
                  訂單 #{o.order_id} —{" "}
                  <span
                    style={{
                      color:
                        o.order_status === "Cancelled"
                          ? "red"
                          : o.order_status === "Delivered"
                          ? "green"
                          : "gray",
                    }}
                  >
                    {o.order_status}
                  </span>
                </h3>

                <p>
                  <strong>使用者：</strong> {o.user_id}
                </p>

                <p>
                  <strong>合作商：</strong> {o.partner_name}
                </p>

                <p>
                  <strong>下單時間：</strong> {formatDateTime(o.order_date)}
                </p>

                <p>
                  <strong>預計到貨：</strong>{" "}
                  {o.expected_arrival || "未設定"}
                </p>

                <p>
                  <strong>總金額：</strong> NT$ {formatPrice(o.total_price)}
                </p>

                {/* ---------- 訂單品項 ---------- */}
                <h4 style={{ marginTop: 12 }}>商品內容</h4>

                {(!o.items || o.items.length === 0) ? (
                  <p className="muted">（沒有商品資訊）</p>
                ) : (
                  <ul style={{ paddingLeft: 20, marginTop: 4 }}>
                    {o.items.map((it, idx) => (
                      <li key={idx} style={{ marginBottom: 6 }}>
                        <strong>{it.product_name}</strong>（x{it.quantity}） — 小計
                        NT$ {formatPrice(it.subtotal)}
                      </li>
                    ))}
                  </ul>
                )}

                {/* ---------- 修改狀態 ---------- */}
                <div style={{ marginTop: 15 }}>
                  <label>
                    <strong>修改訂單狀態：</strong>
                  </label>
                  <br />
                  <select
                    value={o.order_status}
                    onChange={(e) => handleUpdate(o.order_id, e.target.value)}
                    style={{ marginTop: 8 }}
                  >
                    <option>Pending</option>
                    <option>Processing</option>
                    <option>Shipped</option>
                    <option>Delivered</option>
                    <option>Cancelled</option>
                  </select>
                </div>
              </div>
            ))
          )}

          {/* ---------- Pagination Buttons ---------- */}
          {orders.length > 0 && totalPages > 1 && (
            <div
              style={{
                marginTop: 20,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "12px",
              }}
            >
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
              >
                上一頁
              </button>

              <span>
                第 {currentPage} / {totalPages} 頁
              </span>

              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
              >
                下一頁
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
