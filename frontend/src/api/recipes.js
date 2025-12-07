import api from "./client";

// 取得所有食譜
export const getAllRecipes = async () => {
  const res = await api.get(`/recipes`);
  return res.data;
};

// 搜尋食譜（後端需要 search 這個參數）
export const searchRecipes = async (query) => {
  const res = await api.get(`/recipes`, {
    params: { search: query },
  });
  return res.data;
};

// 取得食譜詳情
export const getRecipeDetail = async (id) => {
  const res = await api.get(`/recipes/${id}`);
  return res.data;
};

export const cookRecipe = async (recipeId, fridgeId) => {
  const res = await api.post(`/recipes/${recipeId}/cook`, {
    fridge_id: fridgeId,
  });
  return res.data;
};

// ⭐ 新增食譜（POST /api/recipes）
export const createRecipe = async (data) => {
  const res = await api.post("/recipes", data);
  return res.data;
};

// Get all reviews for a recipe
export const getRecipeReviews = async (recipeId) => {
  const res = await api.get(`/recipes/${recipeId}/reviews`);
  return res.data;
};

// Create or update review
export const submitRecipeReview = async (recipeId, payload) => {
  const res = await api.post(`/recipes/${recipeId}/reviews`, payload);
  return res.data;
};
