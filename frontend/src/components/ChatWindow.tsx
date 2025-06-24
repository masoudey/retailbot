import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import type { Message } from "../types";
import { sendMessageToRasa } from "../api/rasaClient";
import MessageBubble from "./MessageBubble";

interface Props {
  sessionId: string;
}

export default function ChatWindow({ sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem(`chat-${sessionId}`);
    setMessages(stored ? JSON.parse(stored) : []);
  }, [sessionId]);

  useEffect(() => {
    localStorage.setItem(`chat-${sessionId}`, JSON.stringify(messages));
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sessionId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages((prev) => [...prev, { text: input, sender: "user" }]);
    setInput("");

    try {
      const botReplies = await sendMessageToRasa(input, sessionId);
      setMessages((prev) => [...prev, ...botReplies]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { text: "Error contacting server.", sender: "bot" }
      ]);
    }
  };

  return (
    <div className="flex flex-col flex-1 bg-secondary/70 rounded-2xl shadow-xl overflow-hidden backdrop-blur-sm mx-4">
      {/* Scrollable message list */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        <div ref={endRef} />
      </div>

      {/* Input bar */}
      <form
        onSubmit={handleSubmit}
        className="bg-secondary/50 p-4 flex gap-3 mt-auto"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          className="flex-1 rounded-full px-4 py-2 bg-primary/30 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          type="submit"
          className="bg-accent text-white px-4 py-2 rounded-full hover:bg-accent/80 transition"
        >
          Send
        </button>
      </form>
    </div>
  );
}