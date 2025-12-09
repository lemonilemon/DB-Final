import React, { useEffect, useState } from "react";
import { getOrders, cancelOrder, confirmDelivery } from "../../api/orders";

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);

  const formatDate = (isoString) => {
    if (!isoString) return "-";
    const d = new Date(isoString);
    return d.toLocaleString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };


  const load = async () => {
    const data = await getOrders();
    setOrders(data);
  };

  useEffect(() => {
    load();
  }, []);

  const handleCancel = async (orderId) => {
    await cancelOrder(orderId);
    await load();
  };

  const handleConfirm = async (orderId) => {
    await confirmDelivery(orderId);
    await load();
  };

  return (
    <div className="page">
      <h1>Orders</h1>

      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Partner</th>
            <th>Total</th>
            <th>Status</th>
            <th>Actions</th>
            <th>Updated</th>
          </tr>
        </thead>

        <tbody>
          {orders.map((o) => (
            <tr key={o.order_id}>
              <td>{o.order_id}</td>
              <td>{o.partner_name}</td>
              <td>{o.total_price}</td>
              <td>{o.order_status}</td>

              <td>
                {/* Pending → 可取消 */}
                {o.order_status === "Pending" && (
                  <button
                    className="btn-danger"
                    onClick={() => handleCancel(o.order_id)}
                  >
                    Cancel
                  </button>
                )}

                {/* Shipped → 可確認送達 */}
                {o.order_status === "Shipped" && (
                  <button
                    className="btn-primary"
                    onClick={() => handleConfirm(o.order_id)}
                  >
                    Confirm Delivery
                  </button>
                )}

                {/* 其他狀態 → 無按鈕 */}
                {["Processing", "Delivered", "Cancelled"].includes(
                  o.order_status
                ) && <span>—</span>}
              </td>

              <td>{formatDate(o.order_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
