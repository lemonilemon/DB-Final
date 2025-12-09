import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  // ⭐ 如果使用者只有 Admin 角色 → 自動導到 Admin Dashboard
  useEffect(() => {
    if (user?.roles?.length === 1 && user.roles.includes("Admin")) {
      navigate("/admin");
    }
  }, [user, navigate]);

  return (
    <div className="page">
      <h1>Welcome, {user?.username}!</h1>

      <p className="muted">
        Your role: <strong>{user?.roles?.join(", ")}</strong>
      </p>

      <p className="muted">Choose what you want to do today:</p>

      {/* ⭐ 如果是單純 admin 就不要渲染一般 dashboard */}
      {user?.roles?.length === 1 && user.roles.includes("Admin") ? (
        <p>Redirecting to Admin Dashboard...</p>
      ) : (
        <div className="card-grid">
          <Link to="/fridges" className="card-link">
            <div className="card">
              <h2>🧊 Fridges</h2>
              <p>Manage your fridges, members and items.</p>
            </div>
          </Link>

          <Link to="/recipes" className="card-link">
            <div className="card">
              <h2>🍳 Recipes</h2>
              <p>Search and cook recipes.</p>
            </div>
          </Link>

          <Link to="/shopping" className="card-link">
            <div className="card">
              <h2>🛒 Shopping List</h2>
              <p>Plan what you need to buy.</p>
            </div>
          </Link>

          <Link to="/orders" className="card-link">
            <div className="card">
              <h2>📦 Orders</h2>
              <p>View and track orders.</p>
            </div>
          </Link>

          <Link to="/ingredients" className="card-link">
            <div className="card">
              <h2>🥦 Ingredients</h2>
              <p>Browse all available ingredients.</p>
            </div>
          </Link>

          {/* <Link to="/meal-plans" className="card-link">
            <div className="card">
              <h2>📅 Meal Plans</h2>
              <p>Plan meals on a calendar.</p>
            </div>
          </Link> */}

          {/* ⭐ Admin 仍保留 admin 卡片（如果有多角色時）*/}
          {user?.roles?.includes("Admin") && (
            <Link to="/admin" className="card-link">
              <div className="card admin-card">
                <h2>🔧 Admin</h2>
                <p>Manage ingredients, products and system data.</p>
              </div>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}


// import React from "react";
// import { Link } from "react-router-dom";
// import { useAuth } from "../../context/AuthContext";

// export default function DashboardPage() {
//   const { user } = useAuth();

//   return (
//     <div className="page">
//       <h1>Welcome, {user?.username}!</h1>

//       <p className="muted">
//         Your role: <strong>{user?.roles?.join(", ")}</strong>
//       </p>

//       <p className="muted">Choose what you want to do today:</p>

//       <div className="card-grid">
//         <Link to="/fridges" className="card-link">
//           <div className="card">
//             <h2>🧊 Fridges</h2>
//             <p>Manage your fridges, members and items.</p>
//           </div>
//         </Link>

//         <Link to="/recipes" className="card-link">
//           <div className="card">
//             <h2>🍳 Recipes</h2>
//             <p>Search and cook recipes.</p>
//           </div>
//         </Link>

//         <Link to="/shopping" className="card-link">
//           <div className="card">
//             <h2>🛒 Shopping List</h2>
//             <p>Plan what you need to buy.</p>
//           </div>
//         </Link>

//         <Link to="/orders" className="card-link">
//           <div className="card">
//             <h2>📦 Orders</h2>
//             <p>View and track orders.</p>
//           </div>
//         </Link>

//         <Link to="/meal-plans" className="card-link">
//           <div className="card">
//             <h2>📅 Meal Plans</h2>
//             <p>Plan meals on a calendar.</p>
//           </div>
//         </Link>

//         {/* 🟦 Admin-only card */}
//         {user?.roles?.includes("Admin") && (
//           <Link to="/admin" className="card-link">
//             <div className="card admin-card">
//               <h2>🔧 Admin</h2>
//               <p>Manage ingredients, products and system data.</p>
//             </div>
//           </Link>
//         )}
//       </div>
//     </div>
//   );
// }
