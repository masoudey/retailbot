import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { v4 as uuid } from "uuid";

interface Session {
  id: string;
  createdAt: number;
}

export default function SessionsList() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const stored = localStorage.getItem("sessions");
    if (stored) setSessions(JSON.parse(stored));
  }, []);

  const createSession = () => {
    const newSession: Session = { id: uuid(), createdAt: Date.now() };
    const next = [newSession, ...sessions];
    localStorage.setItem("sessions", JSON.stringify(next));
    navigate(`/chat/${newSession.id}`);
  };

  return (
    <div className="max-w-7xl mx-auto p-8">
      <h1 className="text-3xl font-semibold mb-6">Your Conversations</h1>

      {sessions.length === 0 && (
        <p className="text-gray-600 mb-4">
          You haven't started a conversation yet.
        </p>
      )}

      <ul className="space-y-3">
        {sessions.map((s) => (
          <li key={s.id}>
            <Link
              to={`/chat/${s.id}`}
              className="block rounded-xl border border-gray-300 hover:border-gray-500 transition px-4 py-3"
            >
              Chat started {new Date(s.createdAt).toLocaleString()}
            </Link>
          </li>
        ))}
      </ul>

      <button
        onClick={createSession}
        className="mt-8 bg-accent text-white rounded-full px-6 py-3 font-medium shadow hover:shadow-lg transition"
      >
        Start New Chat
      </button>
    </div>
  );
}