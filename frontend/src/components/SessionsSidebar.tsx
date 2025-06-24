import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

interface Session {
  id: string;
  createdAt: number;
}

export default function SessionsSidebar() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const { pathname } = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const stored = localStorage.getItem("sessions");
    if (stored) setSessions(JSON.parse(stored));
  }, []);

  const createSession = () => {
    const newSession: Session = { id: uuidv4(), createdAt: Date.now() };
    const next = [newSession, ...sessions];
    localStorage.setItem("sessions", JSON.stringify(next));
    setSessions(next);
    navigate(`/chat/${newSession.id}`);
  };

  const activeId = pathname.startsWith("/chat/")
    ? pathname.split("/").pop()
    : null;

  return (
    <aside className="w-72 shrink-0 sticky top-0 h-screen flex flex-col bg-secondary/80 backdrop-blur-md p-4 space-y-4 overflow-y-auto">
      <h2 className="text-lg font-medium text-text">Conversations</h2>

      <ul className="space-y-2 list-none">
        {sessions.map((s) => (
          <li key={s.id}>
            <Link
              to={`/chat/${s.id}`}
              className={`block px-3 py-2 rounded-lg text-text hover:bg-primary/50 transition ${
                s.id === activeId ? "bg-accent text-white" : ""
              }`}
            >
              {new Date(s.createdAt).toLocaleTimeString()}
            </Link>
          </li>
        ))}
      </ul>

      <button
        onClick={createSession}
        className="mt-auto bg-accent text-white py-2 rounded-full hover:bg-accent/80 transition"
      >
        + New Chat
      </button>
    </aside>
  );
}