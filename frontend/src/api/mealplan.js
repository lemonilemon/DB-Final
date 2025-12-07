import api from "./client";

export const getMealPlans = async () => {
  const res = await api.get("/meal-plans/");
  return res.data;
};

export const createMealPlan = async (data) => {
  const res = await api.post("/meal-plans/", data);
  return res.data;
};

export const deleteMealPlan = async (id) => {
  const res = await api.delete(`/meal-plans/${id}`);
  return res.data;
};
