import type { Message } from "../types";

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.sender === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-xs rounded-xl px-4 py-2 leading-relaxed ${
          isUser
            ? "bg-accent text-white rounded-br-none"
            : "bg-secondary/50 text-text rounded-bl-none"
        }`}
      >
        {message.text}
      </div>
    </div>
  );
}