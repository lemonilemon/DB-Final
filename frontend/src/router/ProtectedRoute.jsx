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


// import { Navigate } from "react-router-dom";
// import { useAuth } from "../context/AuthContext";

// export default function ProtectedRoute({ roles, children }) {
//   const { user, loading } = useAuth();

//   console.log("🛡 ProtectedRoute activated");
//   console.log("🛡 user.roles =", user?.roles);
//   console.log("🛡 allowed roles =", roles);


//   if (loading) return <div className="page-center">Loading...</div>;
//   if (!user) return <Navigate to="/login" replace />;

//   if (roles && roles.length > 0) {
//     const allowed = user.roles?.some((r) => roles.includes(r));
//     if (!allowed) return <Navigate to="/dashboard" replace />;
//   }

//   return children;
// }

