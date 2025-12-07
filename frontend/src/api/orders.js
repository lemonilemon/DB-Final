import api from "./client";

export const getOrders = async () => {
  const res = await api.get("/orders/");
  return res.data;
};

// 更新訂單狀態
export const updateOrderStatus = async (orderId, status) => {
  const res = await api.put(`/orders/${orderId}/status`, {
    order_status: status,   // 後端需要這個欄位名稱！
  });
  return res.data;
};

// 從購物清單建立分店家訂單
export const createOrdersFromList = async () => {
  const res = await api.post("/orders/create-from-list");
  return res.data;
};

