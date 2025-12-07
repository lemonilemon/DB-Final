import { useAuth } from "../../context/AuthContext";
import { useEffect, useState } from "react";
import { listFridges } from "../../api/fridge";
import { listMealPlans } from "../../api/mealplan";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const { user } = useAuth();
  const [fridges, setFridges] = useState([]);
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const [f, p] = await Promise.all([
          listFridges(),
          listMealPlans({}),
        ]);
        setFridges(f);
        setPlans(p.slice(0, 5));
      } catch (err) {
        console.error(err);
      }
    })();
  }, []);

  return (
    <div>
      <h2>Hi, {user?.user_name}</h2>
      <p>Welcome back to your smart fridge system.</p>

      <section className="section">
        <h3>Your fridges</h3>
        {fridges.length === 0 ? (
          <p>No fridges yet. Go create one!</p>
        ) : (
          <ul className="list">
            {fridges.map((f) => (
              <li key={f.fridge_id} className="list-item">
                <div>
                  <strong>{f.fridge_name}</strong>
                  <span> · role: {f.your_role}</span>
                </div>
                <Link className="btn-small" to={`/fridges/${f.fridge_id}`}>
                  Open
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="section">
        <h3>Upcoming meals</h3>
        {plans.length === 0 ? (
          <p>No meal plans yet.</p>
        ) : (
          <ul className="list">
            {plans.map((p) => (
              <li key={p.plan_id} className="list-item">
                <div>
                  <strong>{p.scheduled_date}</strong> — {p.recipe_name}
                </div>
              </li>
            ))}
          </ul>
        )}
        <Link to="/meal-plans" className="btn-secondary">
          View all meal plans
        </Link>
      </section>
    </div>
  );
}
