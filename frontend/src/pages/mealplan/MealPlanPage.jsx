import React, { useEffect, useState } from "react";
import {
  getMealPlans,
  createMealPlan,
  deleteMealPlan,
} from "../../api/mealplan";
import { searchRecipes } from "../../api/recipes";
import { checkAvailability, addShoppingItem } from "../../api/shopping";

export default function MealPlansPage() {
  const [plans, setPlans] = useState([]);

  // 🔍 搜尋食譜欄位與結果
  const [recipeQuery, setRecipeQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  // 🟦 使用者選取的 recipe（完整 recipe object）
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  // 🟦 meal plan 建立表單
  const [form, setForm] = useState({
    date: "", // planned_date
  });

  // ------------------------------------
  // 初始化載入 meal plan
  // ------------------------------------
  const loadPlans = async () => {
    const p = await getMealPlans();
    setPlans(p);
  };

  useEffect(() => {
    loadPlans();
  }, []);

  // ------------------------------------
  // 搜尋食譜
  // ------------------------------------
  const handleSearchRecipes = async (e) => {
    e.preventDefault();
    if (!recipeQuery.trim()) return;

    const data = await searchRecipes(recipeQuery);
    setSearchResults(data);
  };

  // ------------------------------------
  // 建立 Meal Plan（符合後端格式）
  // ------------------------------------
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.date || !selectedRecipe) return alert("請選擇日期與食譜");

    // 這裡要修：selectedRecipe.id → selectedRecipe.recipe_id
    const payload = {
      recipe_id: selectedRecipe.recipe_id,
      planned_date: form.date,
    };

    console.log("Sending payload:", payload);

    await createMealPlan(payload);

    // 清理表單
    setSelectedRecipe(null);
    setRecipeQuery("");
    setSearchResults([]);
    setForm({ date: "" });

    await loadPlans();
  };

  const handleDelete = async (id) => {
    await deleteMealPlan(id);
    await loadPlans();
  };

  // ------------------------------------
  // Add missing ingredients to shopping list
  // ------------------------------------
  const handleAddMissingIngredients = async (plan) => {
    try {
      // Check availability to get missing ingredients
      // Pass plan_id to avoid double-counting this meal plan
      const availability = await checkAvailability(
        plan.recipe_id,
        plan.fridge_id,
        plan.planned_date,
        plan.plan_id  // Exclude this plan from timeline to avoid double-counting
      );

      if (availability.all_available) {
        alert("All ingredients are available!");
        return;
      }

      // Add each missing ingredient to shopping list
      for (const missing of availability.missing_ingredients) {
        await addShoppingItem({
          ingredient_id: missing.ingredient_id,
          quantity_to_buy: missing.shortage,
          needed_by: missing.needed_by,
        });
      }

      alert(
        `Added ${availability.missing_ingredients.length} ingredient(s) to shopping list!`
      );
    } catch (error) {
      console.error("Error adding ingredients:", error);
      alert("Failed to add ingredients to shopping list");
    }
  };

  return (
    <div className="page">
      <h1>Meal Plans</h1>

      {/* 🟦 建立 Meal Plan 表單 */}
      <form onSubmit={handleCreate} className="meal-form">

        {/* 日期 */}
        <input
          type="date"
          name="date"
          value={form.date}
          onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
        />

        {/* 顯示選中的食譜 */}
        {selectedRecipe ? (
          <div className="selected-box">
            <strong>Selected recipe:</strong> {selectedRecipe.recipe_name}
            <button
              type="button"
              className="btn-link danger"
              onClick={() => setSelectedRecipe(null)}
            >
              remove
            </button>
          </div>
        ) : (
          <p className="muted">No recipe selected</p>
        )}

        <button className="btn-primary">Add</button>
      </form>

      <hr />

      {/* 🔍 搜尋食譜 */}
      <h3>Search Recipes</h3>
      <form onSubmit={handleSearchRecipes} className="inline-form">
        <input
          type="text"
          placeholder="Search recipes..."
          value={recipeQuery}
          onChange={(e) => setRecipeQuery(e.target.value)}
        />
        <button className="btn-primary">Search</button>
      </form>

      {/* 🔍 搜尋結果列表 */}
      <div className="card-grid" style={{ marginTop: 20 }}>
        {searchResults.map((r) => (
          <div className="card" key={r.recipe_id}>
            <h3>{r.recipe_name}</h3>
            <p className="muted">{r.description}</p>
            <button
              className="btn-primary"
              onClick={() => setSelectedRecipe(r)}
            >
              Select
            </button>
          </div>
        ))}
      </div>

      <hr />

      {/* 🟦 meal plan list */}
      <table className="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Recipe</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {plans.map((p) => (
            <tr key={p.plan_id}>
              <td>{p.planned_date}</td>
              <td>{p.recipe_name}</td>
              <td>
                <span
                  style={{
                    color:
                      p.status === "Ready"
                        ? "green"
                        : p.status === "Insufficient"
                        ? "red"
                        : p.status === "Finished"
                        ? "blue"
                        : p.status === "Cancelled"
                        ? "gray"
                        : "orange",
                  }}
                >
                  {p.status}
                </span>
              </td>
              <td>
                {p.status === "Insufficient" && (
                  <button
                    className="btn-primary"
                    style={{ marginRight: 8 }}
                    onClick={() => handleAddMissingIngredients(p)}
                  >
                    Add to Cart
                  </button>
                )}
                <button
                  className="btn-link danger"
                  onClick={() => handleDelete(p.plan_id)}
                >
                  remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
