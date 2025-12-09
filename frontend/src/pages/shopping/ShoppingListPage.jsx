// src/pages/shopping/ShoppingListPage.jsx
import React, { useEffect, useState } from "react";
import {
  getShoppingList,
  addShoppingItem,
  removeShoppingItem,
  getRecommendations,
  createOrder,
} from "../../api/shopping";

import { getUserFridges } from "../../api/fridge"; // ⬅ 新增：取得使用者冰箱

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

  // 🧊 使用者冰箱
  const [fridges, setFridges] = useState([]);
  const [selectedFridge, setSelectedFridge] = useState("");

  const load = async () => {
    const data = await getShoppingList();
    setItems(data);
  };

  useEffect(() => {
    load();

    // load fridges
    const loadFridges = async () => {
      const list = await getUserFridges();
      setFridges(list);

      // 預設第一個冰箱
      if (list.length > 0) setSelectedFridge(list[0].fridge_id);
    };

    loadFridges();
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
        it.needed_by
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
  // 🛒 提交訂單（加入 fridge 選擇）
  // -----------------------------------------------------
  const submitOrder = async () => {
    if (!selectedFridge) {
      alert("Please select a fridge before ordering.");
      return;
    }

    if (orderItems.length === 0) {
      alert("No items selected for order.");
      return;
    }

    const payload = {
      fridge_id: selectedFridge, // ⬅ 使用者選的冰箱
      items: orderItems.map((p) => ({
        external_sku: p.external_sku,
        partner_id: p.partner_id, // 後端需要 partner_id!
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
        {/* existing input fields... */}

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

          <ul>
            {recData.products.map((p, idx) => (
              <li key={idx}>
                <strong>{p.product_name}</strong> — ${p.current_price} <br />
                Partner: {p.partner_name} <br />
                <button className="btn-primary" onClick={() => addOrderItem(p)}>
                  Add to Order Preview
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* -------------------------------------------------- */}
      {/* 🧊 冰箱選擇器 — 新增 */}
      {/* -------------------------------------------------- */}
      {orderItems.length > 0 && (
        <div className="panel">
          <h3>Select a Fridge</h3>

          <select
            value={selectedFridge}
            onChange={(e) => setSelectedFridge(e.target.value)}
          >
            {fridges.map((f) => (
              <option value={f.fridge_id} key={f.fridge_id}>
                {f.fridge_name}
              </option>
            ))}
          </select>
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
