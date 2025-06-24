import { useParams } from "react-router-dom";
import SessionsSidebar from "../components/SessionsSidebar";
import ChatWindow from "../components/ChatWindow";

export default function ChatSession() {
  const { sessionId } = useParams();
  if (!sessionId) return null;

  return (
    /* Fill full viewport minus NavBar (~3.5rem) */
    <div className="flex h-[calc(100vh-3.5rem)]">
      <SessionsSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* ChatWindow will handle its own scrolling */}
        <ChatWindow sessionId={sessionId} />
      </div>
    </div>
  );
}