// src/pages/shopping/ShoppingListPage.jsx
import React, { useEffect, useState } from "react";
import {
  getShoppingList,
  addShoppingItem,
  removeShoppingItem,
  getRecommendations,
  createOrder,
  createOrdersFromShoppingList,
} from "../../api/shopping";
import { getUserFridges } from "../../api/fridge";

// ===============================
// Helpers
// ===============================

// 金額格式化
const formatPrice = (value) => {
  if (value === null || value === undefined || value === "") return "-";
  try {
    const num = Number(value);
    if (Number.isNaN(num)) return value;
    return num.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  } catch {
    return value;
  }
};

// 日期格式化
const formatDate = (isoStr) => {
  if (!isoStr) return "-";
  try {
    const d = new Date(isoStr);
    if (Number.isNaN(d.getTime())) return isoStr;
    return d.toLocaleDateString("en-CA");
  } catch {
    return isoStr;
  }
};

// 比較到貨是否來得及
const isInTime = (expectedArrival, neededBy) => {
  if (!expectedArrival || !neededBy) return false;
  return new Date(expectedArrival).getTime() <= new Date(neededBy).getTime();
};

// 需要多少個 item（無條件進位）
const itemsNeeded = (neededQty, unitQty) => {
  const need = Number(String(neededQty).match(/[\d.]+/));
  const per = Number(String(unitQty).match(/[\d.]+/));

  if (Number.isNaN(need) || Number.isNaN(per) || per === 0) return "-";
  return Math.ceil(need / per);
};

// 一個商品單位是多少標準單位（100 g, 250 ml, 20 pcs）
const standardPerItem = (unitQty, stdUnit) => {
  const qty = Number(String(unitQty).match(/[\d.]+/));
  if (Number.isNaN(qty)) return "-";
  return `${qty} ${stdUnit}`;
};

// 單位價格（每標準單位成本）
const pricePerUnit = (price, unitQty) => {
  const p = Number(price);
  const u = Number(String(unitQty).match(/[\d.]+/));

  if (Number.isNaN(p) || Number.isNaN(u) || u === 0) return "-";
  return (p / u).toFixed(4);
};

const totalStandardUnits = (neededQty, unitQty, stdUnit) => {
  const items = itemsNeeded(neededQty, unitQty);
  const per = Number(String(unitQty).match(/[\d.]+/));
  if (Number.isNaN(items) || Number.isNaN(per)) return "-";
  return `${items * per} ${stdUnit}`;
};

const totalPriceForItem = (price, neededQty, unitQty) => {
  const perItem = Number(price);
  const items = itemsNeeded(neededQty, unitQty);

  if (Number.isNaN(perItem) || Number.isNaN(items)) return "-";

  return (perItem * items).toFixed(2); // 字串數字
};



