// frontend-participant/src/app.js
import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";

const socket = io(
  process.env.REACT_APP_BACKEND || "http://localhost:5000",
  { transports: ["websocket"], path: "/socket.io" });                       

/* little marketing‑style status lines the user sees while waiting */
const WAITING_HINTS = [
  "Thinking…",
  "Consulting the form wizard…",
  "Matching your reply to the form…",
  "Retrieving relevant information…",
  "Generating a response",
  "Just one moment…",
  "Almost there…",
  "Your form wizard is working hard…",
];

export default function App() {
  /* ─────────────────────────────── state */
  const [room] = useState(
    window.location.pathname.split("/").pop()
  );                                         // /chat/<room>
  const [messages, setMessages] = useState([]);
  const [current, setCurrent] = useState("");
  const [wizardTyping, setWizardTyping] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [waitingHint, setWaitingHint] = useState(WAITING_HINTS[0]);

  /* refs */
  const bottomRef        = useRef(null);
  const listRef          = useRef(null);
  const autoScrollRef    = useRef(true);     // track if user is at bottom
  const waitingTimerRef  = useRef(null);

  /* ─────────────────────────────── socket life‑cycle */
  useEffect(() => {
    socket.emit("join", { room, type: "participant" });

    socket.on("new_message", (msg) => {
      if (msg.sender === "wizard") {
        // replace any existing streaming message
        setMessages((prev) => [
          ...prev.filter((m) => m.sender !== "wizard_streaming"),
          msg,
        ]);
        setWizardTyping(false);
        stopWaitingAnimation();
      }
    });

    socket.on("stream_chunk", ({ word, is_last }) => {
      setWizardTyping(true);
      stopWaitingAnimation();                // hide “AI is processing…”
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [room]);

  /* smart autoscroll: only scroll if the user WAS at bottom */
  useEffect(() => {
    if (autoScrollRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, wizardTyping]);

  /* detect manual scrolls */
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const handleScroll = () => {
      const nearBottom =
        el.scrollTop + el.clientHeight >= el.scrollHeight - 80;
      autoScrollRef.current = nearBottom;
    };
    el.addEventListener("scroll", handleScroll);
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  /* ─────────────────────────────── participant actions */
  const send = (e) => {
    e.preventDefault();
    if (!current.trim() || waiting) return;

    setMessages((p) => [...p, { sender: "participant", text: current }]);
    socket.emit("participant_message", { room, text: current });
    socket.emit("participant_typing", { room, text: "" });
    setCurrent("");
    startWaitingAnimation();
  };

  /* ─────────────────────────────── waiting animation helpers */
  const startWaitingAnimation = () => {
    setWaiting(true);
    setWaitingHint(WAITING_HINTS[0]);
    let i = 1;
    waitingTimerRef.current = setInterval(() => {
      setWaitingHint(WAITING_HINTS[i % WAITING_HINTS.length]);
      i += 1;
    }, 2500);
  };

  const stopWaitingAnimation = () => {
    if (waitingTimerRef.current) clearInterval(waitingTimerRef.current);
    waitingTimerRef.current = null;
    setWaiting(false);
  };

  /* ─────────────────────────────── UI */
  return (
    <div className="App">
      <div className="chat-header">
        <h2>🧙‍♂️ Form Wizard Assistant</h2>
        <p>I'm here to help you fill out forms by asking you questions and entering your responses accordingly. Let's get started!</p>
      </div>
      
      <div className="chat-window">
        <div ref={listRef} className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.sender}`}>
              {(m.sender === "wizard" || m.sender === "wizard_streaming") && (
                <span className="wizard-emoji">🧙‍♂️</span>
              )}
              <div className="message-content">
                {typeof m.text === 'object'
                  ? <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                      {JSON.stringify(m.text, null, 2)}
                    </pre>
                  : m.text}
              </div>
            </div>
          ))}

          {waiting && !wizardTyping && (
            <div className="waiting-indicator">
              <div className="spinner" />
              {waitingHint}
            </div>
          )}

          {wizardTyping && (
            <div className="message wizard typing-indicator">
              <span className="wizard-emoji">🧙‍♂️</span>
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* sticky input bar */}
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
