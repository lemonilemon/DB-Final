import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getFridges, createFridge, deleteFridge } from "../../api/fridge";

export default function FridgeListPage() {
  const [fridges, setFridges] = useState([]);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");

  const load = async () => {
    const data = await getFridges();
    setFridges(data || []);
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;

    await createFridge({
      fridge_name: newName,
      description: newDescription,
    });

    setNewName("");
    setNewDescription("");
    await load();
  };

  // 🗑 DELETE FRIDGE
  const handleDeleteFridge = async (id) => {
    if (!window.confirm("Delete this fridge permanently?")) return;

    try {
      await deleteFridge(id);
      await load();
    } catch (err) {
      console.error(err);
      alert("Failed to delete fridge. Only Owners can delete.");
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Fridges</h2>

      {/* Create new fridge */}
      <form
        onSubmit={handleCreate}
        style={{ marginBottom: "20px", gap: "10px", display: "flex" }}
      >
        <input
          type="text"
          value={newName}
          placeholder="New fridge name"
          onChange={(e) => setNewName(e.target.value)}
        />
        <input
          type="text"
          value={newDescription}
          placeholder="Description (optional)"
          onChange={(e) => setNewDescription(e.target.value)}
        />
        <button type="submit">Add</button>
      </form>

      {/* List */}
      <ul>
        {fridges.map((f) => {
          const id = f.fridge_id;
          const name = f.fridge_name;
          const desc = f.description;
          const role = f.your_role || f.access_role || "Owner";

          return (
            <li key={id} style={{ marginBottom: "20px" }}>
              <Link
                to={`/fridges/${id}`}
                style={{ fontSize: "18px", fontWeight: "bold" }}
              >
                {name}
              </Link>

              {desc && (
                <p style={{ margin: "5px 0", color: "#666" }}>{desc}</p>
              )}

              <p style={{ color: "#444" }}>Role: {role}</p>

              {/* Only Owner can delete */}
              {role === "Owner" && (
                <button
                  style={{
                    marginLeft: "10px",
                    color: "red",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                  }}
                  onClick={() => handleDeleteFridge(id)}
                >
                  Delete
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
