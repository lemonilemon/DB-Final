// src/api/partners.js
import api from "./client";

// 取得所有夥伴
export const getPartners = async () => {
  const res = await api.get("/partners");
  return res.data;
};

// 新增夥伴
export const createPartner = async (data) => {
  // data: { partner_name, contract_date, avg_shipping_days, credit_score }
  const res = await api.post("/partners", data);
  return res.data;
};
