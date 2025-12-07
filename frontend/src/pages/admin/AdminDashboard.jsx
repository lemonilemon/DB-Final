// src/pages/admin/AdminDashboard.jsx
import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import AdminIngredients from "./AdminIngredients";
import AdminPartners from "./AdminPartners";
import AdminOrders from "./AdminOrders";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("ingredients");

  if (!user) return null; // 理論上會被 ProtectedRoute 擋掉

  return (
    <div className="page">
      <h1>Admin Dashboard</h1>
      <p className="muted">
        Signed in as <strong>{user.username}</strong> ({user.roles?.join(", ")})
      </p>

      {/* 簡單的 tab 切換 */}
      <div className="tabs" style={{ marginBottom: "20px" }}>
        <button
          className={tab === "ingredients" ? "tab active" : "tab"}
          onClick={() => setTab("ingredients")}
        >
          食材管理
        </button>
        <button
          className={tab === "orders" ? "tab active" : "tab"}
          onClick={() => setTab("orders")}
        >
          訂單管理
        </button>
        <button
          className={tab === "partners" ? "tab active" : "tab"}
          onClick={() => setTab("partners")}
        >
          合作夥伴 / 商品
        </button>
        <button
          className={tab === "more" ? "tab active" : "tab"}
          onClick={() => setTab("more")}
        >
          其他（使用者 / 食譜 / 統計）
        </button>
      </div>

      {tab === "ingredients" && <AdminIngredients />}
      {tab === "orders" && <AdminOrders />}
      {tab === "partners" && <AdminPartners />}

      {tab === "more" && (
        <div className="card">
          <h2>其他 Admin 功能（目前後端未提供 API）</h2>
          <ul>
            <li>查詢所有使用者活動紀錄（需要 /api/admin/users 之類的 API）</li>
            <li>管理所有使用者的食譜與評論（需要 /api/admin/recipes /comments）</li>
            <li>熱銷食材 / 熱門食譜統計（需要報表 / analytics API）</li>
          </ul>
          <p className="muted">
            這些功能前端可以先設計 UI，但沒有對應的後端 endpoint 前，沒辦法真的撈到資料。
          </p>
        </div>
      )}
    </div>
  );
}


// console.log("🏁 AdminDashboard MOUNTED");

// import React, { useEffect, useState } from "react";
// import { useAuth } from "../../context/AuthContext";
// import { useNavigate } from "react-router-dom";
// import { getIngredients, createIngredient } from "../../api/ingredients";

// export default function AdminDashboard() {
//   console.log("🏁 AdminDashboard MOUNTED here");

//   const { user } = useAuth();
//   const navigate = useNavigate();

//   console.log("🧪 AdminDashboard user =", user);


//   // ❗如果沒有 Admin 角色 → 自動踢回首頁或 login
//   useEffect(() => {
//     if (!user?.roles?.includes("Admin")) {
//       navigate("/");   // 或 navigate("/login")
//     }
//   }, [user, navigate]);

//   const [ingredients, setIngredients] = useState([]);
//   const [name, setName] = useState("");
//   const [unit, setUnit] = useState("g");
//   const [shelfLife, setShelfLife] = useState(7);
//   const [loading, setLoading] = useState(true);

//   const load = async () => {
//     setLoading(true);
//     try {
//       const data = await getIngredients();
//       setIngredients(data);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     load();
//   }, []);

//   const handleCreate = async (e) => {
//     e.preventDefault();

//     if (!name.trim()) return;

//     try {
//       await createIngredient({
//         name,
//         standard_unit: unit,
//         shelf_life_days: Number(shelfLife),
//       });

//       setName("");
//       setShelfLife(7);
//       setUnit("g");

//       await load();
//     } catch (err) {
//       console.error("Create ingredient failed:", err);
//     }
//   };

//   return (
//     <div className="page">
//       <h1>Admin Dashboard</h1>

//       <h2>Ingredients Management</h2>

//       <form onSubmit={handleCreate} style={{ marginBottom: "20px" }}>
//         <input
//           type="text"
//           placeholder="Ingredient name"
//           value={name}
//           onChange={(e) => setName(e.target.value)}
//           style={{ marginRight: "10px" }}
//         />

//         <select
//           value={unit}
//           onChange={(e) => setUnit(e.target.value)}
//           style={{ marginRight: "10px" }}
//         >
//           <option value="g">g</option>
//           <option value="ml">ml</option>
//           <option value="pcs">pcs</option>
//         </select>

//         <input
//           type="number"
//           placeholder="Shelf life (days)"
//           value={shelfLife}
//           onChange={(e) => setShelfLife(e.target.value)}
//           min="1"
//           style={{ marginRight: "10px", width: "150px" }}
//         />

//         <button type="submit">Add Ingredient</button>
//       </form>

//       <h3>Ingredient List</h3>

//       {loading ? (
//         <p>Loading...</p>
//       ) : ingredients.length === 0 ? (
//         <p>No ingredients found.</p>
//       ) : (
//         <ul>
//           {ingredients.map((ing) => (
//             <li key={ing.ingredient_id} style={{ marginBottom: "8px" }}>
//               <strong>{ing.name}</strong> — {ing.standard_unit}  
//               <br />
//               Shelf life: {ing.shelf_life_days} days
//             </li>
//           ))}
//         </ul>
//       )}
//     </div>
//   );
// }
