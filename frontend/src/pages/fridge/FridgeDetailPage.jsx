import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import { 
  getFridgeDetail, 
  addMemberToFridge,
  deleteFridge,
  removeMemberFromFridge,
  updateFridge,
  consumeIngredient
} from "../../api/fridge";

import {
  getInventory,
  addItem,
  deleteItem
} from "../../api/inventory";

export default function FridgeDetailPage() {
  const { fridgeId } = useParams();
  const navigate = useNavigate();

  const [fridge, setFridge] = useState(null);
  const [loading, setLoading] = useState(true);

  const [inventory, setInventory] = useState([]);

  // Add Member
  const [newMember, setNewMember] = useState("");

  // Add Item
  const [ingredientId, setIngredientId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [expiryDate, setExpiryDate] = useState("");

  // Edit Fridge
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  // Consume Ingredient
  const [consumeId, setConsumeId] = useState("");
  const [consumeQty, setConsumeQty] = useState("");
  const [consumeResult, setConsumeResult] = useState(null);


  // ---------------------------
  // Load fridge & inventory
  // ---------------------------
  const loadFridge = async () => {
    try {
      const data = await getFridgeDetail(fridgeId);
      setFridge(data);
    } catch (err) {
      console.error("Failed to load fridge:", err);
      setFridge(null);
    }
  };

  const loadInventory = async () => {
    try {
      const items = await getInventory(fridgeId);
      setInventory(items);
    } catch (err) {
      console.error("Failed to load inventory:", err);
    }
  };

  useEffect(() => {
    const init = async () => {
      await loadFridge();
      await loadInventory();
      setLoading(false);
    };
    init();
  }, [fridgeId]);


  if (loading) return <div className="page">Loading...</div>;
  if (!fridge) return <div className="page">Fridge not found.</div>;


  // ---------------------------
  // Add Member
  // ---------------------------
  const handleAddMember = async () => {
    if (!newMember.trim()) return alert("Please enter username");

    try {
      await addMemberToFridge(fridgeId, newMember.trim());
      setNewMember("");
      await loadFridge();
    } catch (e) {
      console.error(e);
      alert("Failed to add member (check permissions or username).");
    }
  };


  // ---------------------------
  // Delete Member
  // ---------------------------
  const handleDeleteMember = async (userId) => {
    if (!window.confirm("Remove this member?")) return;

    try {
      await removeMemberFromFridge(fridgeId, userId);
      await loadFridge();
    } catch (e) {
      console.error(e);
      alert("Failed to remove member.");
    }
  };


  // ---------------------------
  // Delete Fridge
  // ---------------------------
  const handleDeleteFridge = async () => {
    if (!window.confirm("Delete this fridge permanently?")) return;

    try {
      await deleteFridge(fridgeId);
      alert("Fridge deleted.");
      navigate("/fridges");
    } catch (e) {
      console.error(e);
      alert("Failed to delete fridge. Only Owners can delete.");
    }
  };


  // ---------------------------
  // Update Fridge Info (PUT)
  // ---------------------------
  const handleUpdateFridge = async () => {
    try {
      const payload = {};
      if (editName.trim()) payload.fridge_name = editName.trim();
      if (editDescription.trim()) payload.description = editDescription.trim();

      if (Object.keys(payload).length === 0) {
        alert("No changes to update.");
        return;
      }

      await updateFridge(fridgeId, payload);
      await loadFridge();
      setIsEditing(false);

    } catch (e) {
      console.error(e);
      alert("Failed to update fridge. Only Owners can update.");
    }
  };


  // ---------------------------
  // Add Item
  // ---------------------------
  const handleAddItem = async () => {
    if (!ingredientId || !quantity || !expiryDate) {
      alert("Missing fields");
      return;
    }

    try {
      await addItem(fridgeId, {
        ingredient_id: Number(ingredientId),
        quantity: Number(quantity),
        expiry_date: expiryDate,
      });

      setIngredientId("");
      setQuantity("");
      setExpiryDate("");

      await loadInventory();
    } catch (e) {
      alert("Failed to add item");
      console.error(e);
    }
  };


  // ---------------------------
  // Delete Item
  // ---------------------------
  const handleDeleteItem = async (itemId) => {
    if (!window.confirm("Delete this item?")) return;

    try {
      await deleteItem(fridgeId, itemId);
      await loadInventory();
    } catch (e) {
      alert("Failed to delete item");
    }
  };


  // ---------------------------
  // Consume Ingredient (FIFO)
  // ---------------------------
  const handleConsume = async () => {
    if (!consumeId || !consumeQty) {
      alert("Missing ingredient_id or quantity");
      return;
    }

    try {
      const result = await consumeIngredient(fridgeId, {
        ingredient_id: Number(consumeId),
        quantity: Number(consumeQty),
      });

      setConsumeResult(result);
      await loadInventory();

    } catch (e) {
      console.error(e);
      alert("Failed to consume ingredient.");
    }
  };


  return (
    <div className="page">

      {/* Fridge title */}
      <h1>{fridge.fridge_name}</h1>
      <p>{fridge.description || "No description."}</p>


      {/* -------- Edit Fridge -------- */}
      {fridge.your_role === "Owner" && (
        <>
          {isEditing ? (
            <div style={{ marginBottom: "20px" }}>
              <h3>Edit Fridge</h3>

              <input
                placeholder="New fridge name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                style={{ marginRight: "10px" }}
              />

              <input
                placeholder="New description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                style={{ marginRight: "10px" }}
              />

              <button onClick={handleUpdateFridge} style={{ marginRight: "10px" }}>
                Save
              </button>

              <button onClick={() => setIsEditing(false)}>Cancel</button>
            </div>
          ) : (
            <button
              onClick={() => {
                setEditName(fridge.fridge_name);
                setEditDescription(fridge.description || "");
                setIsEditing(true);
              }}
              style={{ marginBottom: "20px" }}
            >
              Edit Fridge Info
            </button>
          )}
        </>
      )}


      {/* Delete fridge */}
      {fridge.your_role === "Owner" && (
        <button 
          className="btn-danger"
          onClick={handleDeleteFridge}
          style={{ marginBottom: "20px" }}
        >
          Delete This Fridge
        </button>
      )}


      {/* -------- Members -------- */}
      <h2>Members</h2>
      <ul>
        {fridge.members.map((m) => (
          <li key={m.user_id}>
            {m.user_name} — <strong>{m.role}</strong>

            {m.role !== "Owner" && fridge.your_role === "Owner" && (
              <button 
                style={{ marginLeft: "10px" }}
                className="btn-link danger"
                onClick={() => handleDeleteMember(m.user_id)}
              >
                remove
              </button>
            )}
          </li>
        ))}
      </ul>

      {fridge.your_role === "Owner" && (
        <>
          <h3>Add Member</h3>
          <input
            value={newMember}
            onChange={(e) => setNewMember(e.target.value)}
            placeholder="username"
          />
          <button onClick={handleAddMember}>Add</button>
        </>
      )}


      {/* -------- Inventory -------- */}
      <h2 style={{ marginTop: "40px" }}>Fridge Items</h2>

      {inventory.length === 0 ? (
        <p>No items in fridge.</p>
      ) : (
        <ul>
          {inventory.map((item) => (
            <li key={item.fridge_item_id}>
              <strong>{item.ingredient_name}</strong> — {item.quantity}
              {item.standard_unit}
              {" , expires: "}
              {item.expiry_date}
              {" ("}{item.days_until_expiry}{" days left)"}

              <button 
                style={{ marginLeft: "10px" }} 
                onClick={() => handleDeleteItem(item.fridge_item_id)}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}


      {/* -------- Add Item -------- */}
      <h3>Add Item</h3>
      <div style={{ display: "flex", gap: "10px" }}>
        <input
          placeholder="ingredient_id"
          value={ingredientId}
          onChange={(e) => setIngredientId(e.target.value)}
        />
        <input
          placeholder="quantity"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
        />
        <input
          type="date"
          value={expiryDate}
          onChange={(e) => setExpiryDate(e.target.value)}
        />
        <button onClick={handleAddItem}>Add</button>
      </div>


      {/* -------- CONSUME INGREDIENT (FIFO) -------- */}
      <h2 style={{ marginTop: "40px" }}>Consume Ingredient (FIFO)</h2>

      <div style={{ display: "flex", gap: "10px" }}>
        <input
          placeholder="ingredient_id"
          value={consumeId}
          onChange={(e) => setConsumeId(e.target.value)}
        />
        <input
          placeholder="quantity"
          value={consumeQty}
          onChange={(e) => setConsumeQty(e.target.value)}
        />
        <button onClick={handleConsume}>Consume</button>
      </div>

      {consumeResult && (
        <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ccc" }}>
          <h4>Consumption Result</h4>
          <p><strong>Ingredient:</strong> {consumeResult.ingredient_name}</p>
          <p><strong>Requested:</strong> {consumeResult.requested_quantity}</p>
          <p><strong>Consumed:</strong> {consumeResult.consumed_quantity}</p>
          <p><strong>Remaining:</strong> {consumeResult.remaining_quantity}</p>
          <p><strong>Batches Used:</strong> {consumeResult.items_consumed}</p>
          <p><strong>Message:</strong> {consumeResult.message}</p>

          <button
            onClick={() => setConsumeResult(null)}
            style={{ marginTop: "10px" }}
          >
            Clear Report
          </button>
        </div>
      )}

    </div>
  );
}
