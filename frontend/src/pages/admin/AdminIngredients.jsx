// src/pages/admin/AdminIngredients.jsx
import React, { useEffect, useState } from "react";
import {
  getIngredients,
  createIngredient,
  // 如果你有做 update / delete，再解開下面
  // updateIngredient,
  // deleteIngredient,
} from "../../api/ingredients";

export default function AdminIngredients() {
  const [ingredients, setIngredients] = useState([]);
  const [name, setName] = useState("");
  const [unit, setUnit] = useState("g");
  const [shelfLife, setShelfLife] = useState(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getIngredients();
      setIngredients(data);
    } catch (err) {
      console.error("load ingredients failed:", err);
      setError("無法載入食材清單");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      await createIngredient({
        name,
        standard_unit: unit,
        shelf_life_days: Number(shelfLife),
      });
      setName("");
      setUnit("g");
      setShelfLife(7);
      await load();
    } catch (err) {
      console.error("create ingredient failed:", err);
      setError("新增食材失敗");
    }
  };

  // 如果後端有做 update / delete，可以再加編輯/刪除功能

  return (
    <section>
      <h2>食材管理（標準食材庫）</h2>
      <p className="muted">
        新增標準食材、設定單位與建議保鮮期（天）。
      </p>

      <form onSubmit={handleCreate} className="inline-form" style={{ marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Ingredient name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <select value={unit} onChange={(e) => setUnit(e.target.value)}>
          <option value="g">g</option>
          <option value="ml">ml</option>
          <option value="pcs">pcs</option>
        </select>
        <input
          type="number"
          min="1"
          value={shelfLife}
          onChange={(e) => setShelfLife(e.target.value)}
          placeholder="Shelf life (days)"
        />
        <button type="submit">新增食材</button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : ingredients.length === 0 ? (
        <p>目前沒有任何食材。</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名稱</th>
              <th>單位</th>
              <th>建議保鮮期 (天)</th>
            </tr>
          </thead>
          <tbody>
            {ingredients.map((ing) => (
              <tr key={ing.ingredient_id}>
                <td>{ing.ingredient_id}</td>
                <td>{ing.name}</td>
                <td>{ing.standard_unit}</td>
                <td>{ing.shelf_life_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
