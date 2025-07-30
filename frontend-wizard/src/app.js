// frontend-wizard/src/app.js
import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";
import TemplateManager from "./TemplateManager";

// ─────────────────────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────────────────────
const API_ORIGIN =
  process.env.REACT_APP_API_ORIGIN || "http://localhost:5000";
const PARTICIPANT_ORIGIN =
  process.env.REACT_APP_PARTICIPANT_ORIGIN || "http://localhost:3000";

const socket = io("http://localhost:5000");          // explicit host for dev

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  /* ─────────── state */
  const [room]           = useState(window.location.pathname.split("/").pop() || null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft]       = useState("");
  const [typing, setTyping]     = useState("");

  const [phases, setPhases]     = useState([]);      // [{id,name,templates:[{id,text}]}]
  const [currentPhaseId, setCurrentPhaseId] = useState(null);
  const [setupMode, setSetupMode]           = useState(false);

  const bottomRef      = useRef(null);
  const initialLoadRef = useRef(true);               // guard to avoid persisting on first load
  const prevDictRef    = useRef({});                 // previous template snapshot for diffing

  /* ───────────────────────── room bootstrap */
  useEffect(() => {
    if (room) return;
    fetch(`${API_ORIGIN}/api/new_room`, { method: "POST" })
      .then((r) => r.json())
      .then(({ room: id }) => {
        window.location.pathname = `/wizard/${id}`;  // hard reload
      });
  }, [room]);

  /* ───────────────────────── socket life‑cycle */
  useEffect(() => {
    if (!room) return;
    socket.emit("join", { room, type: "wizard" });

    const handleNewMsg  = (m)        => setMessages((p) => [...p, m]);
    const handleTyping  = ({ text }) => setTyping(text);
    const handleTplPush = (dict)     => {
      /* Convert {Category: {key: text}} → phases[] */
      const newPhases = Object.entries(dict).map(([cat, items]) => ({
        id:   cat,
        name: cat,
        templates: Object.entries(items).map(([key, text]) => ({
          id: key,
          text,
        })),
      }));
      setPhases(newPhases);
      setCurrentPhaseId((id) => id || (newPhases[0]?.id ?? null));

      // store snapshot for later diffing
      prevDictRef.current = dict;
    };

    socket.on("new_message", handleNewMsg);
    socket.on("participant_is_typing", handleTyping);
    socket.on("templates", handleTplPush);

    return () => {
      socket.off("new_message", handleNewMsg);
      socket.off("participant_is_typing", handleTyping);
      socket.off("templates", handleTplPush);
      socket.emit("leave", { room });
    };
  }, [room]);

  /* ───────────────────────── autoscroll */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ───────────────────────── helpers */
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

  /* ───────────────────────── phase helpers (UI only, unchanged) */
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

  /* ───────────────────────── PERSISTENCE LOGIC */
  // 1. helper to turn phases[] → {cat: {key: text}}
  const phasesToDict = (arr) => {
    const out = {};
    arr.forEach(({ name, templates }) => {
      const cat = name || "General";
      out[cat] = {};
      templates.forEach(({ id, text }) => {
        out[cat][id] = text;
      });
    });
    return out;
  };

  // 2. whenever phases change **after** initial load, diff & sync
  useEffect(() => {
    if (initialLoadRef.current) {
      // first render after socket push → don't persist
      initialLoadRef.current = false;
      return;
    }

    const next = phasesToDict(phases);
    const prev = prevDictRef.current;

    // --- additions & updates
    for (const [cat, items] of Object.entries(next)) {
      for (const [key, text] of Object.entries(items)) {
        if (!prev[cat] || prev[cat][key] !== text) {
          fetch(`${API_ORIGIN}/api/templates/item`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: cat, key, value: text }),
          }).catch(console.error);
        }
      }
    }
    // --- deletions
    for (const [cat, items] of Object.entries(prev)) {
      for (const key of Object.keys(items)) {
        if (!next[cat] || !(key in next[cat])) {
          fetch(
            `${API_ORIGIN}/api/templates/${encodeURIComponent(
              cat
            )}/${encodeURIComponent(key)}`,
            { method: "DELETE" }
          ).catch(console.error);
        }
      }
    }

    prevDictRef.current = next; // update snapshot
  }, [phases]);

  /* ───────────────────────── UI */
  if (!room) return <p>Creating room…</p>;

  return (
    <div className="App">
      <div className="wizard-panel">
        {/* ───── conversation ───── */}
        <div className="chat-area">
          <h2>Conversation</h2>
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

        {/* ───── control column ───── */}
        <div className="control-area">
          <h2>Wizard Controls</h2>

          <button onClick={exportLog} style={{ marginBottom: "15px" }}>
            ⬇ Export conversation as JSON
          </button>

          <p>
            Share with participant:&nbsp;
            <code>{`${PARTICIPANT_ORIGIN}/chat/${room}`}</code>&nbsp;
            <button
              onClick={() =>
                navigator.clipboard.writeText(
                  `${PARTICIPANT_ORIGIN}/chat/${room}`
                )
              }
            >
              Copy
            </button>
          </p>

          {/* setup toggle */}
          <button
            className="setup-toggle"
            onClick={() => setSetupMode((p) => !p)}
          >
            {setupMode ? "✅ Exit Setup Mode" : "🛠 Enter Setup Mode"}
          </button>

          {/* phase selector */}
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
              <button
                className="tiny-btn"
                onClick={addPhase}
                title="Add phase"
              >
                ＋
              </button>
            )}
          </div>

          {/* templates manager (unchanged UI) */}
          <TemplateManager
            phases={phases}
            setPhases={setPhases}
            currentPhaseId={currentPhaseId}
            setupMode={setupMode}
            onSend={send}
          />

          {/* custom free‑text reply */}
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
