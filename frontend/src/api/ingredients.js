// src/api/ingredients.js
import api from "./client";

// 取得全部 ingredients
export async function getIngredients() {
  const res = await api.get("/ingredients");
  return res.data;
}

// 新增 ingredient
export async function createIngredient(data) {
  const res = await api.post("/ingredients", data);
  return res.data;
}

// 搜尋食材
export const searchIngredients = async (query) => {
  const res = await api.get(`/ingredients`, {
    params: { search: query },
  });
  return res.data;
};

