// src/pages/admin/AdminOrders.jsx

import React, { useEffect, useState } from "react";
import { getOrders, updateOrderStatus } from "../../api/admin";

// 金額字串格式化
const formatPrice = (value) => {
  if (!value) return "0";
  try {
    return Number(value).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  } catch {
    return value;
  }
};

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [totalOrders, setTotalOrders] = useState(0);

  const [loading, setLoading] = useState(true);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10; // 每頁顯示幾筆

  // 當 currentPage 改變時，重新抓取資料
  useEffect(() => {
    loadOrders();
  }, [currentPage]); 

  const loadOrders = async () => {
    setLoading(true);
    try {
      // 關鍵修改：傳送 limit 與 offset 給後端
      // offset = (當前頁數 - 1) * 每頁筆數
      const params = {
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
      };
      
      const data = await getAllOrders(params);
      setOrders(data);
    } catch (err) {
      console.error("Failed to load orders:", err);
      alert("無法讀取訂單列表");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders(1, pageSize); // 首次載入第 1 頁
  }, [pageSize]);

  const handleUpdate = async (orderId, newStatus) => {
    try {
      await updateOrderStatus(orderId, newStatus);
      
      // 立即更新畫面，不等待 loadOrders()
      setOrders(prev =>
        prev.map(o =>
          o.order_id === orderId ? { ...o, order_status: newStatus } : o
        )
      );
      
      alert("Order status updated!");
    } catch (err) {
      alert("Update failed");
    }
  };

  // 判斷是否還有下一頁 (如果回傳的筆數少於 pageSize，代表是最後一頁了)
  const hasNextPage = orders.length === pageSize;


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
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>訂單管理 (Server-Side Pagination)</h2>
        <span>目前頁數: {currentPage}</span>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          {/* 直接顯示 orders，不需要再 slice，因為後端已經切好了 */}
          {orders.map((o) => (
            <div key={o.order_id} className="card" style={{ marginBottom: 20 }}>
              <h3>
                訂單 #{o.order_id} —{" "}
                <span style={{ color: "gray" }}>{o.order_status}</span>
              </h3>

              <p><strong>使用者：</strong> {o.user_id}</p>
              <p><strong>合作商：</strong> {o.partner_name}</p>
              <p>
                <strong>下單時間：</strong>{" "}
                {new Date(o.order_date).toLocaleString()}
              </p>
              <p><strong>預計到貨：</strong> {o.expected_arrival}</p>
              <p><strong>總金額：</strong> NT$ {formatPrice(o.total_price)}</p>

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
          <div style={{ marginTop: 20, display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              上一頁
            </button>

            <span>第 {currentPage} 頁</span>

            <button
              disabled={!hasNextPage}
              onClick={() => setCurrentPage((p) => p + 1)}
            >
              下一頁
            </button>
          </div>
          
          <p style={{ color: "gray", fontSize: "0.9em", marginTop: 10 }}>
            * 為了效能優化，系統每次只從資料庫讀取 {pageSize} 筆資料。
          </p>
        </>
      )}
    </div>
  );
}
