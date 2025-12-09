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
  const pageSize = 10;

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const data = await getAllOrders();
      setOrders(data);
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
  const totalPages = Math.ceil(orders.length / pageSize);
  const currentItems = orders.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div>
      <h2>訂單管理</h2>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          {currentItems.map((o) => (
            <div key={o.order_id} className="card" style={{ marginBottom: 20 }}>
              <h3>
                訂單 #{o.order_id} —{" "}
                <span style={{ color: "gray" }}>{o.order_status}</span>
              </h3>

              <p>
                <strong>使用者：</strong> {o.user_id}
              </p>

              <p>
                <strong>合作商：</strong> {o.partner_name}
              </p>

              <p>
                <strong>下單時間：</strong>{" "}
                {new Date(o.order_date).toLocaleString()}
              </p>

              <p>
                <strong>預計到貨：</strong> {o.expected_arrival}
              </p>

              <p>
                <strong>總金額：</strong> NT$ {formatPrice(o.total_price)}
              </p>

              {/* ---------- 訂單品項 ---------- */}
              <h4>商品內容</h4>

              {o.items.length === 0 ? (
                <p className="muted">（沒有商品資訊）</p>
              ) : (
                <ul style={{ paddingLeft: 20 }}>
                  {o.items.map((it, idx) => (
                    <li key={idx} style={{ marginBottom: 6 }}>
                      <strong>{it.product_name}</strong>  
                      （x{it.quantity}）  
                      — 小計 NT$ {formatPrice(it.subtotal)}
                    </li>
                  ))}
                </ul>
              )}

              {/* ---------- 修改狀態 ---------- */}
              <div style={{ marginTop: 15 }}>
                <label><strong>修改訂單狀態：</strong></label>
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
          ))}

          {/* ---------- Pagination Buttons ---------- */}
          {totalPages > 1 && (
            <div style={{ marginTop: 20 }}>
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
              >
                上一頁
              </button>

              <span style={{ margin: "0 12px" }}>
                Page {currentPage} / {totalPages}
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
