import axios from "axios";
import type { Message } from "../types";

// Default Rasa REST webhook – adjust if your server differs
const rasaURL = "http://localhost:5005/webhooks/rest/webhook";

export async function sendMessageToRasa(
  text: string,
  sender: string
): Promise<Message[]> {
  const { data } = await axios.post<{ recipient_id: string; text: string }[]>(
    rasaURL,
    {
      sender,
      message: text
    }
  );
  return data.map((d) => ({ text: d.text, sender: "bot" }));
}