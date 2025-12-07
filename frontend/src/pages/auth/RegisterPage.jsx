// src/pages/auth/RegisterPage.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [okMsg, setOkMsg] = useState("");

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setOkMsg("");
    try {
      await register(form);
      setOkMsg("Register success! You can login now.");
      setTimeout(() => navigate("/login"), 800);
    } catch (err) {
      console.error(err);
      setError("Register failed.");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Register</h1>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Username
            <input
              name="username"
              value={form.username}
              onChange={handleChange}
            />
          </label>

          <label>
            Email
            <input
              name="email"
              value={form.email}
              onChange={handleChange}
            />
          </label>

          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
            />
          </label>

          {error && <p className="error-text">{error}</p>}
          {okMsg && <p className="ok-text">{okMsg}</p>}

          <button type="submit" className="btn-primary">
            Register
          </button>
        </form>

        <p className="auth-switch">
          Already have account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}
