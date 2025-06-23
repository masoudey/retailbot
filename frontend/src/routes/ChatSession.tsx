import { useParams } from "react-router-dom";
import SessionsSidebar from "../components/SessionsSidebar";
import ChatWindow from "../components/ChatWindow";

export default function ChatSession() {
  const { sessionId } = useParams();
  if (!sessionId) return null;

  return (
    <div className="h-[calc(100vh-3.5rem)] flex overflow-hidden bg-primary">
      {/* Sidebar (left) */}
      <SessionsSidebar />

      {/* Chat area (right) – perfectly centred */}
      <div className="flex-1 flex items-center justify-center">
        <ChatWindow sessionId={sessionId} />
      </div>
    </div>
  );
}