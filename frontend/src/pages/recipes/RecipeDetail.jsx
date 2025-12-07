import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getRecipeDetail,
  cookRecipe,
  listReviews,
  createReview,
} from "../../api/recipes";
import { listFridges } from "../../api/fridge";

export default function RecipeDetail() {
  const { id } = useParams();
  const [recipe, setRecipe] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [fridges, setFridges] = useState([]);
  const [selectedFridge, setSelectedFridge] = useState("");
  const [cookingMsg, setCookingMsg] = useState("");
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [r, rev, fs] = await Promise.all([
          getRecipeDetail(id),
          listReviews(id),
          listFridges(),
        ]);
        setRecipe(r);
        setReviews(rev);
        setFridges(fs);
        if (fs.length > 0) setSelectedFridge(fs[0].fridge_id);
      } catch (err) {
        console.error(err);
      }
    })();
  }, [id]);

  async function handleCook() {
    if (!selectedFridge) {
      alert("Select a fridge.");
      return;
    }
    setCookingMsg("");
    try {
      const res = await cookRecipe(id, { fridge_id: selectedFridge });
      setCookingMsg(res.message || "Cooked successfully.");
    } catch (err) {
      console.error(err);
      setCookingMsg("Failed to cook. Check inventory.");
    }
  }

  async function handleReview(e) {
    e.preventDefault();
    try {
      await createReview(id, { rating: Number(rating), comment });
      const newReviews = await listReviews(id);
      setReviews(newReviews);
      setComment("");
    } catch (err) {
      console.error(err);
    }
  }

  if (!recipe) return <p>Loading...</p>;

  return (
    <div>
      <h2>{recipe.recipe_name}</h2>
      {recipe.average_rating && (
        <p>
          ★ {recipe.average_rating.toFixed(1)} ({recipe.review_count} reviews)
        </p>
      )}

      <section className="section">
        <h3>Ingredients</h3>
        <ul className="list">
          {recipe.ingredients.map((i) => (
            <li key={i.ingredient_id}>
              {i.ingredient_name} — {i.quantity_needed} {i.standard_unit}
            </li>
          ))}
        </ul>
      </section>

      <section className="section">
        <h3>Steps</h3>
        <ol className="list">
          {recipe.steps
            .sort((a, b) => a.step_number - b.step_number)
            .map((s) => (
              <li key={s.step_number}>
                <strong>Step {s.step_number}:</strong> {s.description}
              </li>
            ))}
        </ol>
      </section>

      <section className="section">
        <h3>Cook this recipe</h3>
        <div className="form-inline">
          <select
            value={selectedFridge}
            onChange={(e) => setSelectedFridge(e.target.value)}
          >
            {fridges.map((f) => (
              <option key={f.fridge_id} value={f.fridge_id}>
                {f.fridge_name}
              </option>
            ))}
          </select>
          <button className="btn-primary" onClick={handleCook}>
            Cook
          </button>
        </div>
        {cookingMsg && <p>{cookingMsg}</p>}
      </section>

      <section className="section">
        <h3>Reviews</h3>
        {reviews.length === 0 ? (
          <p>No reviews yet.</p>
        ) : (
          <ul className="list">
            {reviews.map((r) => (
              <li key={r.review_id}>
                <strong>{r.user_name}</strong> — ★ {r.rating}
                {r.comment && <span>: {r.comment}</span>}
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={handleReview} className="form-vertical">
          <label>
            Rating
            <input
              type="number"
              min="1"
              max="5"
              value={rating}
              onChange={(e) => setRating(e.target.value)}
            />
          </label>
          <label>
            Comment
            <textarea
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </label>
          <button className="btn-small" type="submit">
            Submit review
          </button>
        </form>
      </section>
    </div>
  );
}
