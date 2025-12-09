// src/pages/dashboard/UserIngredients.jsx

import React, { useEffect, useState } from "react";
import { getIngredients } from "../../api/ingredients";

export default function UserIngredients() {
  const [ingredients, setIngredients] = useState([]);
  const [search, setSearch] = useState("");

  // pagination
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadIngredients();
  }, [search]);

  const loadIngredients = async () => {
    const data = await getIngredients(search ? { search } : {});
    setIngredients(data);
    setCurrentPage(1);
  };

  // pagination calculations
  const totalPages = Math.ceil(ingredients.length / pageSize);
  const start = (currentPage - 1) * pageSize;
  const displayList = ingredients.slice(start, start + pageSize);

  return (
    <div className="page">
      <h1>🥦 Ingredients</h1>
      <p className="muted">Browse all available ingredients.</p>

      {/* 搜尋列 + 分頁設定 */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        {/* 搜尋（未啟用，不顯示） */}
        {/* <input
          type="text"
          placeholder="搜尋食材名稱…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            padding: "6px 10px",
            width: "250px",
            borderRadius: 6,
            border: "1px solid #ccc",
          }}
        /> */}

        <div style={{ marginLeft: "auto" }}>
          <label style={{ marginRight: 8 }}>每頁顯示：</label>
          <select
            value={pageSize}
            onChange={(e) => setPageSize(Number(e.target.value))}
            style={{
              padding: "4px 6px",
              borderRadius: 6,
              border: "1px solid #ccc",
            }}
          >
            <option value={5}>5 筆</option>
            <option value={10}>10 筆</option>
            <option value={20}>20 筆</option>
            <option value={50}>50 筆</option>
          </select>
        </div>
      </div>

      {/* 食材清單 */}
      {displayList.length === 0 ? (
        <p>沒有找到食材。</p>
      ) : (
        displayList.map((ing) => (
          <div
            className="card"
            key={ing.ingredient_id}
            style={{
              marginBottom: 16,
              padding: "16px 20px",
              borderLeft: "4px solid #4caf50",
            }}
          >
            <h2 style={{ margin: 0, marginBottom: 6 }}>{ing.name}</h2>

            <p style={{ margin: "4px 0", color: "#666" }}>
              <strong>ID：</strong> {ing.ingredient_id}
            </p>
            <p style={{ margin: "4px 0" }}>
              <strong>標準單位：</strong> {ing.standard_unit}
            </p>
            <p style={{ margin: "4px 0" }}>
              <strong>保存期限：</strong> {ing.shelf_life_days} 天
            </p>
          </div>
        ))
      )}

      {/* 分頁按鈕 */}
      {totalPages > 1 && (
        <div
          style={{
            marginTop: 20,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 12,
          }}
        >
          <button
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => p - 1)}
            style={{ padding: "6px 12px" }}
          >
            上一頁
          </button>

          <span>
            Page <strong>{currentPage}</strong> / {totalPages}
          </span>

          <button
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => p + 1)}
            style={{ padding: "6px 12px" }}
          >
            下一頁
          </button>
        </div>
      )}
    </div>
  );
}
