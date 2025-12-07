// src/api/fridge.js
import api from "./client";

// 取得所有冰箱列表  GET /api/fridges
export const getFridges = async () => {
  const res = await api.get("/fridges");
  return res.data;
};

// 別名：讓前端可以呼叫 getUserFridges()
export const getUserFridges = getFridges;


// 建立新冰箱  POST /api/fridges
export const createFridge = async (data) => {
  const res = await api.post("/fridges", {
    fridge_name: data.fridge_name,
    description: data.description || "",
  });
  return res.data;
};

// 取得冰箱詳細資料（含 members） GET /api/fridges/{fridge_id}
export const getFridgeDetail = async (fridgeId) => {
  const res = await api.get(`/fridges/${fridgeId}`);
  return res.data;
};

// 新增一位成員（後端會驗證角色） POST /api/fridges/{fridge_id}/members
export const addMemberToFridge = async (fridgeId, userName) => {
  const payload = {
    role: "Member",        // 預設 Member
    user_name: userName,   // 正確欄位名稱
  };

  const res = await api.post(`/fridges/${fridgeId}/members`, payload);
  return res.data;
};
// export const addMemberToFridge = async (fridgeId, username) => {
//   const res = await api.post(`/fridges/${fridgeId}/members`, { username });
//   return res.data;
// };

// 刪除冰箱 DELETE /api/fridges/{fridge_id}
export const deleteFridge = async (fridgeId) => {
  const res = await api.delete(`/fridges/${fridgeId}`);
  return res.data;
};

// 刪除成員 DELETE /api/fridges/{fridge_id}/members/{user_id}
export const removeMemberFromFridge = async (fridgeId, userId) => {
  const res = await api.delete(`/fridges/${fridgeId}/members/${userId}`);
  return res.data;
};

// 更新冰箱資訊 PUT /api/fridges/{fridge_id}
export const updateFridge = async (fridgeId, data) => {
  const res = await api.put(`/fridges/${fridgeId}`, data);
  return res.data;
};

// 消耗食材 FIFO
export const consumeIngredient = async (fridgeId, data) => {
  const res = await api.post(`/fridges/${fridgeId}/consume`, data);
  return res.data;
};
