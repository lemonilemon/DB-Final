import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { searchRecipes, getAllRecipes, createRecipe } from "../../api/recipes";
import { searchIngredients } from "../../api/ingredients";

export default function RecipeListPage() {
  const [q, setQ] = useState("");
  const [recipes, setRecipes] = useState([]);

  // Create Recipe Form States
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    recipe_name: "",
    description: "",
    cooking_time: "",
  });

  // ⭐ Requirements with ingredient search UI
  const [requirements, setRequirements] = useState([
    {
      ingredient_id: "",
      quantity_needed: "",
      searchQuery: "",
      searchResults: [],
    },
  ]);

  const [steps, setSteps] = useState([{ step_number: 1, description: "" }]);

  // SEARCH
  const handleSearch = async (e) => {
    e?.preventDefault();
    let data = q.trim() ? await searchRecipes(q) : await getAllRecipes();
    setRecipes(data);
  };

  // LOAD ALL
  useEffect(() => {
    handleSearch();
  }, []);

  // =============================
  // Add requirement row
  // =============================
  const addRequirement = () => {
    setRequirements([
      ...requirements,
      {
        ingredient_id: "",
        quantity_needed: "",
        searchQuery: "",
        searchResults: [],
      },
    ]);
  };

  // =============================
  // Add step row
  // =============================
  const addStep = () => {
    const num = steps.length + 1;
    setSteps([...steps, { step_number: num, description: "" }]);
  };

  // =============================
  // Ingredient Search Handler
  // =============================
  const handleIngredientSearch = async (idx) => {
    const query = requirements[idx].searchQuery.trim();
    if (!query) return;

    try {
      const results = await searchIngredients(query);

      const list = [...requirements];
      list[idx].searchResults = results;
      setRequirements(list);
    } catch (err) {
      console.error(err);
    }
  };

  // =============================
  // Select Ingredient
  // =============================
  const handleSelectIngredient = (idx, ingredient) => {
    const list = [...requirements];

    list[idx].ingredient_id = ingredient.ingredient_id;
    list[idx].searchQuery = ingredient.name;
    list[idx].searchResults = []; // ⭐ auto-close search results

    setRequirements(list);
  };

  // =============================
  // Create recipe handler
  // =============================
  const handleCreateRecipe = async (e) => {
    e.preventDefault();

    if (!form.cooking_time || Number(form.cooking_time) <= 0) {
      alert("Please enter a valid cooking time.");
      return;
    }

    const filteredReqs = requirements
      .filter((r) => r.ingredient_id && r.quantity_needed)
      .map((r) => ({
        ingredient_id: Number(r.ingredient_id),
        quantity_needed: Number(r.quantity_needed),
      }));

    if (filteredReqs.length === 0) {
      alert("Please add at least one ingredient.");
      return;
    }

    const filteredSteps = steps
      .filter((s) => s.description.trim() !== "")
      .map((s, idx) => ({
        step_number: idx + 1,
        description: s.description.trim(),
      }));

    if (filteredSteps.length === 0) {
      alert("Please add at least one step.");
      return;
    }

    const payload = {
      recipe_name: form.recipe_name,
      description: form.description,
      cooking_time: Number(form.cooking_time),
      requirements: filteredReqs,
      steps: filteredSteps,
    };

    try {
      await createRecipe(payload);
      alert("Recipe created!");

      // Reset
      setForm({ recipe_name: "", description: "", cooking_time: "" });
      setRequirements([
        { ingredient_id: "", quantity_needed: "", searchQuery: "", searchResults: [] },
      ]);
      setSteps([{ step_number: 1, description: "" }]);
      setShowCreate(false);

      await handleSearch();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to create recipe.");
    }
  };

  return (
    <div className="page">
      <h1>Recipes</h1>

      {/* SEARCH BAR */}
      <form onSubmit={handleSearch} className="inline-form">
        <input
          placeholder="Search recipe name / ingredient"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button className="btn-primary">Search</button>
      </form>

      {/* TOGGLE CREATE FORM */}
      <button
        className="btn-primary"
        style={{ marginTop: "20px" }}
        onClick={() => setShowCreate(!showCreate)}
      >
        {showCreate ? "Cancel" : "Create New Recipe"}
      </button>

      {/* CREATE FORM */}
      {showCreate && (
        <form
          onSubmit={handleCreateRecipe}
          style={{
            border: "1px solid #ccc",
            padding: "20px",
            marginTop: "20px",
            borderRadius: "8px",
          }}
        >
          <h2>Create Recipe</h2>

          <label>Recipe Name</label>
          <input
            value={form.recipe_name}
            onChange={(e) =>
              setForm((f) => ({ ...f, recipe_name: e.target.value }))
            }
          />

          <label>Description</label>
          <textarea
            value={form.description}
            onChange={(e) =>
              setForm((f) => ({ ...f, description: e.target.value }))
            }
          />

          <label>Cooking Time (minutes)</label>
          <input
            type="number"
            value={form.cooking_time}
            onChange={(e) =>
              setForm((f) => ({ ...f, cooking_time: e.target.value }))
            }
          />

          {/* ============================= */}
          {/* INGREDIENT REQUIREMENTS */}
          {/* ============================= */}
          <h3>Ingredients</h3>

          {requirements.map((req, idx) => (
            <div key={idx} style={{ marginBottom: "20px" }}>
              {/* ---- Search Ingredient Name ---- */}
              <input
                placeholder="Search ingredient..."
                value={req.searchQuery}
                onChange={(e) => {
                  const list = [...requirements];
                  list[idx].searchQuery = e.target.value;
                  setRequirements(list);
                }}
                style={{ marginRight: "10px" }}
              />

              <button
                type="button"
                onClick={() => handleIngredientSearch(idx)}
              >
                Search
              </button>

              {/* ---- Search Results Cards ---- */}
              <div className="card-grid" style={{ marginTop: "10px" }}>
                {req.searchResults.map((ing) => (
                  <div key={ing.ingredient_id} className="card">
                    <h4>{ing.name}</h4>
                    <p>Unit: {ing.standard_unit}</p>

                    <button
                      onClick={() => handleSelectIngredient(idx, ing)}
                    >
                      Select
                    </button>

                    {/* small close */}
                    <button
                      className="btn-link"
                      style={{
                        color: "#888",
                        marginTop: 6,
                        fontSize: "0.85em",
                      }}
                      onClick={() => {
                        const list = [...requirements];
                        list[idx].searchResults = [];
                        setRequirements(list);
                      }}
                    >
                      close
                    </button>
                  </div>
                ))}
              </div>

              {/* ---- Selected ingredient_id (readonly) ---- */}
              <input
                placeholder="ingredient_id (auto-filled)"
                value={req.ingredient_id}
                readOnly
                style={{ marginTop: "10px", background: "#eee" }}
              />

              {/* ---- Quantity ---- */}
              <input
                placeholder="quantity"
                type="number"
                value={req.quantity_needed}
                onChange={(e) => {
                  const list = [...requirements];
                  list[idx].quantity_needed = e.target.value;
                  setRequirements(list);
                }}
                style={{ marginLeft: "10px" }}
              />
            </div>
          ))}

          <button type="button" onClick={addRequirement}>
            + Add Ingredient
          </button>

          {/* =============== STEPS =============== */}
          <h3 style={{ marginTop: "20px" }}>Steps</h3>

          {steps.map((st, idx) => (
            <div key={idx} style={{ display: "flex", flexDirection: "column" }}>
              <label>Step {idx + 1}</label>
              <textarea
                value={st.description}
                onChange={(e) => {
                  const list = [...steps];
                  list[idx].description = e.target.value;
                  setSteps(list);
                }}
              />
            </div>
          ))}

          <button type="button" onClick={addStep}>
            + Add Step
          </button>

          {/* SUBMIT BUTTON */}
          <button
            className="btn-primary"
            style={{ marginTop: "20px" }}
            type="submit"
          >
            Create Recipe
          </button>
        </form>
      )}

      {/* RECIPE LIST */}
      <div className="card-grid" style={{ marginTop: "20px" }}>
        {recipes.map((r) => (
          <Link
            to={`/recipes/${r.recipe_id}`}
            key={r.recipe_id}
            className="card-link"
          >
            <div className="card">
              <h2>{r.recipe_name}</h2>
              <p className="muted">{r.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}


// import React, { useEffect, useState } from "react";
// import { Link } from "react-router-dom";
// import { searchRecipes, getAllRecipes, createRecipe } from "../../api/recipes";

// export default function RecipeListPage() {
//   const [q, setQ] = useState("");
//   const [recipes, setRecipes] = useState([]);

//   // Create Recipe Form States
//   const [showCreate, setShowCreate] = useState(false);
//   const [form, setForm] = useState({
//     recipe_name: "",
//     description: "",
//     cooking_time: "",
//   });

//   const [requirements, setRequirements] = useState([
//     { ingredient_id: "", quantity_needed: "" },
//   ]);

//   const [steps, setSteps] = useState([{ step_number: 1, description: "" }]);

//   // SEARCH
//   const handleSearch = async (e) => {
//     e?.preventDefault();
//     let data = q.trim() ? await searchRecipes(q) : await getAllRecipes();
//     setRecipes(data);
//   };

//   // LOAD ALL
//   useEffect(() => {
//     handleSearch();
//   }, []);

//   // ADD REQUIREMENT ROW
//   const addRequirement = () => {
//     setRequirements([...requirements, { ingredient_id: "", quantity_needed: "" }]);
//   };

//   // ADD STEP ROW
//   const addStep = () => {
//     const num = steps.length + 1;
//     setSteps([...steps, { step_number: num, description: "" }]);
//   };

//   // HANDLE CREATE RECIPE
//   const handleCreateRecipe = async (e) => {
//   e.preventDefault();

//   // 驗證 cooking_time
//   if (!form.cooking_time || Number(form.cooking_time) <= 0) {
//     alert("Please enter a valid cooking time.");
//     return;
//   }

//   // 過濾掉空的 requirements
//   const filteredReqs = requirements
//       .filter((r) => r.ingredient_id && r.quantity_needed)
//       .map((r) => ({
//         ingredient_id: Number(r.ingredient_id),
//         quantity_needed: Number(r.quantity_needed),
//       }));

//     if (filteredReqs.length === 0) {
//       alert("Please add at least one ingredient.");
//       return;
//     }

//     // 過濾掉空白步驟
//     const filteredSteps = steps
//       .filter((s) => s.description.trim() !== "")
//       .map((s, idx) => ({
//         step_number: idx + 1,
//         description: s.description.trim(),
//       }));

//     if (filteredSteps.length === 0) {
//       alert("Please add at least one step.");
//       return;
//     }

//     const payload = {
//       recipe_name: form.recipe_name,
//       description: form.description,
//       cooking_time: Number(form.cooking_time),
//       requirements: filteredReqs,
//       steps: filteredSteps,
//     };

//     try {
//       await createRecipe(payload);

//       alert("Recipe created!");

//       // RESET
//       setForm({ recipe_name: "", description: "", cooking_time: "" });
//       setRequirements([{ ingredient_id: "", quantity_needed: "" }]);
//       setSteps([{ step_number: 1, description: "" }]);
//       setShowCreate(false);

//       await handleSearch();
//     } catch (err) {
//       console.error(err);
//       alert(err.response?.data?.detail || "Failed to create recipe.");
//     }
//   };


//   return (
//     <div className="page">
//       <h1>Recipes</h1>

//       {/* -------- SEARCH BAR -------- */}
//       <form onSubmit={handleSearch} className="inline-form">
//         <input
//           placeholder="Search recipe name / ingredient"
//           value={q}
//           onChange={(e) => setQ(e.target.value)}
//         />
//         <button className="btn-primary">Search</button>
//       </form>

//       {/* -------- TOGGLE CREATE FORM -------- */}
//       <button
//         className="btn-primary"
//         style={{ marginTop: "20px" }}
//         onClick={() => setShowCreate(!showCreate)}
//       >
//         {showCreate ? "Cancel" : "Create New Recipe"}
//       </button>

//       {/* -------- CREATE RECIPE FORM -------- */}
//       {showCreate && (
//         <form
//           onSubmit={handleCreateRecipe}
//           style={{
//             border: "1px solid #ccc",
//             padding: "20px",
//             marginTop: "20px",
//             borderRadius: "8px",
//           }}
//         >
//           <h2>Create Recipe</h2>

//           <label>Recipe Name</label>
//           <input
//             value={form.recipe_name}
//             onChange={(e) =>
//               setForm((f) => ({ ...f, recipe_name: e.target.value }))
//             }
//           />

//           <label>Description</label>
//           <textarea
//             value={form.description}
//             onChange={(e) =>
//               setForm((f) => ({ ...f, description: e.target.value }))
//             }
//           />

//           <label>Cooking Time (minutes)</label>
//           <input
//             type="number"
//             value={form.cooking_time}
//             onChange={(e) =>
//               setForm((f) => ({ ...f, cooking_time: e.target.value }))
//             }
//           />

//           {/* REQUIREMENTS */}
//           <h3>Ingredients</h3>
//           {requirements.map((req, idx) => (
//             <div key={idx} style={{ display: "flex", gap: "10px" }}>
//               <input
//                 placeholder="ingredient_id"
//                 value={req.ingredient_id}
//                 type="number"
//                 onChange={(e) => {
//                   const list = [...requirements];
//                   list[idx].ingredient_id = e.target.value;
//                   setRequirements(list);
//                 }}
//               />

//               <input
//                 placeholder="quantity"
//                 value={req.quantity_needed}
//                 type="number"
//                 onChange={(e) => {
//                   const list = [...requirements];
//                   list[idx].quantity_needed = e.target.value;
//                   setRequirements(list);
//                 }}
//               />
//             </div>
//           ))}
//           <button type="button" onClick={addRequirement}>
//             + Add Ingredient
//           </button>

//           {/* STEPS */}
//           <h3 style={{ marginTop: "20px" }}>Steps</h3>
//           {steps.map((st, idx) => (
//             <div key={idx} style={{ display: "flex", flexDirection: "column" }}>
//               <label>Step {idx + 1}</label>
//               <textarea
//                 value={st.description}
//                 onChange={(e) => {
//                   const list = [...steps];
//                   list[idx].description = e.target.value;
//                   setSteps(list);
//                 }}
//               />
//             </div>
//           ))}
//           <button type="button" onClick={addStep}>
//             + Add Step
//           </button>

//           <button
//             className="btn-primary"
//             style={{ marginTop: "20px" }}
//             type="submit"
//           >
//             Create Recipe
//           </button>
//         </form>
//       )}

//       {/* -------- RECIPE LIST -------- */}
//       <div className="card-grid" style={{ marginTop: "20px" }}>
//         {recipes.map((r) => (
//           <Link to={`/recipes/${r.recipe_id}`} key={r.recipe_id} className="card-link">
//             <div className="card">
//               <h2>{r.recipe_name}</h2>
//               <p className="muted">{r.description}</p>
//             </div>
//           </Link>
//         ))}
//       </div>
//     </div>
//   );
// }
