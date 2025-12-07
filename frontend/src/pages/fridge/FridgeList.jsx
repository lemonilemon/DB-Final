import { useEffect, useState } from "react";
import { listFridges, createFridge } from "../../api/fridge";
import { Link } from "react-router-dom";

export default function FridgeList() {
  const [fridges, setFridges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  async function fetchFridges() {
    setLoading(true);
    try {
      const data = await listFridges();
      setFridges(data);
    } catch (err) {
      console.error("listFridges failed:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchFridges();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!name) return;
    try {
      await createFridge({ fridge_name: name, description: desc || null });
      setName("");
      setDesc("");
      fetchFridges();
    } catch (err) {
      console.error("createFridge failed:", err);
    }
  }

  return (
    <div>
      <h2>Your Fridges</h2>

      <form onSubmit={handleCreate} className="form-inline">
        <input
          placeholder="Fridge name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          placeholder="Description (optional)"
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
        />
        <button className="btn-small" type="submit">
          Add
        </button>
      </form>

      {loading ? (
        <p>Loading...</p>
      ) : fridges.length === 0 ? (
        <p>No fridges.</p>
      ) : (
        <ul className="list">
          {fridges.map((f) => (
            <li key={f.fridge_id} className="list-item">
              <div>
                <strong>{f.fridge_name}</strong>
                {f.description && <span> — {f.description}</span>}
                <span> · You: {f.your_role}</span>
              </div>
              <Link className="btn-small" to={`/fridges/${f.fridge_id}`}>
                View
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
