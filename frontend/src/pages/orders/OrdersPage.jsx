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

  // 專門格式化後端 Decimal 字串
  const formatPrice = (value) => {
    if (value === null || value === undefined) return "0.00";

    try {
      const num = Number(value);
      if (Number.isNaN(num)) {
        // fallback 處理超大數字：抓前幾位有效數字
        const cleaned = value.replace(/^-0+/, "").replace(/^0+/, "");
        if (!cleaned) return "0.00";
        return cleaned;
      }

      return num.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    } catch {
      return value;
    }
  };

  const load = async () => {
    const data = await getOrders();
    console.log("📦 Orders API response:", data);
    setOrders(data || []);
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
      <h1>My Orders</h1>

      {orders.length === 0 && <p>No orders found.</p>}

      <style>{`
        .table th, .table td {
          text-align: center !important;
          vertical-align: middle !important;
        }

        .order-items-container {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          padding: 8px 0;
        }

        .order-item-card {
          background: #ffffff;
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 10px 14px;
          min-width: 180px;
          max-width: 220px;
          text-align: left;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }

        .order-item-card .item-name {
          font-weight: 600;
          margin-bottom: 6px;
          text-align: center;
        }

        .order-items-label {
          font-weight: 600;
          width: 100%;
          text-align: left;   /* Items 靠左 */
          padding-left: 0.3rem;
          margin-bottom: 4px;
        }

        .order-item-card .item-line {
          font-size: 0.9rem;
          margin: 2px 0;
        }
      `}</style>

      <table className="table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Partner</th>
            <th>Total</th>
            <th>Status</th>
            <th>Expected Arrival</th>
            <th>Actions</th>
            <th>Order Date</th>
          </tr>
        </thead>

        <tbody>
          {orders.map((o) => (
            <React.Fragment key={o.order_id}>
              {/* ========= 訂單主列 ========= */}
              <tr>
                <td><strong>#{o.order_id}</strong></td>
                <td>{o.partner_name}</td>

                {/* ⭐ 使用後端 total_price */}
                <td>${formatPrice(o.total_price)}</td>

                <td>
                  <span
                    className={
                      o.order_status === "Delivered"
                        ? "badge badge-success"
                        : o.order_status === "Cancelled"
                        ? "badge badge-warning"
                        : "badge badge-info"
                    }
                  >
                    {o.order_status}
                  </span>
                </td>

                <td>{o.expected_arrival || "-"}</td>

                <td>
                  {o.order_status === "Pending" && (
                    <button className="btn-danger" onClick={() => handleCancel(o.order_id)}>
                      Cancel
                    </button>
                  )}
                  {o.order_status === "Shipped" && (
                    <button className="btn-primary" onClick={() => handleConfirm(o.order_id)}>
                      Confirm Delivery
                    </button>
                  )}
                  {["Delivered", "Cancelled"].includes(o.order_status) && <span>—</span>}
                </td>

                <td>{formatDate(o.order_date)}</td>
              </tr>

              {/* ========= Items 展開列 ========= */}
              <tr>
                <td colSpan="7" style={{ background: "#fafafa" }}>
                  <div style={{ padding: "0.5rem 1rem" }}>
                    <div className="order-items-label">Items:</div>

                    <div className="order-items-container">
                      {o.items.map((it, idx) => (
                        <div className="order-item-card" key={idx}>
                          <div className="item-name">{it.product_name}</div>

                          <div className="item-line">Qty: {it.quantity}</div>

                          <div className="item-line">
                            Unit Price: ${formatPrice(it.deal_price)}
                          </div>

                          <div className="item-line">
                            Subtotal: ${formatPrice(it.subtotal)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </td>
              </tr>
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
