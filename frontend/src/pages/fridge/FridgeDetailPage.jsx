// src/pages/fridge/FridgeDetailPage.jsx

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import {
  getFridgeDetail,
  addMemberToFridge,
  deleteFridge,
  removeMemberFromFridge,
  updateFridge,
  consumeIngredient,
} from "../../api/fridge";

import {
  getInventory,
  addItem,
  deleteItem,
  updateItem,
} from "../../api/inventory";

import {
  getMealPlans,
  createMealPlan,
  deleteMealPlan,
} from "../../api/mealplan";

import { searchRecipes } from "../../api/recipes";

import { addShoppingItem, checkAvailability } from "../../api/shopping";

// ⭐ Ingredient Search
import { searchIngredients, getIngredients } from "../../api/ingredients";

export default function FridgeDetailPage() {
  const { fridgeId } = useParams();
  const navigate = useNavigate();

  // ---------------------------
  // State
  // ---------------------------
  const [fridge, setFridge] = useState(null);
  const [loading, setLoading] = useState(true);

  const [inventory, setInventory] = useState([]);

  // Members
  const [newMember, setNewMember] = useState("");

  // Ingredient search for "Add item"
  const [ingredientQuery, setIngredientQuery] = useState("");
  const [ingredientResults, setIngredientResults] = useState([]);
  const [selectedIngredient, setSelectedIngredient] = useState(null);

  const [quantity, setQuantity] = useState("");
  const [expiryDate, setExpiryDate] = useState("");

  // Ingredient search for "Consume"
  const [consumeQuery, setConsumeQuery] = useState("");
  const [consumeResults, setConsumeResults] = useState([]);
  const [consumeIngredientSelected, setConsumeIngredientSelected] = useState(null);
  const [consumeQty, setConsumeQty] = useState("");
  const [consumeResult, setConsumeResult] = useState(null);

  // Edit item
  const [editingItem, setEditingItem] = useState(null);
  const [editQty, setEditQty] = useState("");
  const [editExpiry, setEditExpiry] = useState("");

  // Edit fridge info
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  // Meal Plan
  const [mealPlans, setMealPlans] = useState([]);
  const [recipeQuery, setRecipeQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [mealDate, setMealDate] = useState("");

  // ---------------------------
  // Load Data
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

  const loadMealPlans = async () => {
    try {
      const mp = await getMealPlans(fridgeId);
      setMealPlans(mp);
    } catch (err) {
      console.error("Failed to load meal plans:", err);
    }
  };

  useEffect(() => {
    const init = async () => {
      await loadFridge();
      await loadInventory();
      await loadMealPlans();
      setLoading(false);
    };
    init();
  }, [fridgeId]);

  if (loading) return <div className="page">Loading...</div>;
  if (!fridge) return <div className="page">Fridge not found.</div>;

  // -------------------------------------------------------
  // Member Actions
  // -------------------------------------------------------

  const handleAddMember = async () => {
    if (!newMember.trim()) return alert("請輸入 username");

    try {
      await addMemberToFridge(fridgeId, newMember.trim());
      setNewMember("");
      await loadFridge();
    } catch {
      alert("Failed to add member");
    }
  };

  const handleDeleteMember = async (userId) => {
    if (!window.confirm("Remove this member?")) return;

    try {
      await removeMemberFromFridge(fridgeId, userId);
      await loadFridge();
    } catch {
      alert("Failed to remove member");
    }
  };

  // -------------------------------------------------------
  // Fridge Info Update
  // -------------------------------------------------------

  const handleUpdateFridge = async () => {
    const payload = {};
    if (editName.trim()) payload.fridge_name = editName.trim();
    if (editDescription.trim()) payload.description = editDescription.trim();

    if (!Object.keys(payload).length) {
      alert("No changes");
      return;
    }

    try {
      await updateFridge(fridgeId, payload);
      await loadFridge();
      setIsEditing(false);
    } catch {
      alert("Update failed");
    }
  };

  // -------------------------------------------------------
  // Ingredient Search (Add item)
  // -------------------------------------------------------

  const handleSearchIngredient = async (e) => {
    e.preventDefault();

    if (!ingredientQuery.trim()) return;

    try {
      const results = await searchIngredients(ingredientQuery);
      setIngredientResults(results);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddItem = async () => {
    if (!selectedIngredient) return alert("請先選擇食材");
    if (!quantity || !expiryDate) return alert("請輸入數量與到期日");

    try {
      await addItem(fridgeId, {
        ingredient_id: selectedIngredient.ingredient_id,
        quantity: Number(quantity),
        expiry_date: expiryDate,
      });

      // reset
      setSelectedIngredient(null);
      setIngredientQuery("");
      setQuantity("");
      setExpiryDate("");
      setIngredientResults([]);

      await loadInventory();
    } catch {
      alert("Failed to add item");
    }
  };

  // -------------------------------------------------------
  // Ingredient Search (Consume)
  // -------------------------------------------------------

  const handleSearchConsumeIngredient = async (e) => {
    e.preventDefault();

    if (!consumeQuery.trim()) return;

    try {
      const results = await searchIngredients(consumeQuery);
      setConsumeResults(results);
    } catch (err) {
      console.error(err);
    }
  };

  const handleConsume = async () => {
    if (!consumeIngredientSelected) return alert("請先選擇食材");
    if (!consumeQty) return alert("請輸入消耗數量");

    try {
      const res = await consumeIngredient(fridgeId, {
        ingredient_id: consumeIngredientSelected.ingredient_id,
        quantity: Number(consumeQty),
      });

      setConsumeResult(res);
      await loadInventory();
    } catch {
      alert("Failed to consume ingredient");
    }
  };

  // -------------------------------------------------------
  // Inventory Edit
  // -------------------------------------------------------

  const handleUpdateItem = async () => {
    if (!editingItem) return;

    const payload = {};
    if (editQty) payload.quantity = Number(editQty);
    if (editExpiry) payload.expiry_date = editExpiry;

    if (!Object.keys(payload).length) {
      alert("No changes");
      return;
    }

    try {
      await updateItem(fridgeId, editingItem.fridge_item_id, payload);
      alert("Item updated!");
      setEditingItem(null);
      setEditQty("");
      setEditExpiry("");
      await loadInventory();
    } catch {
      alert("Update failed");
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm("Delete this item?")) return;

    try {
      await deleteItem(fridgeId, itemId);
      await loadInventory();
    } catch {
      alert("Failed to delete item");
    }
  };

  // -------------------------------------------------------
  // Recipe Search (Meal plan)
  // -------------------------------------------------------

  const handleSearchRecipes = async (e) => {
    e.preventDefault();
    if (!recipeQuery.trim()) return;

    const results = await searchRecipes(recipeQuery);
    setSearchResults(results);
  };

  // -------------------------------------------------------
  // Create Meal Plan
  // -------------------------------------------------------

  const handleCreateMealPlan = async (e) => {
    e.preventDefault();

    if (!mealDate || !selectedRecipe)
      return alert("請選擇日期與食譜");

    const recipeId = selectedRecipe.recipe_id;

    let availability;
    try {
      availability = await checkAvailability(recipeId, fridgeId, mealDate);
    } catch {
      return alert("無法檢查庫存，請稍後再試");
    }

    if (availability.all_available) {
      await createMealPlan({
        recipe_id: recipeId,
        fridge_id: fridgeId,
        planned_date: mealDate,
      });

      setMealDate("");
      setSelectedRecipe(null);
      setSearchResults([]);

      await loadMealPlans();
      alert("Meal plan created!");
      return;
    }

    // 缺料提醒
    const missing = availability.missing_ingredients;

    let msg = "以下食材不足：\n\n";
    for (const m of missing) {
      msg += `• ${m.ingredient_name} (${m.shortage} ${m.standard_unit})\n`;
    }
    msg += "\n是否要加入購物清單？";

    if (window.confirm(msg)) {
      try {
        for (const m of missing) {
          await addShoppingItem({
            ingredient_id: m.ingredient_id,
            needed_by: mealDate,
            quantity_to_buy: m.shortage,
          });
        }
        alert("已加入購物清單！");
      } catch {
        alert("加入購物清單失敗");
      }
    }

    if (!window.confirm("仍然要建立 meal plan？")) return;

    await createMealPlan({
      recipe_id: recipeId,
      fridge_id: fridgeId,
      planned_date: mealDate,
    });

    setMealDate("");
    setSelectedRecipe(null);
    setSearchResults([]);
    await loadMealPlans();

    alert("Meal plan created（含缺料提醒）!");
  };

  const handleDeleteMealPlan = async (planId) => {
    await deleteMealPlan(planId);
    await loadMealPlans();
  };

  // -------------------------------------------------------
  // Render
  // -------------------------------------------------------

  return (
    <div className="page">

      {/* =======================================================
          Fridge Info
      ======================================================== */}
      <h1>{fridge.fridge_name}</h1>
      <p>{fridge.description || "No description."}</p>

      {fridge.your_role === "Owner" && (
        <>
          {isEditing ? (
            <div>
              <input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="Fridge name"
              />
              <input
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="Description"
              />
              <button onClick={handleUpdateFridge}>Save</button>
              <button onClick={() => setIsEditing(false)}>Cancel</button>
            </div>
          ) : (
            <button
              onClick={() => {
                setEditName(fridge.fridge_name);
                setEditDescription(fridge.description || "");
                setIsEditing(true);
              }}
            >
              Edit Fridge Info
            </button>
          )}

          <button
            className="btn-danger"
            style={{ marginTop: 10 }}
            onClick={async () => {
              if (!window.confirm("Delete this fridge?")) return;
              await deleteFridge(fridgeId);
              navigate("/fridges");
            }}
          >
            Delete Fridge
          </button>
        </>
      )}

      {/* =======================================================
          Members
      ======================================================== */}
      <h2 style={{ marginTop: 40 }}>Members</h2>

      <ul>
        {fridge.members.map((m) => (
          <li key={m.user_id}>
            {m.user_name} — <strong>{m.role}</strong>
            {m.role !== "Owner" && fridge.your_role === "Owner" && (
              <button
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
          <input
            placeholder="username"
            value={newMember}
            onChange={(e) => setNewMember(e.target.value)}
          />
          <button onClick={handleAddMember}>Add Member</button>
        </>
      )}

      {/* =======================================================
          Inventory
      ======================================================== */}
      <h2 style={{ marginTop: 40 }}>Inventory</h2>

      {inventory.length === 0 ? (
        <p>No items</p>
      ) : (
        <ul>
          {inventory.map((item) => (
            <li key={item.fridge_item_id}>
              <strong>{item.ingredient_name}</strong> — {item.quantity}
              {item.standard_unit}, expires {item.expiry_date}

              <button
                onClick={() => handleDeleteItem(item.fridge_item_id)}
                style={{ marginLeft: 10 }}
              >
                Delete
              </button>

              <button
                onClick={() => {
                  setEditingItem(item);
                  setEditQty(item.quantity);
                  setEditExpiry(item.expiry_date);
                }}
                style={{ marginLeft: 10 }}
              >
                Edit
              </button>
            </li>
          ))}
        </ul>
      )}

      {editingItem && (
        <div style={{ marginTop: 10 }}>
          <h3>Edit Item</h3>
          <input
            type="number"
            value={editQty}
            onChange={(e) => setEditQty(e.target.value)}
          />
          <input
            type="date"
            value={editExpiry}
            onChange={(e) => setEditExpiry(e.target.value)}
          />
          <button onClick={handleUpdateItem}>Save</button>
          <button onClick={() => setEditingItem(null)}>Cancel</button>
        </div>
      )}

      {/* =======================================================
          Add Item (Search ingredient)
      ======================================================== */}
      <h2 style={{ marginTop: 40 }}>Add Item</h2>

      <form onSubmit={handleSearchIngredient} style={{ marginBottom: 10 }}>
        <input
          type="text"
          placeholder="Search ingredients..."
          value={ingredientQuery}
          onChange={(e) => setIngredientQuery(e.target.value)}
        />
        <button>Search</button>
      </form>

      <div className="card-grid" style={{ marginTop: 20 }}>
        {ingredientResults.map((ing) => (
          <div key={ing.ingredient_id} className="card">
            <h4>{ing.name}</h4>
            <p>Unit: {ing.standard_unit}</p>

            <button onClick={() => setSelectedIngredient(ing)}>Select</button>

            {/* 小 close 按鍵 */}
            <button
              className="btn-link"
              style={{ color: "#888", marginTop: 6, fontSize: "0.85em" }}
              onClick={() => setIngredientResults([])}
            >
              close
            </button>
          </div>
        ))}
      </div>




      {selectedIngredient && (
        <div style={{ marginTop: 15 }}>
          <h4>Selected Ingredient: {selectedIngredient.name}</h4>

          <input
            type="number"
            placeholder="quantity"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />

          <input
            type="date"
            value={expiryDate}
            onChange={(e) => setExpiryDate(e.target.value)}
          />

          <button onClick={handleAddItem}>Add to Fridge</button>
          <button onClick={() => setSelectedIngredient(null)}>Cancel</button>
        </div>
      )}

      {/* =======================================================
          Consume Ingredient (Search ingredient)
      ======================================================== */}
      <h2 style={{ marginTop: 40 }}>Consume Ingredient</h2>

      <form onSubmit={handleSearchConsumeIngredient} style={{ marginBottom: 10 }}>
        <input
          type="text"
          placeholder="Search ingredients..."
          value={consumeQuery}
          onChange={(e) => setConsumeQuery(e.target.value)}
        />
        <button>Search</button>
      </form>

      <div className="card-grid" style={{ marginTop: 20 }}>
        {consumeResults.map((ing) => (
          <div key={ing.ingredient_id} className="card">
            <h4>{ing.name}</h4>
            <p>Unit: {ing.standard_unit}</p>

            <button onClick={() => setConsumeIngredientSelected(ing)}>
              Select
            </button>

            {/* 小 close 按鍵 */}
            <button
              className="btn-link"
              style={{ color: "#888", marginTop: 6, fontSize: "0.85em" }}
              onClick={() => setConsumeResults([])}
            >
              close
            </button>
          </div>
        ))}
      </div>



      {consumeIngredientSelected && (
        <div style={{ marginTop: 15 }}>
          <h4>Selected Ingredient: {consumeIngredientSelected.name}</h4>

          <input
            type="number"
            placeholder="quantity"
            value={consumeQty}
            onChange={(e) => setConsumeQty(e.target.value)}
          />

          <button onClick={handleConsume}>Consume</button>
          <button onClick={() => setConsumeIngredientSelected(null)}>
            Cancel
          </button>
        </div>
      )}

      {consumeResult && (
        <div style={{ border: "1px solid #aaa", marginTop: 20, padding: 10 }}>
          <h3>Consume Result</h3>
          <p>Ingredient: {consumeResult.ingredient_name}</p>
          <p>Requested: {consumeResult.requested_quantity}</p>
          <p>Consumed: {consumeResult.consumed_quantity}</p>
          <p>Remaining: {consumeResult.remaining_quantity}</p>
          <p>Batches Used: {consumeResult.items_consumed}</p>

          <button onClick={() => setConsumeResult(null)}>Close</button>
        </div>
      )}

      {/* =======================================================
          Meal Plan Section
      ======================================================== */}
      <h2 style={{ marginTop: 40 }}>Meal Plans</h2>

      <form onSubmit={handleCreateMealPlan}>
        <input
          type="date"
          value={mealDate}
          onChange={(e) => setMealDate(e.target.value)}
        />

        {selectedRecipe ? (
          <div>
            <strong>Selected Recipe: </strong>
            {selectedRecipe.recipe_name}
            <button
              type="button"
              className="btn-link danger"
              onClick={() => setSelectedRecipe(null)}
            >
              remove
            </button>
          </div>
        ) : (
          <p>No recipe selected</p>
        )}

        <button className="btn-primary">Add Meal Plan</button>
      </form>

      <hr />

      <h3>Search Recipes</h3>
      <form onSubmit={handleSearchRecipes}>
        <input
          type="text"
          placeholder="Search recipes..."
          value={recipeQuery}
          onChange={(e) => setRecipeQuery(e.target.value)}
        />
        <button>Search</button>
      </form>

      <div className="card-grid" style={{ marginTop: 20 }}>
        {searchResults.map((r) => (
          <div key={r.recipe_id} className="card">
            <h3>{r.recipe_name}</h3>
            <p>{r.description}</p>
            <button onClick={() => setSelectedRecipe(r)}>Select</button>
          </div>
        ))}
      </div>

      <hr />

      <table className="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Recipe</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {mealPlans.map((p) => (
            <tr key={p.plan_id}>
              <td>{p.planned_date}</td>
              <td>{p.recipe_name}</td>
              <td>{p.status}</td>
              <td>
                <button
                  className="btn-link danger"
                  onClick={() => handleDeleteMealPlan(p.plan_id)}
                >
                  remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

    </div>
  );
}



// // src/pages/fridge/FridgeDetailPage.jsx

// import React, { useEffect, useState } from "react";
// import { useParams, useNavigate } from "react-router-dom";

// import {
//   getFridgeDetail,
//   addMemberToFridge,
//   deleteFridge,
//   removeMemberFromFridge,
//   updateFridge,
//   consumeIngredient
// } from "../../api/fridge";

// import {
//   getInventory,
//   addItem,
//   deleteItem,
//   updateItem
// } from "../../api/inventory";

// // ⭐ Meal Plan API（依照你的 API 修正）
// import {
//   getMealPlans,
//   createMealPlan,
//   deleteMealPlan,
// } from "../../api/mealplan";

// // ⭐ Recipe Search API
// import { searchRecipes } from "../../api/recipes";

// import { 
//   addShoppingItem,
//   checkAvailability 
// } from "../../api/shopping";



// export default function FridgeDetailPage() {
//   const { fridgeId } = useParams();
//   const navigate = useNavigate();

//   // ---------------------------
//   // State
//   // ---------------------------
//   const [fridge, setFridge] = useState(null);
//   const [loading, setLoading] = useState(true);

//   const [inventory, setInventory] = useState([]);

//   // Members
//   const [newMember, setNewMember] = useState("");

//   // Add item
//   const [ingredientId, setIngredientId] = useState("");
//   const [quantity, setQuantity] = useState("");
//   const [expiryDate, setExpiryDate] = useState("");

//   // Edit fridge
//   const [editName, setEditName] = useState("");
//   const [editDescription, setEditDescription] = useState("");
//   const [isEditing, setIsEditing] = useState(false);

//   // Consume ingredient
//   const [consumeId, setConsumeId] = useState("");
//   const [consumeQty, setConsumeQty] = useState("");
//   const [consumeResult, setConsumeResult] = useState(null);

//   // Edit item
//   const [editingItem, setEditingItem] = useState(null);
//   const [editQty, setEditQty] = useState("");
//   const [editExpiry, setEditExpiry] = useState("");

//   // ⭐ Meal Plans
//   const [mealPlans, setMealPlans] = useState([]);
//   const [recipeQuery, setRecipeQuery] = useState("");
//   const [searchResults, setSearchResults] = useState([]);
//   const [selectedRecipe, setSelectedRecipe] = useState(null);
//   const [mealDate, setMealDate] = useState("");

//   // ---------------------------
//   // Load
//   // ---------------------------
//   const loadFridge = async () => {
//     try {
//       const data = await getFridgeDetail(fridgeId);
//       setFridge(data);
//     } catch (err) {
//       console.error("Failed to load fridge:", err);
//       setFridge(null);
//     }
//   };

//   const loadInventory = async () => {
//     try {
//       const items = await getInventory(fridgeId);
//       setInventory(items);
//     } catch (err) {
//       console.error("Failed to load inventory:", err);
//     }
//   };

//   const loadMealPlans = async () => {
//     try {
//       const data = await getMealPlans(fridgeId);
//       setMealPlans(data);
//     } catch (err) {
//       console.error("Failed to load meal plans:", err);
//     }
//   };

//   useEffect(() => {
//     const init = async () => {
//       await loadFridge();
//       await loadInventory();
//       await loadMealPlans();
//       setLoading(false);
//     };
//     init();
//   }, [fridgeId]);

//   if (loading) return <div className="page">Loading...</div>;
//   if (!fridge) return <div className="page">Fridge not found.</div>;

//   // ---------------------------
//   // Member Actions
//   // ---------------------------
//   const handleAddMember = async () => {
//     if (!newMember.trim()) return alert("Please enter username");

//     try {
//       await addMemberToFridge(fridgeId, newMember.trim());
//       setNewMember("");
//       await loadFridge();
//     } catch (e) {
//       console.error(e);
//       alert("Failed to add member.");
//     }
//   };

//   const handleDeleteMember = async (userId) => {
//     if (!window.confirm("Remove this member?")) return;

//     try {
//       await removeMemberFromFridge(fridgeId, userId);
//       await loadFridge();
//     } catch (e) {
//       console.error(e);
//       alert("Failed to remove member.");
//     }
//   };

//   // ---------------------------
//   // Fridge Info Update
//   // ---------------------------
//   const handleUpdateFridge = async () => {
//     try {
//       const payload = {};
//       if (editName.trim()) payload.fridge_name = editName.trim();
//       if (editDescription.trim()) payload.description = editDescription.trim();

//       if (Object.keys(payload).length === 0) {
//         alert("No changes.");
//         return;
//       }

//       await updateFridge(fridgeId, payload);
//       await loadFridge();
//       setIsEditing(false);
//     } catch (e) {
//       console.error(e);
//       alert("Update failed.");
//     }
//   };

//   // ---------------------------
//   // Inventory Actions
//   // ---------------------------
//   const handleAddItem = async () => {
//     if (!ingredientId || !quantity || !expiryDate) {
//       alert("Missing fields");
//       return;
//     }

//     try {
//       await addItem(fridgeId, {
//         ingredient_id: Number(ingredientId),
//         quantity: Number(quantity),
//         expiry_date: expiryDate,
//       });

//       setIngredientId("");
//       setQuantity("");
//       setExpiryDate("");

//       await loadInventory();
//     } catch (e) {
//       alert("Failed to add item");
//       console.error(e);
//     }
//   };

//   const handleDeleteItem = async (itemId) => {
//     if (!window.confirm("Delete this item?")) return;

//     try {
//       await deleteItem(fridgeId, itemId);
//       await loadInventory();
//     } catch (e) {
//       alert("Failed to delete item");
//     }
//   };

//   const handleUpdateItem = async () => {
//     if (!editingItem) return;

//     const payload = {};
//     if (editQty) payload.quantity = Number(editQty);
//     if (editExpiry) payload.expiry_date = editExpiry;

//     if (Object.keys(payload).length === 0) {
//       alert("No changes.");
//       return;
//     }

//     try {
//       await updateItem(fridgeId, editingItem.fridge_item_id, payload);

//       alert("Item updated!");
//       setEditingItem(null);
//       setEditQty("");
//       setEditExpiry("");

//       await loadInventory();
//     } catch (e) {
//       console.error(e);
//       alert("Update failed.");
//     }
//   };

//   // ---------------------------
//   // Consume Ingredient + Availability Check After Consume
//   // ---------------------------
//   // const handleConsume = async () => {
//   //   if (!consumeId || !consumeQty) {
//   //     alert("Missing ingredient_id or quantity");
//   //     return;
//   //   }

//   //   let consumeResponse;

//   //   try {
//   //     // ⭐ Step 1：先消耗食材（FIFO）
//   //     consumeResponse = await consumeIngredient(fridgeId, {
//   //       ingredient_id: Number(consumeId),
//   //       quantity: Number(consumeQty),
//   //     });

//   //     setConsumeResult(consumeResponse);
//   //     await loadInventory();
//   //   } catch (e) {
//   //     console.error(e);
//   //     return alert("Failed to consume ingredient.");
//   //   }

//   //   // ⭐ Step 2：消耗後立即檢查該食材是否不足
//   //   let availability;
//   //   try {
//   //     availability = await checkAvailability(
//   //       consumeId,                     // recipe_id（這裡用 ingredient_id 當作單項檢查）
//   //       fridgeId,                      // 冰箱
//   //       new Date().toISOString().slice(0, 10)  // needed_by = 今天
//   //     );
//   //   } catch (err) {
//   //     console.error("Availability check failed:", err);
//   //     return; // 不阻斷消耗流程
//   //   }

//   //   // ⭐ Step 3：如果全數足夠，不需要加入購物清單
//   //   if (availability.all_available) return;

//   //   // ⭐ Step 4：缺少材料列表
//   //   const missing = availability.missing_ingredients;

//   //   let msg = "消耗後，以下食材庫存不足：\n\n";
//   //   for (const m of missing) {
//   //     msg += `• ${m.ingredient_name}（缺少 ${m.shortage} ${m.standard_unit}）\n`;
//   //   }
//   //   msg += "\n是否要將缺少的食材自動加入購物清單？";

//   //   const addToShoppingList = window.confirm(msg);

//   //   if (!addToShoppingList) return;

//   //   // ⭐ Step 5：逐一加入購物清單
//   //   try {
//   //     for (const m of missing) {
//   //       await addShoppingItem({
//   //         ingredient_id: m.ingredient_id,
//   //         needed_by: availability.needed_by || new Date().toISOString().slice(0, 10),
//   //         quantity_to_buy: m.shortage,
//   //       });
//   //     }
//   //     alert("已成功將缺少的食材加入購物清單！");
//   //   } catch (err) {
//   //     console.error("Failed to add shopping items:", err);
//   //     alert("加入購物清單時發生錯誤。");
//   //   }
//   // };

//   const handleConsume = async () => {
//     if (!consumeId || !consumeQty) {
//       alert("Missing ingredient_id or quantity");
//       return;
//     }

//     try {
//       const consumeResponse = await consumeIngredient(fridgeId, {
//         ingredient_id: Number(consumeId),
//         quantity: Number(consumeQty),
//       });

//       setConsumeResult(consumeResponse);
//       await loadInventory();
//     } catch (e) {
//       console.error(e);
//       alert("Failed to consume ingredient.");
//     }
//   };


//   // ---------------------------
//   // ⭐ Meal Plan Actions
//   // ---------------------------
//   const handleSearchRecipes = async (e) => {
//     e.preventDefault();
//     if (!recipeQuery.trim()) return;

//     const results = await searchRecipes(recipeQuery);
//     setSearchResults(results);
//   };

//   const handleCreateMealPlan = async (e) => {
//     e.preventDefault();

//     if (!mealDate || !selectedRecipe)
//       return alert("請選擇日期與食譜");

//     // ⭐ Step 1：呼叫 availability check API
//     const recipeId = selectedRecipe.recipe_id;
//     let availability;

//     try {
//       availability = await checkAvailability(
//         recipeId,
//         fridgeId,
//         mealDate
//       );
//     } catch (err) {
//       console.error("Availability check failed:", err);
//       return alert("無法檢查庫存，請稍後再試");
//     }

//     console.log("Availability result:", availability);

//     // ⭐ Step 2：如果全部足夠 → 直接建立 Meal Plan
//     if (availability.all_available) {
//       await createMealPlan({
//         recipe_id: recipeId,
//         fridge_id: fridgeId,
//         planned_date: mealDate,
//       });

//       setMealDate("");
//       setSelectedRecipe(null);
//       setRecipeQuery("");
//       setSearchResults([]);

//       await loadMealPlans();

//       return alert("Meal plan created!");
//     }

//     // ⭐ Step 3：若不足 → 顯示缺少清單並詢問是否自動加入購物清單
//     const missing = availability.missing_ingredients;

//     let msg = "以下食材不足：\n\n";
//     for (const m of missing) {
//       msg += `• ${m.ingredient_name} (${m.shortage} ${m.standard_unit})\n`;
//     }
//     msg += "\n要自動加入購物清單嗎？";

//     const addToCart = window.confirm(msg);

//     if (addToCart) {
//       try {
//         for (const m of missing) {
//           await addShoppingItem({
//             ingredient_id: m.ingredient_id,
//             needed_by: mealDate,
//             quantity_to_buy: m.shortage,
//           });
//         }
//         alert("已將所有缺少的食材加入購物清單！");
//       } catch (err) {
//         console.error("Add shopping failed:", err);
//         alert("加入購物清單時失敗");
//       }
//     }

//     // ⭐ Step 4：詢問是否仍建立 Meal Plan
//     const stillCreate = window.confirm("是否仍然要建立這份 Meal Plan？");

//     if (!stillCreate) return;

//     await createMealPlan({
//       recipe_id: recipeId,
//       fridge_id: fridgeId,
//       planned_date: mealDate,
//     });

//     setMealDate("");
//     setSelectedRecipe(null);
//     setRecipeQuery("");
//     setSearchResults([]);

//     await loadMealPlans();

//     alert("Meal plan created（含缺料提醒）!");
//   };
//   // const handleCreateMealPlan = async (e) => {
//   //   e.preventDefault();

//   //   if (!mealDate || !selectedRecipe)
//   //     return alert("請選擇日期與食譜");

//   //   try {
//   //     const result = await createMealPlan({
//   //       recipe_id: selectedRecipe.recipe_id,
//   //       fridge_id: fridgeId,
//   //       planned_date: mealDate,
//   //     });

//   //     console.log("📦 Meal Plan API 回傳：", result);  // ⭐ 新增：印出回傳內容
//   //     alert("Meal plan created!");

//   //     // reset UI
//   //     setMealDate("");
//   //     setSelectedRecipe(null);
//   //     setRecipeQuery("");
//   //     setSearchResults([]);

//   //     await loadMealPlans();
//   //   } catch (err) {
//   //     console.error("❌ Create meal plan failed:", err);
//   //     alert("無法建立 meal plan，請稍後再試");
//   //   }
//   // };




//   const handleDeleteMealPlan = async (planId) => {
//     await deleteMealPlan(planId);
//     await loadMealPlans();
//   };

//   // ---------------------------
//   // Render
//   // ---------------------------
//   return (
//     <div className="page">

//       {/* ----------------- Fridge Info ----------------- */}
//       <h1>{fridge.fridge_name}</h1>
//       <p>{fridge.description || "No description."}</p>

//       {fridge.your_role === "Owner" && (
//         <>
//           {isEditing ? (
//             <div style={{ marginBottom: 20 }}>
//               <h3>Edit Fridge</h3>

//               <input
//                 placeholder="New fridge name"
//                 value={editName}
//                 onChange={(e) => setEditName(e.target.value)}
//                 style={{ marginRight: 10 }}
//               />

//               <input
//                 placeholder="New description"
//                 value={editDescription}
//                 onChange={(e) => setEditDescription(e.target.value)}
//                 style={{ marginRight: 10 }}
//               />

//               <button onClick={handleUpdateFridge} style={{ marginRight: 10 }}>
//                 Save
//               </button>

//               <button onClick={() => setIsEditing(false)}>Cancel</button>
//             </div>
//           ) : (
//             <button
//               onClick={() => {
//                 setEditName(fridge.fridge_name);
//                 setEditDescription(fridge.description || "");
//                 setIsEditing(true);
//               }}
//               style={{ marginBottom: 20 }}
//             >
//               Edit Fridge Info
//             </button>
//           )}
//         </>
//       )}

//       {fridge.your_role === "Owner" && (
//         <button
//           className="btn-danger"
//           onClick={async () => {
//             if (!window.confirm("Delete this fridge?")) return;
//             await deleteFridge(fridgeId);
//             navigate("/fridges");
//           }}
//           style={{ marginBottom: 20 }}
//         >
//           Delete This Fridge
//         </button>
//       )}

//       {/* ----------------- Members ----------------- */}
//       <h2>Members</h2>
//       <ul>
//         {fridge.members.map((m) => (
//           <li key={m.user_id}>
//             {m.user_name} — <strong>{m.role}</strong>
//             {m.role !== "Owner" &&
//               fridge.your_role === "Owner" && (
//                 <button
//                   className="btn-link danger"
//                   style={{ marginLeft: 10 }}
//                   onClick={() => handleDeleteMember(m.user_id)}
//                 >
//                   remove
//                 </button>
//               )}
//           </li>
//         ))}
//       </ul>

//       {fridge.your_role === "Owner" && (
//         <>
//           <h3>Add Member</h3>
//           <input
//             value={newMember}
//             onChange={(e) => setNewMember(e.target.value)}
//             placeholder="username"
//           />
//           <button onClick={handleAddMember}>Add</button>
//         </>
//       )}

//       {/* ----------------- Inventory ----------------- */}
//       <h2 style={{ marginTop: 40 }}>Fridge Items</h2>

//       {inventory.length === 0 ? (
//         <p>No items in fridge.</p>
//       ) : (
//         <ul>
//           {inventory.map((item) => (
//             <li key={item.fridge_item_id}>
//               <strong>{item.ingredient_name}</strong> — {item.quantity}
//               {item.standard_unit}, expires: {item.expiry_date} (
//               {item.days_until_expiry} days left)
//               <button
//                 style={{ marginLeft: 10 }}
//                 onClick={() => handleDeleteItem(item.fridge_item_id)}
//               >
//                 Delete
//               </button>

//               {fridge.your_role === "Owner" && (
//                 <button
//                   style={{ marginLeft: 10 }}
//                   onClick={() => {
//                     setEditingItem(item);
//                     setEditQty(item.quantity);
//                     setEditExpiry(item.expiry_date);
//                   }}
//                 >
//                   Edit
//                 </button>
//               )}
//             </li>
//           ))}
//         </ul>
//       )}

//       {/* Edit Item */}
//       {editingItem && (
//         <div style={{ marginTop: 30, padding: 15, border: "1px solid gray" }}>
//           <h3>Edit Item</h3>

//           <input
//             type="number"
//             value={editQty}
//             onChange={(e) => setEditQty(e.target.value)}
//             placeholder="New quantity"
//             style={{ marginRight: 10 }}
//           />

//           <input
//             type="date"
//             value={editExpiry}
//             onChange={(e) => setEditExpiry(e.target.value)}
//           />

//           <button onClick={handleUpdateItem} style={{ marginLeft: 10 }}>
//             Save
//           </button>

//           <button
//             style={{ marginLeft: 10 }}
//             onClick={() => setEditingItem(null)}
//           >
//             Cancel
//           </button>
//         </div>
//       )}

//       {/* ----------------- Add Item to Fridge ----------------- */}
//       <h2 style={{ marginTop: 40 }}>Add Item to Fridge</h2>

//       <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
//         <input
//           type="number"
//           placeholder="ingredient_id"
//           value={ingredientId}
//           onChange={(e) => setIngredientId(e.target.value)}
//         />
//         <input
//           type="number"
//           placeholder="quantity"
//           value={quantity}
//           onChange={(e) => setQuantity(e.target.value)}
//         />
//         <input
//           type="date"
//           placeholder="expiry_date"
//           value={expiryDate}
//           onChange={(e) => setExpiryDate(e.target.value)}
//         />
//         <button className="btn-primary" onClick={handleAddItem}>
//           Add Item
//         </button>
//       </div>


//       {/* ----------------- Consume Ingredient ----------------- */}
//       <h2 style={{ marginTop: 40 }}>Consume Ingredient (FIFO)</h2>

//       <div style={{ display: "flex", gap: 10 }}>
//         <input
//           placeholder="ingredient_id"
//           value={consumeId}
//           onChange={(e) => setConsumeId(e.target.value)}
//         />
//         <input
//           placeholder="quantity"
//           value={consumeQty}
//           onChange={(e) => setConsumeQty(e.target.value)}
//         />
//         <button onClick={handleConsume}>Consume</button>
//       </div>

//       {consumeResult && (
//         <div style={{ marginTop: 20, padding: 10, border: "1px solid #ccc", position: "relative" }}>
//           <h4>Consumption Result</h4>

//           <p>Ingredient: {consumeResult.ingredient_name}</p>
//           <p>Requested: {consumeResult.requested_quantity}</p>
//           <p>Consumed: {consumeResult.consumed_quantity}</p>
//           <p>Remaining: {consumeResult.remaining_quantity}</p>
//           <p>Batches Used: {consumeResult.items_consumed}</p>
//           <p>{consumeResult.message}</p>

//           {/* Close Button */}
//           <button
//             style={{
//               marginTop: 10,
//               backgroundColor: "#aaa",
//               color: "white",
//               border: "none",
//               padding: "5px 10px",
//               borderRadius: 4,
//               cursor: "pointer",
//             }}
//             onClick={() => setConsumeResult(null)}
//           >
//             Close
//           </button>
//         </div>
//       )}


//       {/* ------------------------------------------------------- */}
//       {/*                    ⭐ MEAL PLAN SECTION                  */}
//       {/* ------------------------------------------------------- */}

//       <h2 style={{ marginTop: 40 }}>Meal Plans</h2>

//       {/* Create Meal Plan */}
//       <form onSubmit={handleCreateMealPlan} className="meal-form">
//         <input
//           type="date"
//           value={mealDate}
//           onChange={(e) => setMealDate(e.target.value)}
//         />

//         {selectedRecipe ? (
//           <div>
//             <strong>Selected Recipe:</strong> {selectedRecipe.recipe_name}
//             <button
//               type="button"
//               className="btn-link danger"
//               onClick={() => setSelectedRecipe(null)}
//             >
//               remove
//             </button>
//           </div>
//         ) : (
//           <p className="muted">No recipe selected</p>
//         )}

//         <button className="btn-primary">Add Meal Plan</button>
//       </form>

//       <hr />

//       {/* Recipe Search */}
//       <h3>Search Recipes</h3>
//       <form onSubmit={handleSearchRecipes} className="inline-form">
//         <input
//           type="text"
//           placeholder="Search recipes..."
//           value={recipeQuery}
//           onChange={(e) => setRecipeQuery(e.target.value)}
//         />
//         <button className="btn-primary">Search</button>
//       </form>

//       {/* Search Results */}
//       <div className="card-grid" style={{ marginTop: 20 }}>
//         {searchResults.map((r) => (
//           <div className="card" key={r.recipe_id}>
//             <h3>{r.recipe_name}</h3>
//             <p className="muted">{r.description}</p>
//             <button
//               className="btn-primary"
//               onClick={() => setSelectedRecipe(r)}
//             >
//               Select
//             </button>
//           </div>
//         ))}
//       </div>

//       <hr />

//       {/* Meal Plan List */}
//       <table className="table">
//         <thead>
//           <tr>
//             <th>Date</th>
//             <th>Recipe</th>
//             <th>Status</th>
//             <th></th>
//           </tr>
//         </thead>
//         <tbody>
//           {mealPlans.map((p) => (
//             <tr key={p.plan_id}>
//               <td>{p.planned_date}</td>
//               <td>{p.recipe_name}</td>
//               <td>{p.status}</td>
//               <td>
//                 <button
//                   className="btn-link danger"
//                   onClick={() => handleDeleteMealPlan(p.plan_id)}
//                 >
//                   remove
//                 </button>
//               </td>
//             </tr>
//           ))}
//         </tbody>
//       </table>

//       {/* ----------------- END MEAL PLAN SECTION ----------------- */}

//     </div>
//   );
// }
