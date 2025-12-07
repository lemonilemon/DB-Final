// src/api/products.js
import api from "./client";

// 取得外部商品（可用 ingredient_id / partner_id 篩選）
export const getProducts = async (params = {}) => {
  const res = await api.get("/products", { params });
  return res.data;
};

// 新增外部商品
export const createProduct = async (data) => {
  // data: {
  //   external_sku, partner_id, ingredient_id,
  //   product_name, current_price, selling_unit
  // }
  const res = await api.post("/products", data);
  return res.data;
};
