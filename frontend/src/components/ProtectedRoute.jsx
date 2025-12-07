import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth();

  console.log("🛡 ProtectedRoute user.roles =", user?.roles);

  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;

  if (roles && !user.roles?.some(r => roles.includes(r))) {
    return <Navigate to="/dashboard" />;
  }

  return <Outlet />;   // ←←← 重要！！
}


// import React from "react";
// import { Navigate, Outlet } from "react-router-dom";
// import { useAuth } from "../context/AuthContext";

// export default function ProtectedRoute({ roles }) {
//   const { isAuthenticated, user, loading } = useAuth();

//   console.log("🔐 ProtectedRoute roles=", roles);
//   console.log("🔐 user.roles=", user?.roles);


//   if (loading) {
//     return (
//       <div className="flex-center">
//         <p>Loading...</p>
//       </div>
//     );
//   }

//   if (!isAuthenticated) {
//     return <Navigate to="/login" replace />;
//   }

//   if (roles && roles.length > 0) {
//     const userRole = user?.role || "user";
//     if (!roles.includes(userRole)) {
//       return <Navigate to="/" replace />;
//     }
//   }

//   return <Outlet />;
// }
