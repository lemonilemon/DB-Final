import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getFridge,
  listFridgeItems,
  addItem,
  removeItem,
} from "../../api/fridge";
import { listIngredients } from "../../api/inventory";

export default function FridgeDetail() {
  const { id } = useParams();
  const [fridge, setFridge] = useState(null);
  const [items, setItems] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);

  // add item form
  const [ingredientId, setIngredientId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [expiryDate, setExpiryDate] = useState("");

  async function fetchAll() {
    setLoading(true);
    try {
      const [f, its, ings] = await Promise.all([
        getFridge(id),
        listFridgeItems(id),
        listIngredients(""),
      ]);
      setFridge(f);
      setItems(its);
      setIngredients(ings);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAll();
  }, [id]);

  async function handleAddItem(e) {
    e.preventDefault();
    if (!ingredientId || !quantity || !expiryDate) return;
    try {
      await addItem(id, {
        ingredient_id: parseInt(ingredientId, 10),
        quantity: parseFloat(quantity),
        expiry_date: expiryDate,
      });
      setIngredientId("");
      setQuantity("");
      setExpiryDate("");
      fetchAll();
    } catch (err) {
      console.error("add item failed:", err);
    }
  }

  async function handleRemoveItem(itemId) {
    if (!window.confirm("Remove this item?")) return;
    try {
      await removeItem(id, itemId);
      setItems((prev) => prev.filter((i) => i.fridge_item_id !== itemId));
    } catch (err) {
      console.error(err);
    }
  }

  if (loading) return <p>Loading...</p>;
  if (!fridge) return <p>Fridge not found.</p>;

  return (
    <div>
      <h2>{fridge.fridge_name}</h2>
      {fridge.description && <p>{fridge.description}</p>}

      <section className="section">
        <h3>Inventory</h3>
        {items.length === 0 ? (
          <p>No items.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Ingredient</th>
                <th>Qty</th>
                <th>Unit</th>
                <th>Expiry</th>
                <th>Days left</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.fridge_item_id}>
                  <td>{it.ingredient_name}</td>
                  <td>{it.quantity}</td>
                  <td>{it.standard_unit}</td>
                  <td>{it.expiry_date}</td>
                  <td>{it.days_until_expiry}</td>
                  <td>
                    <button
                      className="btn-small"
                      onClick={() => handleRemoveItem(it.fridge_item_id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="section">
        <h3>Add item</h3>
        <form onSubmit={handleAddItem} className="form-inline">
          <select
            value={ingredientId}
            onChange={(e) => setIngredientId(e.target.value)}
          >
            <option value="">Select ingredient</option>
            {ingredients.map((ing) => (
              <option key={ing.ingredient_id} value={ing.ingredient_id}>
                {ing.name} ({ing.standard_unit})
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Quantity"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />
          <input
            type="date"
            value={expiryDate}
            onChange={(e) => setExpiryDate(e.target.value)}
          />
          <button className="btn-small" type="submit">
            Add
          </button>
        </form>
      </section>
    </div>
  );
}
