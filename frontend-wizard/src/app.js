// frontend-wizard/src/app.js
import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";
import TemplateManager from "./TemplateManager";


// Explicitly connect to the backend server for robust development
const socket = io("http://localhost:5000");


export default function App() {
  // ───────────────────────────────────────── state
  const [room] = useState(
    window.location.pathname.split("/").pop() || null
  );
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [typing, setTyping] = useState("");

  // new ▼────────────────────────────────────
  const [phases, setPhases] = useState([]); // [{id,name,templates:[{id,text}]}]
  const [currentPhaseId, setCurrentPhaseId] = useState(null);
  const [setupMode, setSetupMode] = useState(false);
  // ▲────────────────────────────────────────

  const bottomRef = useRef(null);

  // ───────────────────────────────────────── room bootstrap
  useEffect(() => {
    if (room) return;
    const API_ORIGIN = process.env.REACT_APP_API_ORIGIN || "http://localhost:5000";
    fetch(`${API_ORIGIN}/api/new_room`, { method: "POST" })
      .then((r) => r.json())
      .then(({ room: id }) => {
        window.location.pathname = `/wizard/${id}`; // hard reload
      });
  }, [room]);

  // ───────────────────────────────────────── socket life‑cycle
  useEffect(() => {
    if (!room) return;
    socket.emit("join", { room, type: "wizard" });

    socket.on("new_message", (m) => setMessages((p) => [...p, m]));
    socket.on("participant_is_typing", ({ text }) => setTyping(text));
    socket.on("templates", (dict) => {
      // Handle the new nested template structure from backend
      const allTemplates = [];
      
      // Add pinned templates
      if (Array.isArray(dict.pinned)) {
        dict.pinned.forEach((text, i) => {
          allTemplates.push({
            id: `pinned-${i}`,
            text: text
          });
        });
      }
      
      // Add contextual templates with field prefixes
      if (dict.contextual && typeof dict.contextual === 'object') {
        Object.entries(dict.contextual).forEach(([field, templates]) => {
          if (Array.isArray(templates)) {
            templates.forEach((text, i) => {
              allTemplates.push({
                id: `${field}-${i}`,
                text: text
              });
            });
          }
        });
      }
      
      setPhases([
        {
          id: "general",
          name: "General",
          templates: allTemplates,
        },
      ]);
      setCurrentPhaseId("general");
    });

    return () => socket.emit("leave", { room });
  }, [room]);

  // ───────────────────────────────────────── scroll on new msg
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ───────────────────────────────────────── helpers
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

  // ───────────────────────────────────────── phase helpers
  const addPhase = () => {
    const name = prompt("New phase name:");
    if (!name) return;
    const id = Date.now().toString();
    setPhases([...phases, { id, name, templates: [] }]);
    setCurrentPhaseId(id);
  };

  const renamePhase = (id) => {
    const name = prompt("Rename phase:");
    if (!name) return;
    setPhases(phases.map((p) => (p.id === id ? { ...p, name } : p)));
  };

  const removePhase = (id) => {
    if (phases.length === 1) return;
    if (!window.confirm("Delete this phase (and its templates)?")) return;
    const next = phases.filter((p) => p.id !== id);
    setPhases(next);
    setCurrentPhaseId(next[0].id);
  };

  // ───────────────────────────────────────── UI
  if (!room) return <p>Creating room…</p>;

  return (
    <div className="App">
      <div className="wizard-panel">
        {/* ───────────── conversation ───────────── */}
        <div className="chat-area">
          <h2>Conversation</h2>
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.sender}`}>
                <div className="sender-label">{m.sender}</div>
                {typeof m.text === 'object'
                  ? <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                      {JSON.stringify(m.text, null, 2)}
                    </pre>
                  : m.text}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="live-typing">
            <p>Participant is typing:</p>
            <div className="typing-preview">{typing || "…"}</div>
          </div>
        </div>

        {/* ───────────── control column ───────────── */}
        <div className="control-area">
          <h2>Wizard Controls</h2>

          <button onClick={exportLog} style={{ marginBottom: "15px" }}>
            ⬇ Export conversation as JSON
          </button>

          <p>
            Share with participant:&nbsp;
            <code>{`${process.env.REACT_APP_PARTICIPANT_ORIGIN || "http://localhost:3000"}/chat/${room}`}</code>&nbsp;
            <button
              onClick={() =>
                navigator.clipboard.writeText(
                  `${process.env.REACT_APP_PARTICIPANT_ORIGIN || "http://localhost:3000"}/chat/${room}`
                )
              }
            >
              Copy
            </button>
          </p>

          {/* ───────────── setup toggle ───────────── */}
          <button
            className="setup-toggle"
            onClick={() => setSetupMode((p) => !p)}
          >
            {setupMode ? "✅ Exit Setup Mode" : "🛠 Enter Setup Mode"}
          </button>

          {/* ───────────── phase selector ───────────── */}
          <div className="phase-selector">
            {phases.map((p) => (
              <div
                key={p.id}
                className={`phase-pill ${
                  p.id === currentPhaseId ? "active" : ""
                }`}
              >
                <button
                  onClick={() => setCurrentPhaseId(p.id)}
                  title="Select phase"
                >
                  {p.name}
                </button>
                {setupMode && (
                  <>
                    <button
                      className="tiny-btn"
                      title="Rename"
                      onClick={() => renamePhase(p.id)}
                    >
                      ✏
                    </button>
                    <button
                      className="tiny-btn"
                      title="Delete phase"
                      onClick={() => removePhase(p.id)}
                      disabled={phases.length === 1}
                    >
                      🗑
                    </button>
                  </>
                )}
              </div>
            ))}
            {setupMode && (
              <button className="tiny-btn" onClick={addPhase} title="Add phase">
                ＋
              </button>
            )}
          </div>

          {/* ───────────── templates ───────────── */}
          <TemplateManager
            phases={phases}
            setPhases={setPhases}
            currentPhaseId={currentPhaseId}
            setupMode={setupMode}
            onSend={send}
          />

          {/* ───────────── custom response ───────────── */}
          {!setupMode && (
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
          )}
        </div>
      </div>
    </div>
  );
}