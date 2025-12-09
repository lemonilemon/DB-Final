// src/api/shopping.js
import api from "./client";

// 🛍 GET /api/shopping-list
export const getShoppingList = async () => {
  const res = await api.get("/shopping-list");
  return res.data;
};

// ➕ POST /api/shopping-list
export const addShoppingItem = async (data) => {
  const payload = {
    ingredient_id: data.ingredient_id,
    quantity_to_buy: data.quantity_to_buy,
    needed_by: data.needed_by ?? new Date().toISOString().slice(0, 10) // 若前端沒給就使用今天
  };

  const res = await api.post("/shopping-list", payload);
  return res.data;
};

// 🗑 DELETE /api/shopping-list/{ingredient_id}
export const removeShoppingItem = async (ingredient_id) => {
  const res = await api.delete(`/shopping-list/${ingredient_id}`);
  return res.data;
};

// -------------------------------------------------------
// 🔍 NEW: Availability Check (/api/availability/check)
// -------------------------------------------------------
export const checkAvailability = async (recipeId, fridgeId, neededBy) => {
  const res = await api.get("/availability/check", {
    params: {
      recipe_id: recipeId,
      fridge_id: fridgeId,
      needed_by: neededBy,
    },
  });
  return res.data;
};

// -------------------------------------------------------
// ⭐ NEW: Product Recommendations
// -------------------------------------------------------
export const getRecommendations = async (ingredientId, qty, neededBy) => {
  const res = await api.get("/products/recommendations", {
    params: {
      ingredient_id: ingredientId,
      quantity_needed: qty,
      needed_by: neededBy,
    },
  });
  return res.data;
};

// -------------------------------------------------------
// 🛒 NEW: 建立訂單
// -------------------------------------------------------
export const createOrder = async (payload) => {
  console.log("Creating order. Payload:", payload);
  console.log("POST URL:", api.defaults.baseURL + "/orders");

  const res = await api.post("/orders", payload);
  return res.data;
};
