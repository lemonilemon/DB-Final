// src/pages/admin/AdminPartners.jsx
import React, { useEffect, useState } from "react";
import { getPartners, createPartner } from "../../api/partners";
import { getProducts, createProduct } from "../../api/products";
import { getIngredients } from "../../api/ingredients";

export default function AdminPartners() {
  const [partners, setPartners] = useState([]);
  const [products, setProducts] = useState([]);
  const [ingredients, setIngredients] = useState([]);

  // 新 partner form
  const [partnerForm, setPartnerForm] = useState({
    partner_name: "",
    contract_date: "",
    avg_shipping_days: 3,
    credit_score: 80,
  });

  // 新 product form
  const [productForm, setProductForm] = useState({
    external_sku: "",
    partner_id: "",
    ingredient_id: "",
    product_name: "",
    current_price: "",
    selling_unit: "",
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAll = async () => {
    try {
      setLoading(true);
      setError("");
      const [pList, prodList, ingList] = await Promise.all([
        getPartners(),
        getProducts(),
        getIngredients(),
      ]);
      setPartners(pList);
      setProducts(prodList);
      setIngredients(ingList);
    } catch (err) {
      console.error("load partners/products failed:", err);
      setError("無法載入合作夥伴 / 商品資料");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handlePartnerChange = (e) => {
    const { name, value } = e.target;
    setPartnerForm((f) => ({ ...f, [name]: value }));
  };

  const handleProductChange = (e) => {
    const { name, value } = e.target;
    setProductForm((f) => ({ ...f, [name]: value }));
  };

  const handleCreatePartner = async (e) => {
    e.preventDefault();
    if (!partnerForm.partner_name.trim()) return;

    try {
      await createPartner({
        partner_name: partnerForm.partner_name,
        contract_date: partnerForm.contract_date,
        avg_shipping_days: Number(partnerForm.avg_shipping_days),
        credit_score: Number(partnerForm.credit_score),
      });
      setPartnerForm({
        partner_name: "",
        contract_date: "",
        avg_shipping_days: 3,
        credit_score: 80,
      });
      await loadAll();
    } catch (err) {
      console.error("create partner failed:", err);
      setError("新增合作夥伴失敗");
    }
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();

    try {
      await createProduct({
        external_sku: productForm.external_sku,
        partner_id: Number(productForm.partner_id),
        ingredient_id: Number(productForm.ingredient_id),
        product_name: productForm.product_name,
        current_price: Number(productForm.current_price),
        selling_unit: productForm.selling_unit,
      });
      setProductForm({
        external_sku: "",
        partner_id: "",
        ingredient_id: "",
        product_name: "",
        current_price: "",
        selling_unit: "",
      });
      await loadAll();
    } catch (err) {
      console.error("create product failed:", err);
      setError("新增外部商品失敗");
    }
  };

  return (
    <section>
      <h2>合作夥伴 / 供應商品管理</h2>
      <p className="muted">
        管理合作商（Partner）與外部商品（External Product），例如設定信用評分、上架商品與售價。
      </p>

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          {/* 新增 Partner */}
          <div className="card" style={{ marginBottom: 24 }}>
            <h3>新增合作夥伴</h3>
            <form onSubmit={handleCreatePartner} className="inline-form">
              <input
                name="partner_name"
                placeholder="Partner name"
                value={partnerForm.partner_name}
                onChange={handlePartnerChange}
              />
              <input
                type="date"
                name="contract_date"
                value={partnerForm.contract_date}
                onChange={handlePartnerChange}
              />
              <input
                type="number"
                min="1"
                name="avg_shipping_days"
                value={partnerForm.avg_shipping_days}
                onChange={handlePartnerChange}
                placeholder="Avg shipping days"
              />
              <input
                type="number"
                min="0"
                max="100"
                name="credit_score"
                value={partnerForm.credit_score}
                onChange={handlePartnerChange}
                placeholder="Credit score"
              />
              <button type="submit">新增合作夥伴</button>
            </form>
          </div>

          {/* Partner 清單 */}
          <h3>合作夥伴列表</h3>
          {partners.length === 0 ? (
            <p>目前沒有任何合作夥伴。</p>
          ) : (
            <table className="table" style={{ marginBottom: 32 }}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Contract Date</th>
                  <th>Avg Shipping Days</th>
                  <th>Credit Score</th>
                </tr>
              </thead>
              <tbody>
                {partners.map((p) => (
                  <tr key={p.partner_id}>
                    <td>{p.partner_id}</td>
                    <td>{p.partner_name}</td>
                    <td>{p.contract_date}</td>
                    <td>{p.avg_shipping_days}</td>
                    <td>{p.credit_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* 新增外部商品 */}
          <div className="card" style={{ marginBottom: 24 }}>
            <h3>新增外部商品</h3>
            <form onSubmit={handleCreateProduct} className="inline-form">
              <input
                name="external_sku"
                placeholder="External SKU"
                value={productForm.external_sku}
                onChange={handleProductChange}
              />
              <select
                name="partner_id"
                value={productForm.partner_id}
                onChange={handleProductChange}
              >
                <option value="">選擇合作夥伴…</option>
                {partners.map((p) => (
                  <option key={p.partner_id} value={p.partner_id}>
                    {p.partner_name}
                  </option>
                ))}
              </select>

              <select
                name="ingredient_id"
                value={productForm.ingredient_id}
                onChange={handleProductChange}
              >
                <option value="">選擇對應食材…</option>
                {ingredients.map((ing) => (
                  <option key={ing.ingredient_id} value={ing.ingredient_id}>
                    {ing.name}
                  </option>
                ))}
              </select>

              <input
                name="product_name"
                placeholder="Product name"
                value={productForm.product_name}
                onChange={handleProductChange}
              />
              <input
                type="number"
                min="0"
                step="0.01"
                name="current_price"
                placeholder="Price"
                value={productForm.current_price}
                onChange={handleProductChange}
              />
              <input
                name="selling_unit"
                placeholder="Selling unit (e.g., 1L Bottle)"
                value={productForm.selling_unit}
                onChange={handleProductChange}
              />
              <button type="submit">新增商品</button>
            </form>
          </div>

          {/* 外部商品清單 */}
          <h3>外部商品列表</h3>
          {products.length === 0 ? (
            <p>目前沒有任何外部商品。</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Partner</th>
                  <th>Ingredient</th>
                  <th>Product Name</th>
                  <th>Price</th>
                  <th>Unit</th>
                </tr>
              </thead>
              <tbody>
                {products.map((prod) => (
                  <tr key={prod.external_sku}>
                    <td>{prod.external_sku}</td>
                    <td>{prod.partner_name}</td>
                    <td>{prod.ingredient_name}</td>
                    <td>{prod.product_name}</td>
                    <td>{prod.current_price}</td>
                    <td>{prod.selling_unit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}
