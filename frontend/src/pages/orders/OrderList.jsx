import { useEffect, useState } from "react";
import { listOrders, updateOrderStatus } from "../../api/procurement";

export default function OrderList() {
  const [orders, setOrders] = useState([]);
  const [updatingId, setUpdatingId] = useState(null);

  async function fetchOrders() {
    try {
      const data = await listOrders();
      setOrders(data);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    fetchOrders();
  }, []);

  async function handleStatusChange(orderId, status) {
    setUpdatingId(orderId);
    try {
      await updateOrderStatus(orderId, { order_status: status });
      fetchOrders();
    } catch (err) {
      console.error(err);
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div>
      <h2>Orders</h2>

      {orders.length === 0 ? (
        <p>No orders.</p>
      ) : (
        orders.map((o) => (
          <div key={o.order_id} className="card" style={{ marginBottom: 12 }}>
            <h3>
              Order #{o.order_id} · {o.partner_name}
            </h3>
            <p>Status: {o.order_status}</p>
            <p>Order date: {o.order_date}</p>
            <p>Expected arrival: {o.expected_arrival_date}</p>
            <p>Total: {o.total_amount}</p>

            <h4>Items</h4>
            <ul className="list">
              {o.items.map((it) => (
                <li key={it.external_sku}>
                  {it.product_name} — {it.quantity} @ {it.deal_price}
                </li>
              ))}
            </ul>

            <div className="form-inline">
              {["Pending", "Processing", "Shipped", "Delivered", "Cancelled"].map(
                (s) => (
                  <button
                    key={s}
                    className="btn-small"
                    disabled={updatingId === o.order_id}
                    onClick={() => handleStatusChange(o.order_id, s)}
                  >
                    {s}
                  </button>
                )
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
