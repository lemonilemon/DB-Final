import { useEffect, useState } from "react";
import { listRecipes } from "../../api/recipes";
import { Link } from "react-router-dom";

export default function RecipeList() {
  const [recipes, setRecipes] = useState([]);
  const [search, setSearch] = useState("");

  async function fetchRecipes() {
    try {
      const data = await listRecipes(search);
      setRecipes(data);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    fetchRecipes();
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    fetchRecipes();
  }

  return (
    <div>
      <h2>Recipes</h2>
      <form onSubmit={handleSubmit} className="form-inline">
        <input
          placeholder="Search recipe name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="btn-small">Search</button>
      </form>

      {recipes.length === 0 ? (
        <p>No recipes.</p>
      ) : (
        <ul className="list">
          {recipes.map((r) => (
            <li key={r.recipe_id} className="list-item">
              <div>
                <strong>{r.recipe_name}</strong>
                {r.average_rating && (
                  <span> · ★ {r.average_rating.toFixed(1)}</span>
                )}
                {r.review_count && <span> ({r.review_count} reviews)</span>}
              </div>
              <Link className="btn-small" to={`/recipes/${r.recipe_id}`}>
                View
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
