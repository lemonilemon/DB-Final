import { useEffect, useState } from "react";
import {
  getShoppingList,
  addToShoppingList,
  removeFromShoppingList,
  createOrdersFromList,
} from "../../api/procurement";
import { listIngredients } from "../../api/inventory";

export default function ShoppingList() {
  const [items, setItems] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [ingredientId, setIngredientId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [msg, setMsg] = useState("");

  async function fetchAll() {
    try {
      const [list, ings] = await Promise.all([
        getShoppingList(),
        listIngredients(""),
      ]);
      setItems(list);
      setIngredients(ings);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    fetchAll();
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    if (!ingredientId || !quantity) return;
    try {
      await addToShoppingList({
        ingredient_id: parseInt(ingredientId, 10),
        quantity: parseFloat(quantity),
      });
      setIngredientId("");
      setQuantity("");
      fetchAll();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleRemove(id) {
    await removeFromShoppingList(id);
    setItems((prev) => prev.filter((it) => it.ingredient_id !== id));
  }

  async function handleCreateOrders() {
    try {
      const res = await createOrdersFromList();
      setMsg(res.message || "Orders created from shopping list.");
      fetchAll();
    } catch (err) {
      console.error(err);
      setMsg("Failed to create orders.");
    }
  }

  return (
    <div>
      <h2>Shopping List</h2>

      <form onSubmit={handleAdd} className="form-inline">
        <select
          value={ingredientId}
          onChange={(e) => setIngredientId(e.target.value)}
        >
          <option value="">Select ingredient</option>
          {ingredients.map((ing) => (
            <option key={ing.ingredient_id} value={ing.ingredient_id}>
              {ing.name}
            </option>
          ))}
        </select>
        <input
          type="number"
          placeholder="Quantity (standard unit)"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
        />
        <button className="btn-small" type="submit">
          Add
        </button>
      </form>

      {items.length === 0 ? (
        <p>No items.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Ingredient</th>
              <th>Quantity</th>
              <th>Available products</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.ingredient_id}>
                <td>{it.ingredient_name}</td>
                <td>{it.quantity}</td>
                <td>{it.available_products}</td>
                <td>
                  <button
                    className="btn-small"
                    onClick={() => handleRemove(it.ingredient_id)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <button
        className="btn-primary"
        disabled={items.length === 0}
        onClick={handleCreateOrders}
      >
        Create orders from list
      </button>
      {msg && <p>{msg}</p>}
    </div>
  );
}
