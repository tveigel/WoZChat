// frontend-participant/src/app.js
import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";

// Simple markdown-style formatter for bot messages
const formatMessage = (text) => {
  if (typeof text !== 'string') return text;
  
  // Split by lines to handle different formatting per line
  const lines = text.split('\n');
  const formattedLines = lines.map((line, index) => {
    let formattedLine = line;
    
    // Handle bold text **text**
    formattedLine = formattedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text *text* (but not when surrounded by **)
    formattedLine = formattedLine.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');
    
    // Handle bullet points • or - at start of line (with potential whitespace)
    if (/^\s*[•\-]\s/.test(line)) {
      const cleanLine = formattedLine.replace(/^\s*[•\-]\s*/, '');
      return (
        <div key={index} className="bullet-point">
          <span dangerouslySetInnerHTML={{ __html: cleanLine }} />
        </div>
      );
    }
    
    // Handle error messages with ❌
    if (line.includes('❌')) {
      return (
        <div key={index} className="error-message">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    }
    
    // Handle progress indicators
    if (line.includes('Progress:')) {
      return (
        <div key={index} className="progress-indicator">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    }
    
    // Empty lines for spacing
    if (line.trim() === '') {
      return <div key={index} className="empty-line">&nbsp;</div>;
    }
    
    // Regular line with potential formatting
    if (formattedLine !== line) {
      return (
        <div key={index}>
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    }
    
    return <div key={index}>{line}</div>;
  });
  
  return <div className="formatted-message">{formattedLines}</div>;
};

// Environment-aware socket connection
const socket = io(
  process.env.NODE_ENV === 'development' 
    ? "http://localhost:5000" 
    : window.location.origin,
  {
    transports: ["websocket"],
    path: "/socket.io"
  }
);                       

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

    socket.on("message_history", ({ messages }) => {
      setMessages(messages || []);
    });

    socket.on("new_message", (msg) => {
      if (msg.sender === "wizard") {
        // replace any existing streaming message
        setMessages((prev) => [
          ...prev.filter((m) => m.sender !== "wizard_streaming"),
          msg,
        ]);
        setWizardTyping(false);
        stopWaitingAnimation();
      } else if (msg.sender === "bot") {
        // Handle bot messages - add them directly to the message list
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
    }, 2700); // change hint every 3 seconds
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
              {(m.sender === "wizard" || m.sender === "wizard_streaming" || m.sender === "bot") && (
                <span className="wizard-emoji">
                  {m.sender === "bot" ? "🤖" : "🧙‍♂️"}
                </span>
              )}
              <div className="message-content">
                {typeof m.text === 'object'
                  ? <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                      {JSON.stringify(m.text, null, 2)}
                    </pre>
                  : (m.sender === "bot" || m.sender === "wizard" || m.sender === "wizard_streaming") 
                    ? formatMessage(m.text)
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
