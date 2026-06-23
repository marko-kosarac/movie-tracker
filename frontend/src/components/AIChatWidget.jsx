import "./AIChatWidget.css";
import { useEffect, useRef, useState } from "react";

function AIChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const chatBodyRef = useRef(null);
  const abortControllerRef = useRef(null);

  const scrollToBottom = () => {
    if (!chatBodyRef.current) return;
    chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const closeChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setIsOpen(false);
    setMessage("");
    setMessages([]);
    setLoading(false);
  };

  const sendMessage = async () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || loading) return;

    const userMessage = {
      role: "user",
      content: trimmedMessage,
    };

    const updatedMessages = [...messages, userMessage];

    setMessages([
      ...updatedMessages,
      {
        role: "assistant",
        content: "",
      },
    ]);

    setMessage("");
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch("http://127.0.0.1:8000/ai/chat-stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: updatedMessages,
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        throw new Error("AI request failed.");
      }

      if (!res.body) {
        throw new Error("Streaming response body is empty.");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let assistantText = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        assistantText += chunk;

        setMessages((currentMessages) => {
          const newMessages = [...currentMessages];
          const lastIndex = newMessages.length - 1;

          if (lastIndex >= 0 && newMessages[lastIndex].role === "assistant") {
            newMessages[lastIndex] = {
              ...newMessages[lastIndex],
              content: assistantText,
            };
          }

          return newMessages;
        });
      }
    } catch (err) {
      if (err.name === "AbortError") return;

      console.error(err);

      setMessages([
        ...updatedMessages,
        {
          role: "assistant",
          content: "Došlo je do greške pri komunikaciji sa AI asistentom.",
        },
      ]);
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <>
      {!isOpen && (
        <button className="ai-chat-button" onClick={() => setIsOpen(true)}>
          <span className="ai-chat-dot"></span>
          AI Assistant
        </button>
      )}

      {isOpen && (
        <div className="ai-chat-window">
          <div className="ai-chat-header">
            <div>
              <h3>Movie Tracker AI</h3>
              <p>Movie & TV assistant</p>
            </div>

            <button onClick={closeChat} className="ai-chat-close">
              ✕
            </button>
          </div>

          <div className="ai-chat-body" ref={chatBodyRef}>
            {messages.length === 0 ? (
              <div className="ai-chat-welcome">
                <h4>Kako mogu pomoći?</h4>
                <p>Pitaj me za preporuku filma ili serije.</p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  className={
                    msg.role === "user"
                      ? "ai-message user-message"
                      : "ai-message assistant-message"
                  }
                >
                  {msg.content || "AI razmišlja..."}
                </div>
              ))
            )}
          </div>

          <div className="ai-chat-footer">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Npr. Preporuči mi dobar triler..."
              rows={2}
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />

            <button onClick={sendMessage} disabled={loading || !message.trim()}>
              {loading ? "..." : "➤"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default AIChatWidget;