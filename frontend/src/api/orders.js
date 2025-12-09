import api from "./client";

export const getOrders = async () => {
  const res = await api.get("/orders/");
  return res.data;
};

// 取消訂單
export const cancelOrder = async (orderId) => {
  const res = await api.put(`/orders/${orderId}/cancel`);
  return res.data;
};

// 確認訂單送達
export const confirmDelivery = async (orderId) => {
  const res = await api.put(`/orders/${orderId}/confirm-delivery`);
  return res.data;
};
