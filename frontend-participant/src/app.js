// frontend-participant/src/app.js
import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";

const socket = io();                      // <── SAME ORIGIN WS

export default function App() {
  const [room] = useState(
    window.location.pathname.split("/").pop()
  );                                      // /chat/<room>
  const [messages, setMessages] = useState([]);
  const [current, setCurrent] = useState("");
  const [wizardTyping, setWizardTyping] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const bottomRef = useRef(null);

  /* socket life‑cycle */
  useEffect(() => {
    socket.emit("join", { room, type: "participant" });

    socket.on("new_message", (msg) => {
      if (msg.sender === "wizard") {
        setMessages((p) => [
          ...p.filter((m) => m.sender !== "wizard_streaming"),
          msg,
        ]);
        setWizardTyping(false);
        setWaiting(false);
      }
    });

    socket.on("stream_chunk", ({ word, is_last }) => {
      setWizardTyping(true);
      setMessages((prev) => {
        const last = prev.at(-1);
        if (last?.sender === "wizard_streaming") {
          last.text += ` ${word}`;
          return [...prev.slice(0, -1), last];
        }
        return [...prev, { sender: "wizard_streaming", text: word }];
      });
      if (is_last) setWizardTyping(false);
    });

    return () => socket.emit("leave", { room });
  }, [room]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, wizardTyping]);

  /* participant actions */
  const send = (e) => {
    e.preventDefault();
    if (!current.trim() || waiting) return;
    setMessages((p) => [...p, { sender: "participant", text: current }]);
    socket.emit("participant_message", { room, text: current });
    socket.emit("participant_typing", { room, text: "" });
    setCurrent("");
    setWaiting(true);
  };

  return (
    <div className="App">
      <div className="chat-window">
        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.sender}`}>{m.text}</div>
          ))}
          {wizardTyping && (
            <div className="message wizard typing-indicator">
              <span /><span /><span />
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form className="message-form" onSubmit={send}>
          <input
            value={current}
            onChange={(e) => {
              setCurrent(e.target.value);
              socket.emit("participant_typing", {
                room,
                text: e.target.value,
              });
            }}
            disabled={waiting}
            placeholder={
              waiting ? "Waiting for reply…" : "Type your message…"
            }
          />
          <button disabled={waiting}>Send</button>
        </form>
      </div>
    </div>
  );
}
