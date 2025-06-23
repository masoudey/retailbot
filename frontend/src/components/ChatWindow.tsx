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

  /* ─────────────────────────────────────────────
     Load chat history (or clear) when sessionId
     changes — ensures “New chat” starts blank
  ────────────────────────────────────────────── */
  useEffect(() => {
    const stored = localStorage.getItem(`chat-${sessionId}`);
    setMessages(stored ? JSON.parse(stored) : []);
  }, [sessionId]);

  /* persist + auto-scroll */
  useEffect(() => {
    localStorage.setItem(`chat-${sessionId}`, JSON.stringify(messages));
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sessionId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = { text: input, sender: "user" };
    setMessages((prev) => [...prev, userMsg]);
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
    <div className="flex flex-col h-full w-full max-w-lg bg-white/60 rounded-3xl shadow-xl overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m, idx) => (
          <MessageBubble key={idx} message={m} />
        ))}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 p-4 flex gap-4 bg-white/80 backdrop-blur-sm"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message…"
          className="flex-1 rounded-full px-3 py-2 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          type="submit"
          className="bg-accent text-white rounded-full px-6 py-3 font-medium shadow hover:shadow-lg transition"
        >
          Send
        </button>
      </form>
    </div>
  );
}