// frontend-wizard/src/components/ChatArea.js
import React, { useRef, useEffect } from "react";

function ChatArea({ messages, typing, onExportLog, room }) {
  const bottomRef = useRef(null);

  /* ───────── autoscroll */
  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), [messages]);

  const exportLog = () => {
    const blob = new Blob([JSON.stringify(messages, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `chat_${room}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="chat-area" style={{ overflowY: "auto" }}>
      <div className="header-row">
        <h2>Conversation</h2>
        <button onClick={exportLog} className="header-btn">
          ⬇ Export JSON
        </button>
      </div>
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.sender}`}>
            <div className="sender-label">{m.sender}</div>
            {typeof m.text === "object" ? (
              <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
                {JSON.stringify(m.text, null, 2)}
              </pre>
            ) : (
              m.text
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="live-typing">
        <p>Participant is typing:</p>
        <div className="typing-preview">{typing || "…"}</div>
      </div>
    </div>
  );
}

export default ChatArea;