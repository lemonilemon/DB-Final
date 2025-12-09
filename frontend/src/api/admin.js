// src/api/admin.js
import api from "./client";

// =======================
// Admin - Orders
// =======================

// GET /api/admin/orders
export const getAllOrders = async (params = {}) => {
  const res = await api.get("/admin/orders", { params });
  return res.data;
};

// PUT /api/admin/orders/{order_id}/status
export const updateOrderStatus = async (orderId, status) => {
  console.log("PUT /admin/orders", orderId, "status =", status);

  const res = await api.put(
    `/admin/orders/${orderId}/status`,
    { order_status: status },
    {
      headers: {
        "Content-Type": "application/json",   // 強制 JSON
      },
    }
  );

  return res.data;
};


// =======================
// Admin - Users
// =======================

// GET /api/admin/users
export const getAllUsers = async () => {
  const res = await api.get("/admin/users");
  return res.data;
};

// GET /api/admin/users/{user_id}
export const getUserDetail = async (userId) => {
  const res = await api.get(`/admin/users/${userId}`);
  return res.data;
};

// PUT /api/admin/users/{user_id}/status?new_status=Active/Disabled
export const updateUserStatus = async (userId, newStatus) => {
  const res = await api.put(`/admin/users/${userId}/status`, null, {
    params: { new_status: newStatus },
  });
  return res.data;
};

// POST /api/admin/users/{user_id}/roles/{role_name}
export const setUserRole = async (userId, roleName) => {
  const res = await api.post(`/admin/users/${userId}/roles/${roleName}`);
  return res.data;
};

// DELETE /api/admin/users/{user_id}/roles/{role_name}
export const revokeRole = async (userId, roleName) => {
  const res = await api.delete(`/admin/users/${userId}/roles/${roleName}`);
  return res.data;
};

// 分頁取得訂單
export const getOrders = async (page, pageSize) => {
  const res = await api.get("/admin/orders", {
    params: { page, page_size: pageSize }
  });
  return res.data;
};
