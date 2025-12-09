// src/api/products.js
import api from "./client";

// 取得外部商品（可用 ingredient_id / partner_id 篩選）
export const getProducts = async (params = {}) => {
  const res = await api.get("/products", { params });
  return res.data;
};

// 新增外部商品（符合後端 schema）
export const createProduct = async (data) => {
  // data 需包含：
  // external_sku, partner_id, ingredient_id,
  // product_name, current_price, selling_unit, unit_quantity
  const res = await api.post("/products", {
    external_sku: data.external_sku,
    partner_id: data.partner_id,
    ingredient_id: data.ingredient_id,
    product_name: data.product_name,
    current_price: data.current_price,
    selling_unit: data.selling_unit,
    unit_quantity: data.unit_quantity,   // ⭐ 後端新增需求
  });
  return res.data;
};
