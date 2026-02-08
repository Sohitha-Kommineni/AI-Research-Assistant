import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../lib/api.js";
import { clearToken } from "../lib/auth.js";

export default function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  const loadProjects = async () => {
    const data = await apiFetch("/projects");
    setProjects(data);
  };

  useEffect(() => {
    loadProjects().catch((err) => setError(err.message));
  }, []);

  const onCreate = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await apiFetch("/projects", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      });
      setName("");
      setDescription("");
      await loadProjects();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <h1>Research Projects</h1>
          <p className="muted">Manage sources and chat history per workspace.</p>
        </div>
        <button
          className="secondary"
          onClick={() => {
            clearToken();
            navigate("/login");
          }}
        >
          Sign out
        </button>
      </header>
      <section className="card">
        <h2>Create a new project</h2>
        <form className="inline-form" onSubmit={onCreate}>
          <input
            placeholder="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            placeholder="Short description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button className="primary" type="submit">
            Create
          </button>
        </form>
        {error && <div className="error">{error}</div>}
      </section>
      <section className="grid">
        {projects.map((project) => (
          <button
            key={project.id}
            className="project-card"
            onClick={() => navigate(`/projects/${project.id}`)}
          >
            <h3>{project.name}</h3>
            <p className="muted">{project.description || "No description yet."}</p>
            <div className="project-meta">
              <span>{project.document_count} documents</span>
              <span>
                Last active{" "}
                {new Date(project.last_activity_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })}
              </span>
            </div>
          </button>
        ))}
      </section>
    </div>
  );
}
