import React, { useEffect, useState } from "react";
import {
  getShoppingList,
  addShoppingItem,
  removeShoppingItem,
} from "../../api/shopping";
import { createOrdersFromList } from "../../api/orders";

export default function ShoppingListPage() {
  const [items, setItems] = useState([]);

  const [orderResult, setOrderResult] = useState(null);

  // 新增項目表單
  const [newItem, setNewItem] = useState({
    ingredient_id: "",
    quantity_to_buy: 1,
  });

  const load = async () => {
    const data = await getShoppingList();
    setItems(data);
  };

  useEffect(() => {
    load();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();

    if (!newItem.ingredient_id) {
      alert("Please enter ingredient ID");
      return;
    }

    const payload = {
      ingredient_id: Number(newItem.ingredient_id),
      quantity_to_buy: Number(newItem.quantity_to_buy),
    };

    await addShoppingItem(payload);

    setNewItem({
      ingredient_id: "",
      quantity_to_buy: 1,
    });

    await load();
  };

  const handleRemove = async (ingredient_id) => {
    await removeShoppingItem(ingredient_id);
    await load();
  };

  const handleCreateOrders = async () => {
    if (items.length === 0) {
      alert("Shopping list is empty!");
      return;
    }

    try {
      const result = await createOrdersFromList();
      setOrderResult(result);
      await load(); // shopping list is cleared by backend
    } catch (e) {
      console.error(e);
      alert("Failed to create orders.");
    }
  };

  return (
    <div className="page">
      <h1>Shopping List</h1>

      {/* Add New Item */}
      <form onSubmit={handleAdd} className="inline-form">
        <input
          type="number"
          placeholder="Ingredient ID"
          value={newItem.ingredient_id}
          onChange={(e) =>
            setNewItem((i) => ({ ...i, ingredient_id: e.target.value }))
          }
          style={{ width: 140 }}
        />

        <input
          type="number"
          min="1"
          placeholder="Quantity"
          value={newItem.quantity_to_buy}
          onChange={(e) =>
            setNewItem((i) => ({
              ...i,
              quantity_to_buy: Number(e.target.value),
            }))
          }
          style={{ width: 100 }}
        />

        <button className="btn-primary">Add / Update</button>
      </form>

      {/* Shopping List */}
      <ul className="list">
        {items.map((it) => (
          <li key={it.ingredient_id} className="list-item">
            <span>
              <strong>ID {it.ingredient_id}</strong> — {it.ingredient_name} :{" "}
              {it.quantity_to_buy} {it.standard_unit}
            </span>

            <button
              className="btn-link danger"
              onClick={() => handleRemove(it.ingredient_id)}
            >
              remove
            </button>
          </li>
        ))}
      </ul>

      {/* Create Orders from Shopping List */}
      <button
        className="btn-primary"
        style={{ marginTop: "20px" }}
        onClick={handleCreateOrders}
      >
        Create Orders from Shopping List
      </button>

      {/* Order Creation Result */}
      {orderResult && (
        <div style={{ marginTop: "25px", padding: "15px", border: "1px solid #ccc" }}>
          <h3>Orders Created</h3>
          <p><strong>Total Partners:</strong> {orderResult.total_partners}</p>
          <p><strong>Total Orders:</strong> {orderResult.orders_created}</p>
          <p><strong>Total Amount:</strong> {orderResult.total_amount}</p>

          <h4 style={{ marginTop: "10px" }}>Order Details</h4>
          <ul>
            {orderResult.orders.map((o) => (
              <li key={o.order_id} style={{ marginBottom: "20px" }}>
                <strong>Order #{o.order_id}</strong> — Partner: {o.partner_name}<br />
                Arrival: {o.expected_arrival} | Status: {o.order_status}
                <ul>
                  {o.items.map((it, idx) => (
                    <li key={idx}>
                      {it.product_name} — {it.quantity} × {it.deal_price}
                      <br />
                      Subtotal: {it.subtotal}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>

          <button
            className="btn-link danger"
            onClick={() => setOrderResult(null)}
            style={{ marginTop: "10px" }}
          >
            Clear Result
          </button>
        </div>
      )}
    </div>
  );
}
