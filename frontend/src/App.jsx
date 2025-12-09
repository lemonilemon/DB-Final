import React from "react";
import { Routes, Route } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";

import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";

import DashboardPage from "./pages/dashboard/DashboardPage";

import FridgeListPage from "./pages/fridge/FridgeListPage";
import FridgeDetailPage from "./pages/fridge/FridgeDetailPage";

import RecipeListPage from "./pages/recipes/RecipeListPage";
import RecipeDetailPage from "./pages/recipes/RecipeDetailPage";

import ShoppingListPage from "./pages/shopping/ShoppingListPage";
import OrdersPage from "./pages/orders/OrdersPage";

import MealPlansPage from "./pages/mealplan/MealPlanPage";

import AdminDashboard from "./pages/admin/AdminDashboard";

import UserIngredients from "./pages/dashboard/UserIngredients";

import { Outlet } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

/* -------------------------------
   Protected layout (navbar + outlet)
-------------------------------- */
function ProtectedLayout() {
  const { loading } = useAuth();
  if (loading) return <div className="page">Loading...</div>;

  return (
    <>
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
    </>
  );
}

/* -------------------------------
   Main App
-------------------------------- */
export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* ------ public routes ------ */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* ------ everything below needs login ------ */}
        <Route element={<ProtectedLayout />}>
          {/* Default page after login */}
          <Route index element={<DashboardPage />} />

          {/* Fridge */}
          <Route path="/fridges" element={<FridgeListPage />} />
          <Route path="/fridges/:fridgeId" element={<FridgeDetailPage />} />

          {/* Recipes */}
          <Route path="/recipes" element={<RecipeListPage />} />
          <Route path="/recipes/:recipeId" element={<RecipeDetailPage />} />

          {/* Shopping */}
          <Route path="/shopping" element={<ShoppingListPage />} />

          {/* Orders */}
          <Route path="/orders" element={<OrdersPage />} />

          {/* Meal plans */}
          <Route path="/meal-plans" element={<MealPlansPage />} />

          {/* Ingredient list */}
          <Route path="/ingredients" element={<UserIngredients />} />

          {/* ------ admin bashboard test ------
          <Route
            path="/admin"
            element={<div style={{ fontSize: 40 }}>ADMIN TEST</div>}
          /> */}
          {/* <Route path="/admin" element={<AdminDashboard />} /> */}

          {/* ------ admin only routes ------ */}
          {/* <Route
            path="/admin"
            element={
              <ProtectedRoute roles={["Admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          /> */}

          <Route element={<ProtectedRoute roles={["Admin"]} />}>
            <Route path="/admin" element={<AdminDashboard />} />
          </Route>

        </Route>

        {/* fallback → redirect to login */}
        <Route path="*" element={<LoginPage />} />
      </Routes>
    </AuthProvider>
  );
}
