import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const isOnlyAdmin =
    user?.roles?.length === 1 && user.roles.includes("Admin");

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <Link to="/" className="logo">
        NEW FRIDGE
      </Link>

      <div className="nav-links">
        {/* ⭐ 如果只有 Admin 角色 → 只顯示 Admin */}
        {isOnlyAdmin ? (
          <NavLink to="/admin">Admin</NavLink>
        ) : (
          <>
            <NavLink to="/fridges">Fridges</NavLink>
            <NavLink to="/recipes">Recipes</NavLink>
            <NavLink to="/shopping">Shopping</NavLink>
            <NavLink to="/orders">Orders</NavLink>
            {/* <NavLink to="/meal-plans">Meal Plans</NavLink> */}

            {/* 多角色 Admin 也能看到 Admin */}
            {user?.roles?.includes("Admin") && (
              <NavLink to="/admin">Admin</NavLink>
            )}
          </>
        )}
      </div>

      <div className="nav-user">
        {user && <span className="username">Hi, {user.username}</span>}
        <button className="btn-outline" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}


// import React from "react";
// import { Link, NavLink, useNavigate } from "react-router-dom";
// import { useAuth } from "../context/AuthContext";

// export default function Navbar() {
//   const { user, logout } = useAuth();
//   const navigate = useNavigate();

//   console.log("NAV USER ROLES =", user?.roles);

//   const handleLogout = () => {
//     logout();           // 清空 token / user
//     navigate("/login"); // ⭐ 登出後跳去 login
//   };

//   return (
//     <nav className="navbar">
//       <Link to="/" className="logo">
//         NEW FRIDGE
//       </Link>

//       <div className="nav-links">
//         <NavLink to="/fridges">Fridges</NavLink>
//         <NavLink to="/recipes">Recipes</NavLink>
//         <NavLink to="/shopping">Shopping</NavLink>
//         <NavLink to="/orders">Orders</NavLink>
//         <NavLink to="/meal-plans">Meal Plans</NavLink>
//         {/* ⭐ 只有 Admin 才能看到 Admin 分頁 */}
//         {user?.roles?.includes("Admin") && (
//           <NavLink to="/admin">Admin</NavLink>
//         )}
//       </div>

//       <div className="nav-user">
//         {user && <span className="username">Hi, {user.username}</span>}
//         <button className="btn-outline" onClick={handleLogout}>
//           Logout
//         </button>
//       </div>
//     </nav>
//   );
// }