// ===============================
// Component
// ===============================
export default function ShoppingListPage() {
  const today = new Date().toISOString().slice(0, 10);

  const [items, setItems] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [orderResult, setOrderResult] = useState(null);

  const [newItem, setNewItem] = useState({
    ingredient_id: "",
    quantity_to_buy: 1,
    needed_by: today,
  });

  const [recData, setRecData] = useState(null);
  const [loadingRec, setLoadingRec] = useState(false);

  const [fridges, setFridges] = useState([]);
  const [selectedFridge, setSelectedFridge] = useState("");

  // Load shopping list
  const loadShoppingList = async () => {
    const data = await getShoppingList();
    setItems(data || []);
  };

  // Load fridges
  const loadFridges = async () => {
    const list = await getUserFridges();
    setFridges(list || []);
    if (list?.length > 0) setSelectedFridge(list[0].fridge_id);
  };

  useEffect(() => {
    loadShoppingList();
    loadFridges();
  }, []);

  // Add item
  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newItem.ingredient_id) return alert("Please enter ingredient ID");

    await addShoppingItem({
      ingredient_id: Number(newItem.ingredient_id),
      quantity_to_buy: Number(newItem.quantity_to_buy),
      needed_by: newItem.needed_by,
    });

    setNewItem({
      ingredient_id: "",
      quantity_to_buy: 1,
      needed_by: today,
    });

    loadShoppingList();
  };

  // Remove
  const handleRemove = async (ingredient_id) => {
    await removeShoppingItem(ingredient_id);
    loadShoppingList();
  };

  // Show recommendations
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
      alert("Failed to fetch recommendations");
    }
    setLoadingRec(false);
  };

  // Which product is recommended?
  const recommendedProduct = (() => {
    if (!recData?.products?.length) return null;

    // backend provided
    const backend = recData.products.find((p) => p.is_recommended);
    if (backend) return backend;

    // else choose cheapest in-time
    const inTimeProducts = recData.products.filter((p) =>
      isInTime(p.expected_arrival, recData.needed_by)
    );

    if (!inTimeProducts.length) return null;

    return inTimeProducts.reduce((best, p) =>
      Number(p.current_price) < Number(best.current_price) ? p : best
    );
  })();

  // Add to order
  const addOrderItem = (p) => {
    // Calculate quantity needed for this product
    const quantity = itemsNeeded(recData.quantity_needed, p.unit_quantity);
    setOrderItems((prev) => [...prev, { ...p, quantity: Number(quantity) }]);
  };

  // Submit order (manual selection)
  const submitOrder = async () => {
    if (!selectedFridge) return alert("Select a fridge first.");
    if (!orderItems.length) return alert("No items selected.");

    try {
      // Group items by partner_id (split orders)
      const itemsByPartner = {};
      orderItems.forEach((p) => {
        if (!itemsByPartner[p.partner_id]) {
          itemsByPartner[p.partner_id] = [];
        }
        itemsByPartner[p.partner_id].push({
          external_sku: p.external_sku,
          partner_id: p.partner_id,
          quantity: p.quantity || 1,
        });
      });

      const partnerIds = Object.keys(itemsByPartner);
      const createdOrders = [];

      // Create one order per partner
      for (const partnerId of partnerIds) {
        const payload = {
          fridge_id: selectedFridge,
          items: itemsByPartner[partnerId],
        };

        const result = await createOrder(payload);
        createdOrders.push(result);
      }

      // Show success message
      if (createdOrders.length === 1) {
        setOrderResult(createdOrders[0]);
      } else {
        alert(
          `✅ Created ${createdOrders.length} orders (split by partner)\n\n` +
          createdOrders
            .map(
              (o, i) =>
                `Order ${i + 1}: ${o.partner_name} - $${formatPrice(o.total_price)}`
            )
            .join("\n")
        );
      }

      setOrderItems([]);
      setRecData(null);
    } catch (error) {
      console.error("Order creation failed:", error);
      alert("Failed to create order: " + (error.response?.data?.detail || error.message));
    }
  };

  // Checkout all from shopping list (auto-split by partner)
  const handleCheckoutAll = async () => {
    if (items.length === 0) {
      return alert("Shopping list is empty");
    }

    if (!selectedFridge) {
      return alert("Please select a fridge first");
    }

    if (!confirm(`Create orders for all ${items.length} items in your shopping list?\n\nOrders will be automatically split by partner and optimized for cheapest prices.`)) {
      return;
    }

    try {
      const result = await createOrdersFromShoppingList(selectedFridge);

      alert(
        `✅ Success!\n\n` +
        `Orders created: ${result.orders_created}\n` +
        `Partners: ${result.total_partners}\n` +
        `Total amount: $${result.total_amount}\n\n` +
        result.message +
        `\n\n💡 Meal plan statuses have been updated!`
      );

      // Reload shopping list (should be empty now)
      await loadShoppingList();
      setRecData(null);
      setOrderItems([]);
    } catch (error) {
      console.error("Checkout failed:", error);
      alert("Failed to checkout: " + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="page">
      <h1>Shopping List</h1>

      {/* ================= Select Fridge ================= */}
      <div className="panel">
        <h2>Select Fridge</h2>
        <select
          value={selectedFridge}
          onChange={(e) => setSelectedFridge(e.target.value)}
          style={{ width: "100%", padding: "8px" }}
        >
          {fridges.map((f) => (
            <option key={f.fridge_id} value={f.fridge_id}>
              {f.fridge_name}
            </option>
          ))}
        </select>
        <p className="text-muted" style={{ marginTop: 8 }}>
          Orders will be associated with this fridge
        </p>
      </div>

      {/* ================= Add Item ================= */}
      <div className="panel">
        <h2>Add Item</h2>
        <form onSubmit={handleAdd} className="inline-form">
          <label>
            Ingredient ID
            <input
              type="number"
              value={newItem.ingredient_id}
              onChange={(e) =>
                setNewItem({ ...newItem, ingredient_id: e.target.value })
              }
            />
          </label>

          <label>
            Quantity to buy
            <input
              type="number"
              value={newItem.quantity_to_buy}
              onChange={(e) =>
                setNewItem({ ...newItem, quantity_to_buy: e.target.value })
              }
            />
          </label>

          <label>
            Needed by
            <input
              type="date"
              value={newItem.needed_by}
              onChange={(e) =>
                setNewItem({ ...newItem, needed_by: e.target.value })
              }
            />
          </label>

          <button className="btn-primary">Add</button>
        </form>
      </div>

      {/* ================= Shopping List ================= */}
      <div className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Current Shopping List</h2>
          {items.length > 0 && (
            <button className="btn-primary" onClick={handleCheckoutAll}>
              🛒 Checkout All ({items.length} items)
            </button>
          )}
        </div>

        {items.length === 0 ? (
          <p>No items.</p>
        ) : (
          <>
            <p className="text-muted" style={{ marginTop: 8, marginBottom: 12 }}>
              Click "Checkout All" to automatically create orders split by partner with cheapest prices.
            </p>
            <ul className="list">
              {items.map((it) => (
                <li key={it.ingredient_id} className="list-item">
                  <div>
                    <strong>{it.ingredient_name}</strong> — {it.quantity_to_buy}{" "}
                    {it.standard_unit}
                    <div className="text-muted">
                      Needed by: {formatDate(it.needed_by)}
                    </div>
                  </div>

                  <div>
                    <button
                      className="btn-secondary"
                      onClick={() => showRecommendations(it)}
                    >
                      Recommend
                    </button>
                    <button
                      className="btn-link danger"
                      onClick={() => handleRemove(it.ingredient_id)}
                    >
                      remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      {/* ================= Recommendations ================= */}
      {loadingRec && (
        <div className="panel">
          <p>Loading...</p>
        </div>
      )}

      {recData && !loadingRec && (
        <div className="panel">
          <h2>Recommended Products</h2>

          <p className="text-muted">
            Ingredient: <strong>{recData.ingredient_name}</strong>
            <br />
            Needed:{" "}
            <strong>
              {recData.quantity_needed}{" "}
              {recData.products[0]?.standard_unit || ""}
            </strong>
            <br />
            Needed by: {formatDate(recData.needed_by)}
          </p>

          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Partner</th>
                <th>Total Price</th>

                <th>Items needed</th>
                <th>Standard per item</th>
                <th>Price per item</th>
                {/* <th>Unit</th> */}

                <th>Shipping</th>
                <th>Arrival</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {recData.products.map((p) => {
                const inTime = isInTime(p.expected_arrival, recData.needed_by);
                const recommended =
                  recommendedProduct &&
                  p.external_sku === recommendedProduct.external_sku &&
                  p.partner_id === recommendedProduct.partner_id;

                return (
                  <tr key={`${p.external_sku}-${p.partner_id}`}>
                    <td>
                      <strong>{p.product_name}</strong>
                      {recommended && (
                        <span style={{ marginLeft: 6, color: "#f5c518" }}>⭐</span>
                      )}
                    </td>
                    <td>{p.partner_name}</td>
                    <td>
                      ${totalPriceForItem(
                        p.current_price,
                        recData.quantity_needed,
                        p.unit_quantity
                      )}
                    </td>


                    <td>
                      {itemsNeeded(
                        recData.quantity_needed,
                        p.unit_quantity
                      )}
                    </td>

                    <td>
                      {standardPerItem(p.unit_quantity, p.standard_unit)}
                    </td>

                    <td>{formatPrice(p.current_price)}</td>

                    {/* <td>{p.standard_unit}</td> */}

                    <td>{p.avg_shipping_days}</td>
                    <td>{formatDate(p.expected_arrival)}</td>

                    <td>
                      {inTime ? (
                        <span className="badge badge-success">In time</span>
                      ) : (
                        <span className="badge badge-warning">Late</span>
                      )}
                    </td>

                    <td>
                      <button
                        className="btn-primary"
                        onClick={() => addOrderItem(p)}
                      >
                        Add
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ================= Order Preview ================= */}
      {orderItems.length > 0 && (
        <div className="panel">
          <h2>Order Preview</h2>

          <ul className="list">
            {orderItems.map((p, i) => {
              // 從 recData 抓出需要量 & 標準單位
              const neededQty = recData?.quantity_needed ?? null;
              const stdUnit = p.standard_unit;

              return (
                <li key={i}>
                  <strong>{p.product_name}</strong> — {p.partner_name} (<span style={{ fontWeight: 500 }}>${formatPrice(p.current_price)} per item</span>)
                  <div className="text-muted">
                    Total Price: $
                    {totalPriceForItem(
                      p.current_price,
                      neededQty,
                      p.unit_quantity
                    )}
                  </div>
                  <div className="text-muted">
                    Items needed:{" "}
                    {itemsNeeded(neededQty, p.unit_quantity)} item(s)
                  </div>
                  <div className="text-muted">
                    Total:{" "}
                    {totalStandardUnits(
                      neededQty,
                      p.unit_quantity,
                      stdUnit
                    )}
                  </div>
                </li>
              );
            })}
          </ul>


          <button className="btn-primary" onClick={submitOrder}>
            Submit Order
          </button>
        </div>
      )}

      {/* ================= Order Result ================= */}
      {orderResult && (
        <div className="panel">
          <h2>Order Created!</h2>
          <p>ID: {orderResult.order_id}</p>
          <p>Total: ${formatPrice(orderResult.total_price)}</p>
          <p>Status: {orderResult.order_status}</p>

          <button className="btn-link" onClick={() => setOrderResult(null)}>
            Clear
          </button>
        </div>
      )}
    </div>
  );
}
