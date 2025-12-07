import React, { useEffect, useState } from "react";
import { getOrders, updateOrderStatus } from "../../api/orders";

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);

  const load = async () => {
    const data = await getOrders();
    setOrders(data);
  };

  useEffect(() => {
    load();
  }, []);

  const handleUpdate = async (orderId, status) => {
    await updateOrderStatus(orderId, status);
    await load();  // 重新取得訂單
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
            <th>Updated</th>
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
                    handleUpdate(o.order_id, e.target.value)
                  }
                >
                  <option value="Pending">Pending</option>
                  <option value="Processing">Processing</option>
                  <option value="Shipped">Shipped</option>
                  <option value="Delivered">Delivered</option>
                  <option value="Cancelled">Cancelled</option>
                </select>
              </td>

              <td>{o.order_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
