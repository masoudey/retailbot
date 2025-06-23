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

  const activeId =
    pathname.startsWith("/chat/") ? pathname.split("/").pop() : null;

  return (
    <aside className="w-64 shrink-0 h-full flex flex-col bg-white/80 backdrop-blur-md">
      <header className="px-4 py-3 font-semibold tracking-tight">Sessions</header>

      <nav className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <p className="px-4 py-6 text-gray-600 text-sm">
            No conversations yet.
          </p>
        ) : (
          <ul className="space-y-1 p-2 list-none">
            {sessions.map((s) => (
              <li key={s.id}>
                <Link
                  to={`/chat/${s.id}`}
                  className={`block px-3 py-2 rounded-md text-sm ${
                    s.id === activeId
                      ? "bg-accent text-white"
                      : "hover:bg-gray-100"
                  }`}
                >
                  {new Date(s.createdAt).toLocaleString()}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <button
        onClick={createSession}
        className="m-4 bg-accent text-white rounded-full px-4 py-2 text-sm font-medium shadow hover:shadow-lg transition"
      >
        + New chat
      </button>
    </aside>
  );
}