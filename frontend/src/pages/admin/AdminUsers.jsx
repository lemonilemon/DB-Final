// src/pages/admin/AdminUsers.jsx
import React, { useEffect, useState } from "react";
import {
  getAllUsers,
  updateUserStatus,
  setUserRole,
  revokeRole,
} from "../../api/admin";

export default function AdminUsers() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    const data = await getAllUsers();
    setUsers(data);
  };

  const toggleRole = async (u) => {
    if (u.role === "Admin") {
      await revokeRole(u.user_id, "Admin");
    } else {
      await setUserRole(u.user_id, "Admin");
    }
    loadUsers();
  };

  const toggleStatus = async (u) => {
    const newStatus = u.status === "Active" ? "Disabled" : "Active";
    await updateUserStatus(u.user_id, newStatus);
    loadUsers();
  };

  return (
    <div>
      <h2>Admin - User Management</h2>

      {users.map((u) => (
        <div key={u.user_id} className="card">
          <p><b>Name:</b> {u.user_name}</p>
          <p><b>Email:</b> {u.email}</p>
          <p><b>Status:</b> {u.status}</p>
          <p><b>Role:</b> {u.role}</p>

          <button onClick={() => toggleStatus(u)}>
            {u.status === "Active" ? "Disable" : "Activate"}
          </button>

          <button onClick={() => toggleRole(u)}>
            {u.role === "Admin" ? "Revoke Admin" : "Make Admin"}
          </button>

          <hr />
        </div>
      ))}
    </div>
  );
}
