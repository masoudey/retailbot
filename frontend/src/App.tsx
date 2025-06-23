import { Routes, Route, Navigate } from "react-router-dom";
import SessionsList from "./routes/SessionsList";
import ChatSession from "./routes/ChatSession";
import NavBar from "./components/NavBar";

export default function App() {
    return (
      <div className="flex flex-col h-full bg-primary">
      <NavBar />
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<SessionsList />} />
          <Route path="/chat/:sessionId" element={<ChatSession />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}