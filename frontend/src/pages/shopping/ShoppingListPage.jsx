// src/pages/shopping/ShoppingListPage.jsx
import React, { useEffect, useState } from "react";
import {
  getShoppingList,
  addShoppingItem,
  removeShoppingItem,
  getRecommendations,
  createOrder,
} from "../../api/shopping";

export default function ShoppingListPage() {
  const today = new Date().toISOString().slice(0, 10);

  const [items, setItems] = useState([]);

  // 訂單 preview
  const [orderItems, setOrderItems] = useState([]);
  const [orderResult, setOrderResult] = useState(null);

  // Add Item Form
  const [newItem, setNewItem] = useState({
    ingredient_id: "",
    quantity_to_buy: 1,
    needed_by: today,
  });

  const [recData, setRecData] = useState(null);
  const [loadingRec, setLoadingRec] = useState(false);

  const load = async () => {
    const data = await getShoppingList();
    setItems(data);
  };

  useEffect(() => {
    load();
  }, []);

  // -------------------------------
  // ➕ Add Item to Shopping List
  // -------------------------------
  const handleAdd = async (e) => {
    e.preventDefault();

    if (!newItem.ingredient_id) {
      alert("Please enter ingredient ID");
      return;
    }

    const payload = {
      ingredient_id: Number(newItem.ingredient_id),
      quantity_to_buy: Number(newItem.quantity_to_buy),
      needed_by: newItem.needed_by,
    };

    await addShoppingItem(payload);

    // Reset form
    setNewItem({
      ingredient_id: "",
      quantity_to_buy: 1,
      needed_by: today,
    });

    await load();
  };

  // -------------------------------
  // 🗑 Remove Shopping Item
  // -------------------------------
  const handleRemove = async (ingredient_id) => {
    await removeShoppingItem(ingredient_id);
    await load();
  };

  // -----------------------------------------------------
  // 🔍 顯示 Product Recommendations
  // -----------------------------------------------------
  const showRecommendations = async (it) => {
    setLoadingRec(true);
    try {
      const res = await getRecommendations(
        it.ingredient_id,
        it.quantity_to_buy,
        it.needed_by // 使用後端回傳的 needed_by
      );
      setRecData(res);
    } catch (err) {
      console.error(err);
      alert("Failed to fetch product recommendations");
    }
    setLoadingRec(false);
  };

  // -----------------------------------------------------
  // ➕ 加入 Order Preview
  // -----------------------------------------------------
  const addOrderItem = (product) => {
    setOrderItems((prev) => [...prev, product]);
  };

  // -----------------------------------------------------
  // 🛒 提交訂單
  // -----------------------------------------------------
  const submitOrder = async () => {
    if (orderItems.length === 0) {
      alert("No items selected for order.");
      return;
    }

    const payload = {
      fridge_id: "123e4567-e89b-12d3-a456-426614174000", // TODO: Replace with real fridge_id
      items: orderItems.map((p) => ({
        external_sku: p.external_sku,
        quantity: 1,
      })),
    };

    const result = await createOrder(payload);
    setOrderResult(result);

    setOrderItems([]);
    setRecData(null);
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
          placeholder="Qty"
          value={newItem.quantity_to_buy}
          onChange={(e) =>
            setNewItem((i) => ({
              ...i,
              quantity_to_buy: Number(e.target.value),
            }))
          }
          style={{ width: 100 }}
        />

        <input
          type="date"
          value={newItem.needed_by}
          onChange={(e) =>
            setNewItem((i) => ({ ...i, needed_by: e.target.value }))
          }
          style={{ width: 150 }}
        />

        <button className="btn-primary">Add</button>
      </form>

      {/* Shopping List Items */}
      <ul className="list">
        {items.map((it) => (
          <li key={it.ingredient_id} className="list-item">
            <span>
              <strong>{it.ingredient_name}</strong> — {it.quantity_to_buy}{" "}
              {it.standard_unit} (need by {it.needed_by})
            </span>

            <button
              className="btn-secondary"
              onClick={() => showRecommendations(it)}
            >
              Recommend Products
            </button>

            <button
              className="btn-link danger"
              onClick={() => handleRemove(it.ingredient_id)}
            >
              remove
            </button>
          </li>
        ))}
      </ul>

      {/* Recommendation Panel */}
      {recData && (
        <div className="panel">
          <h3>Recommended Products</h3>
          <p>
            Need: <strong>{recData.quantity_needed}</strong> by{" "}
            {recData.needed_by}
          </p>

          <ul>
            {recData.products.map((p, idx) => (
              <li key={idx} style={{ marginBottom: "10px" }}>
                <strong>{p.product_name}</strong> — ${p.current_price} <br />
                Partner: {p.partner_name} <br />
                Arrives: {p.expected_arrival}{" "}
                {p.expected_arrival <= recData.needed_by ? "✓" : "❌"} <br />
                <button
                  className="btn-primary"
                  onClick={() => addOrderItem(p)}
                >
                  Add to Order Preview
                </button>
              </li>
            ))}
          </ul>

          <button className="btn-link" onClick={() => setRecData(null)}>
            Close Recommendations
          </button>
        </div>
      )}

      {/* Order Preview */}
      {orderItems.length > 0 && (
        <div className="panel">
          <h3>Order Preview</h3>
          <ul>
            {orderItems.map((p, idx) => (
              <li key={idx}>
                {p.product_name} — {p.partner_name}
              </li>
            ))}
          </ul>

          <button className="btn-primary" onClick={submitOrder}>
            Submit Order
          </button>
        </div>
      )}

      {/* Order Result */}
      {orderResult && (
        <div className="panel">
          <h3>Order Created!</h3>
          <p>ID: {orderResult.order_id}</p>
          <p>Total: {orderResult.total_price}</p>
          <p>Status: {orderResult.order_status}</p>

          <button className="btn-link" onClick={() => setOrderResult(null)}>
            Clear
          </button>
        </div>
      )}
    </div>
  );
}
