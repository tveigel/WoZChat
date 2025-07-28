/* frontend-wizard/src/app.js */
import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";

/* ───────── configuration ───────── */
const WS_ORIGIN  = process.env.REACT_APP_WS_ORIGIN  || "";
const API_ORIGIN = process.env.REACT_APP_API_ORIGIN || "";
const FIXED_ROOM = process.env.REACT_APP_DEV_ROOM   || null;
const socket = io(WS_ORIGIN);

/* ───────── component ───────── */
export default function App() {
  const [room, setRoom] = useState(
    FIXED_ROOM || window.location.pathname.split("/").pop() || null
  );
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [typing, setTyping] = useState("");
  const [templates, setTemplates] = useState({});
  const bottomRef = useRef(null);

  /* create a room once – skipped if FIXED_ROOM is present */
  useEffect(() => {
    if (room || FIXED_ROOM) return;
    fetch(`${API_ORIGIN}/api/new_room`, { method: "POST" })
      .then((r) => r.json())
      .then(({ room: id }) =>
        (window.location.pathname = `/wizard/${id}`)
      );
  }, [room]);

  /* join + handlers */
  useEffect(() => {
    if (!room) return;
    socket.emit("join", { room, type: "wizard" });

    const onNewMessage = (m) => setMessages((p) => [...p, m]);
    const onTyping = ({ text }) => setTyping(text);
    const onTemplates = (t) => setTemplates(t);

    socket.on("new_message", onNewMessage);
    socket.on("participant_is_typing", onTyping);
    socket.on("templates", onTemplates);

    return () => {
      socket.emit("leave", { room });
      socket.off("new_message", onNewMessage);
      socket.off("participant_is_typing", onTyping);
      socket.off("templates", onTemplates);
    };
  }, [room]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* helpers */
  const send = (txt) => {
    if (!txt.trim()) return;
    socket.emit("wizard_response", { room, text: txt });
    setDraft("");
  };

  const exportLog = () => {
    const blob = new Blob([JSON.stringify(messages, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `chat_${room}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (!room) return <p>Creating room…</p>;

  /* ui */
  return (
    <div className="App">
      <div className="wizard-panel">
        <div className="chat-area">
          <h2>Conversation</h2>
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.sender}`}>
                <div className="sender-label">{m.sender}</div>
                {m.text}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
          <div className="live-typing">
            <p>Participant is typing:</p>
            <div className="typing-preview">{typing || "…"}</div>
          </div>
        </div>

        <div className="control-area">
          <h2>Wizard Controls</h2>

          <button onClick={exportLog} style={{ marginBottom: "15px" }}>
            ⬇ Export conversation as JSON
          </button>

          <p>
            Share with participant:&nbsp;
            <code>{`${window.location.origin}/chat/${room}`}</code>&nbsp;
            <button
              onClick={() =>
                navigator.clipboard.writeText(
                  `${window.location.origin}/chat/${room}`
                )
              }
            >
              Copy
            </button>
          </p>

          <div className="templates">
            <h3>Response Templates</h3>
            {Object.entries(templates).map(([k, v]) => (
              <button key={k} onClick={() => send(v)}>
                {v}
              </button>
            ))}
          </div>

          <div className="custom-response">
            <h3>Custom Response</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(draft);
              }}
            >
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Type a custom response…"
              />
              <button type="submit">Send Response</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
