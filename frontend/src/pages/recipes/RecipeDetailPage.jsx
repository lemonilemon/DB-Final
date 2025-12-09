import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { 
  getRecipeDetail, 
  cookRecipe,
  getRecipeReviews,
  submitRecipeReview
} from "../../api/recipes";

import { getUserFridges } from "../../api/fridge";

export default function RecipeDetailPage() {
  const { recipeId } = useParams();

  const [recipe, setRecipe] = useState(null);
  const [message, setMessage] = useState("");

  const [fridges, setFridges] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedFridge, setSelectedFridge] = useState("");

  // ⭐ Review states
  const [reviews, setReviews] = useState([]);
  const [myRating, setMyRating] = useState(5);
  const [myComment, setMyComment] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");

  // ---------------------------
  // Load recipe
  // ---------------------------
  const loadRecipe = async () => {
    const data = await getRecipeDetail(recipeId);
    setRecipe(data);
  };

  // ---------------------------
  // Load fridges
  // ---------------------------
  const loadFridges = async () => {
    const list = await getUserFridges();
    setFridges(list);
  };

  // ---------------------------
  // Load Reviews
  // ---------------------------
  const loadReviews = async () => {
    try {
      const list = await getRecipeReviews(recipeId);
      setReviews(list);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadRecipe();
    loadFridges();
    loadReviews();
  }, [recipeId]);


  // ---------------------------
  // Cooking handler
  // ---------------------------
  const handleCookClick = () => setShowModal(true);

  const handleCookConfirm = async () => {
    try {
      const result = await cookRecipe(recipeId, selectedFridge);
      setMessage(result.message || "Cooked!");
    } catch (err) {
      console.error(err);
      setMessage(err.response?.data?.detail || "Cook failed.");
    }
    setShowModal(false);
  };


  // ---------------------------
  // Submit Review
  // ---------------------------
  const handleSubmitReview = async () => {
    try {
      await submitRecipeReview(recipeId, {
        rating: Number(myRating),
        comment: myComment
      });

      setReviewMessage("Review submitted!");
      setMyComment("");

      await loadReviews();
    } catch (err) {
      console.error(err);
      setReviewMessage(err.response?.data?.detail || "Failed to submit review.");
    }
  };


  if (!recipe) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>{recipe.recipe_name}</h1>
      <p className="muted">{recipe.description}</p>

      {/* ---- Cook button ---- */}
      <button className="btn-primary" onClick={handleCookClick}>
        Cook this recipe
      </button>

      {message && <p style={{ marginTop: 10, color: "green" }}>{message}</p>}

      {/* ------------------------------ */}
      {/* Modal: Select fridge */}
      {/* ------------------------------ */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal">
            <h3>Select a fridge</h3>

            <select
              value={selectedFridge}
              onChange={(e) => setSelectedFridge(e.target.value)}
            >
              <option value="">-- choose --</option>
              {fridges.map((f) => (
                <option key={f.fridge_id} value={f.fridge_id}>
                  {f.fridge_name}
                </option>
              ))}
            </select>

            <div className="modal-actions">
              <button onClick={() => setShowModal(false)}>Cancel</button>
              <button
                disabled={!selectedFridge}
                className="btn-primary"
                onClick={handleCookConfirm}
              >
                Cook
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------ */}
      {/* Ingredients */}
      {/* ------------------------------ */}
      <section className="section">
        <h2>Ingredients</h2>
        <ul>
          {recipe.requirements?.map((req) => (
            <li key={req.ingredient_id}>
              {req.ingredient_name} — {req.quantity_needed} {req.standard_unit}
            </li>
          ))}
        </ul>
      </section>

      {/* ------------------------------ */}
      {/* Steps */}
      {/* ------------------------------ */}
      <section className="section">
        <h2>Steps</h2>
        <ol>
          {recipe.steps?.map((s, idx) => (
            <li key={idx}>{s.description}</li>
          ))}
        </ol>
      </section>

      {/* ------------------------------ */}
      {/* Add / Update Review */}
      {/* ------------------------------ */}
      <section className="section">
        <h2>Write a Review</h2>

        <label>Rating</label>
        <select
          value={myRating}
          onChange={(e) => setMyRating(e.target.value)}
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>

        <label>Comment</label>
        <textarea
          value={myComment}
          onChange={(e) => setMyComment(e.target.value)}
        />

        <button className="btn-primary" onClick={handleSubmitReview}>
          Submit Review
        </button>

        {reviewMessage && (
          <p style={{ marginTop: 10, color: "green" }}>{reviewMessage}</p>
        )}
      </section>

      {/* ------------------------------ */}
      {/* Reviews - List */}
      {/* ------------------------------ */}
      <section className="section">
        <h2>Reviews</h2>

        {reviews.length === 0 ? (
          <p>No reviews yet.</p>
        ) : (
          <ul className="list">
            {reviews.map((r) => (
              <li key={r.user_id} className="list-item">
                <strong>{r.user_name}</strong> — ⭐ {r.rating}
                <br />
                {r.comment}
                <br />
                <span className="muted">{new Date(r.review_date).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

    </div>
  );
}
