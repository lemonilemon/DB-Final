// src/api/mealplan.js
import api from "./client";

// 取得某冰箱的 meal plans：GET /api/meal-plans?fridge_id=xxx
export const getMealPlans = async (fridgeId) => {
  const res = await api.get(`/meal-plans`, {
    params: { fridge_id: fridgeId }
  });
  return res.data;
};

// 新增 meal plan：POST /api/meal-plans
export const createMealPlan = async (data) => {
  const res = await api.post(`/meal-plans`, data);
  return res.data;
};

// 刪除 meal plan：DELETE /api/meal-plans/{plan_id}
export const deleteMealPlan = async (planId) => {
  const res = await api.delete(`/meal-plans/${planId}`);
  return res.data;
};
