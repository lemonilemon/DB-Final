// src/pages/admin/AdminOrders.jsx
import React, { useEffect, useState } from "react";
import { getOrders, updateOrderStatus } from "../../api/orders";

const STATUS_OPTIONS = [
  "Pending",
  "Processing",
  "Shipped",
  "Delivered",
  "Cancelled",
];

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getOrders(); // 目前登入 user 的訂單
      setOrders(data);
    } catch (err) {
      console.error("load orders failed:", err);
      setError("無法載入訂單資料");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      await updateOrderStatus(orderId, { order_status: newStatus });
      await load();
    } catch (err) {
      console.error("update status failed:", err);
      setError("更新訂單狀態失敗");
    }
  };

  return (
    <section>
      <h2>訂單管理</h2>
      <p className="muted">
        目前後端 API 只提供「自己帳號的訂單」，所以這裡看到的是目前登入 Admin 的訂單。
        如果要管理所有使用者的訂單，需要後端再另外開 admin 專用 endpoint。
      </p>

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : orders.length === 0 ? (
        <p>目前沒有任何訂單。</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Partner</th>
              <th>Total</th>
              <th>Status</th>
              <th>Order Time</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.order_id}>
                <td>{o.order_id}</td>
                <td>{o.partner_name}</td>
                <td>{o.total_price}</td>
                <td>
                  <select
                    value={o.order_status}
                    onChange={(e) =>
                      handleStatusChange(o.order_id, e.target.value)
                    }
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td>{new Date(o.order_date).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
