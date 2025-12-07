import api from "./client";

// partners
export async function listPartners() {
  const res = await api.get("/api/partners");
  return res.data;
}

export async function createPartner(payload) {
  const res = await api.post("/api/partners", payload);
  return res.data;
}

// products
export async function listProducts(params = {}) {
  const res = await api.get("/api/products", { params });
  return res.data;
}

export async function createProduct(payload) {
  const res = await api.post("/api/products", payload);
  return res.data;
}

// shopping list
export async function getShoppingList() {
  const res = await api.get("/api/shopping-list");
  return res.data;
}

export async function addToShoppingList(payload) {
  const res = await api.post("/api/shopping-list", payload);
  return res.data;
}

export async function removeFromShoppingList(ingredientId) {
  const res = await api.delete(`/api/shopping-list/${ingredientId}`);
  return res.data;
}

// orders
export async function createOrdersFromList() {
  const res = await api.post("/api/orders/create-from-list");
  return res.data;
}

export async function listOrders() {
  const res = await api.get("/api/orders");
  return res.data;
}

export async function updateOrderStatus(orderId, payload) {
  const res = await api.put(`/api/orders/${orderId}/status`, payload);
  return res.data;
}
