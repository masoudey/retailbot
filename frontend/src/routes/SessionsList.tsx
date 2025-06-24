import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

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
    const newSession: Session = { id: uuidv4(), createdAt: Date.now() };
    const next = [newSession, ...sessions];
    localStorage.setItem("sessions", JSON.stringify(next));
    navigate(`/chat/${newSession.id}`);
  };

  return (
    <div className="flex-1 flex items-center justify-center bg-primary">
      <button
        onClick={createSession}
        className="bg-accent text-white px-6 py-3 rounded-full shadow-lg hover:bg-accent/80 transition"
      >
        + Start a Chat
      </button>
    </div>
  );
}