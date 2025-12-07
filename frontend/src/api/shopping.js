import api from "./client";

// 🛍 GET /api/shopping-list
export const getShoppingList = async () => {
  try {
    const res = await api.get("/shopping-list");
    return res.data;
  } catch (err) {
    console.error("❌ Failed to load shopping list", err);
    throw err;
  }
};

// ➕ POST /api/shopping-list
// data 應該包含 ingredient_id、quantity(optional)
export const addShoppingItem = async (data) => {
  try {
    const res = await api.post("/shopping-list", data);
    return res.data;
  } catch (err) {
    console.error("❌ Failed to add shopping list item", err);
    throw err;
  }
};

// 🗑 DELETE /api/shopping-list/{ingredient_id}
export const removeShoppingItem = async (ingredient_id) => {
  try {
    const res = await api.delete(`/shopping-list/${ingredient_id}`);
    return res.data;
  } catch (err) {
    console.error("❌ Failed to remove shopping list item", err);
    throw err;
  }
};
