import type { Message } from "../types";

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.sender === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-xs md:max-w-md rounded-2xl px-4 py-3 shadow transition whitespace-pre-wrap ${
          isUser
            ? "bg-accent text-white rounded-br-none"
            : "bg-gray-200 text-gray-900 rounded-bl-none"
        }`}
      >
        {message.text}
      </div>
    </div>
  );
}