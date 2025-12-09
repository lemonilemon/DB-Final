import api from "./client";

export const getInventory = async (fridgeId) => {
  // correct backend route
  const res = await api.get(`/fridges/${fridgeId}/items`);
  return res.data;
};

export const addItem = async (fridgeId, payload) => {
  const res = await api.post(`/fridges/${fridgeId}/items`, payload);
  return res.data;
};

export const deleteItem = async (fridgeId, itemId) => {
  const res = await api.delete(`/fridges/${fridgeId}/items/${itemId}`);
  return res.data;
};


// ⭐ 新增：更新冰箱內的食材（PUT）
export const updateItem = async (fridgeId, itemId, payload) => {
  const res = await api.put(`/fridges/${fridgeId}/items/${itemId}`, payload);
  return res.data;
};