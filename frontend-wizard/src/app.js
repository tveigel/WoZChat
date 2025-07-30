// frontend‑wizard/src/app.js – updated for:
//   1) Scrollable chat column and template lists
//   2) Enter → send, Shift+Enter → newline in textarea
// Keeps all previous functionality incl. pinned templates & freeze‑fix.

import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";
import TemplateManager from "./TemplateManager";

// ─────────────────────────────────────────────────────────────────────────────
// CONSTANTS (unchanged – explicit host/port avoids “Creating room…” freeze)
// ─────────────────────────────────────────────────────────────────────────────
const API_ORIGIN =
  process.env.REACT_APP_API_ORIGIN || "http://localhost:5000";
const PARTICIPANT_ORIGIN =
  process.env.REACT_APP_PARTICIPANT_ORIGIN || "http://localhost:3000";

const socket = io("http://localhost:5000");

// ─────────────────────────────────────────────────────────────────────────────
// LOCAL COMPONENT – Pinned templates (same behaviour as before)
// ─────────────────────────────────────────────────────────────────────────────
function PinnedTemplates({ templates, setTemplates, setupMode, onPick }) {
  const [editIdx, setEditIdx] = useState(null);
  const [draft,   setDraft]   = useState("");

  const commit = () => {
    if (!draft.trim()) return;
    const next = [...templates];
    if (editIdx === "new") {
      next.push({ id: Date.now().toString(), text: draft.trim() });
    } else {
      next[editIdx] = { ...next[editIdx], text: draft.trim() };
    }
    setTemplates(next);
    setEditIdx(null);
    setDraft("");
  };

  const remove = (idx) => {
    const next = [...templates];
    next.splice(idx, 1);
    setTemplates(next);
  };

  /* drag‑n‑drop */
  const dragFrom = useRef(null);
  const dragTo   = useRef(null);
  const endDrag  = () => {
    if (
      dragFrom.current === null ||
      dragTo.current   === null ||
      dragFrom.current === dragTo.current
    ) {
      dragFrom.current = dragTo.current = null;
      return;
    }
    const next = [...templates];
    const [moved] = next.splice(dragFrom.current, 1);
    next.splice(dragTo.current, 0, moved);
    setTemplates(next);
    dragFrom.current = dragTo.current = null;
  };

  return (
    <div className="templates">
      <h3>
        Pinned Templates
        {setupMode && (
          <button
            className="tiny-btn"
            title="Add pinned template"
            onClick={() => {
              setEditIdx("new");
              setDraft("");
            }}
          >
            ＋
          </button>
        )}
      </h3>

      {templates.map((t, i) => (
        <div
          key={t.id}
          className="template-row"
          draggable={setupMode}
          onDragStart={() => (dragFrom.current = i)}
          onDragEnter={() => (dragTo.current   = i)}
          onDragEnd={endDrag}
        >
          {!setupMode && (
            <button
              className="template-btn"
              onClick={() => onPick(t.text)}
              title="Paste template"
            >
              {t.text}
            </button>
          )}

          {setupMode && (
            editIdx === i ? (
              <>
                <input
                  className="template-input"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  autoFocus
                />
                <button className="tiny-btn" onClick={commit} title="Save">✔</button>
                <button className="tiny-btn" onClick={() => setEditIdx(null)} title="Cancel">✖</button>
              </>
            ) : (
              <>
                <span className="template-text">{t.text}</span>
                <button className="tiny-btn" title="Edit" onClick={() => { setEditIdx(i); setDraft(t.text); }}>✏</button>
                <button className="tiny-btn" title="Delete" onClick={() => remove(i)}>🗑</button>
              </>
            )
          )}
        </div>
      ))}

      {setupMode && editIdx === "new" && (
        <div className="template-row">
          <input
            className="template-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="New template…"
            autoFocus
          />
          <button className="tiny-btn" onClick={commit} title="Add">✔</button>
          <button className="tiny-btn" onClick={() => setEditIdx(null)} title="Cancel">✖</button>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN WIZARD COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  /* state */
  const [room]    = useState(window.location.pathname.split("/").pop() || null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft]       = useState("");
  const [typing, setTyping]     = useState("");

  const [phases, setPhases] = useState([]);
  const [currentPhaseId, setCurrentPhaseId] = useState(null);
  const [pinnedTemplates, setPinnedTemplates] = useState([]);
  const [setupMode, setSetupMode] = useState(false);

  /* refs */
  const bottomRef   = useRef(null);
  const textareaRef = useRef(null);
  const initialLoad = useRef(true);
  const prevDict    = useRef({});

  /* ───────── room bootstrap */
  useEffect(() => {
    if (room) return;
    fetch(`${API_ORIGIN}/api/new_room`, { method: "POST" })
      .then((r) => r.json())
      .then(({ room: id }) => (window.location.pathname = `/wizard/${id}`));
  }, [room]);

  /* ───────── socket life‑cycle */
  useEffect(() => {
    if (!room) return;
    socket.emit("join", { room, type: "wizard" });

    const onMsg   = (m)        => setMessages((p) => [...p, m]);
    const onType  = ({ text }) => setTyping(text);
    const onHistory = ({ messages }) => setMessages(messages || []);
    const onTpls  = (dict)     => {
      /* pinned */
      const pinnedCat = dict.Pinned || {};
      setPinnedTemplates(Object.entries(pinnedCat).map(([id, text]) => ({ id, text })));

      /* phases */
      const newPhases = Object.entries(dict)
        .filter(([cat]) => cat !== "Pinned")
        .map(([cat, items]) => ({ id: cat, name: cat, templates: Object.entries(items).map(([id, text]) => ({ id, text })) }));
      setPhases(newPhases);
      setCurrentPhaseId((id) => id || newPhases[0]?.id || null);

      prevDict.current = dict; // snapshot
    };

    socket.on("new_message", onMsg);
    socket.on("participant_is_typing", onType);
    socket.on("message_history", onHistory);
    socket.on("templates", onTpls);

    return () => {
      socket.off("new_message", onMsg);
      socket.off("participant_is_typing", onType);
      socket.off("message_history", onHistory);
      socket.off("templates", onTpls);
      socket.emit("leave", { room });
    };
  }, [room]);

  /* ───────── autoscroll */
  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), [messages]);

  /* helpers */
  const send = (txt) => {
    if (!txt.trim()) return;
    socket.emit("wizard_response", { room, text: txt });
    setDraft("");
  };

  const pasteTemplate = (txt) => {
    setDraft(txt);
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const exportLog = () => {
    const blob = new Blob([JSON.stringify(messages, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `chat_${room}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  /* phase helpers (unchanged) */
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

  /* ───────── persistence (phases + pinned) */
  const toDict = (ph, pin) => {
    const out = {};
    ph.forEach(({ name, templates }) => {
      const cat = name || "General";
      out[cat] = {};
      templates.forEach(({ id, text }) => (out[cat][id] = text));
    });
    out.Pinned = {};
    pin.forEach(({ id, text }) => (out.Pinned[id] = text));
    return out;
  };

  useEffect(() => {
    if (initialLoad.current) { initialLoad.current = false; return; }
    const next = toDict(phases, pinnedTemplates);
    const prev = prevDict.current;

    // additions/updates
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
    // deletions
    for (const [cat, items] of Object.entries(prev)) {
      for (const key of Object.keys(items)) {
        if (!next[cat] || !(key in next[cat])) {
          fetch(`${API_ORIGIN}/api/templates/${encodeURIComponent(cat)}/${encodeURIComponent(key)}`, { method: "DELETE" }).catch(console.error);
        }
      }
    }

    prevDict.current = next;
  }, [phases, pinnedTemplates]);

  /* ───────── UI */
  if (!room) return <p>Creating room…</p>;

  return (
    <div className="App">
      {/* grid override: 1fr 2fr keeps chat ≤33% */}
      <div className="wizard-panel" style={{ gridTemplateColumns: "1fr 2fr" }}>
        {/* chat column */}
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
                {typeof m.text === "object" ? <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{JSON.stringify(m.text, null, 2)}</pre> : m.text}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="live-typing">
            <p>Participant is typing:</p>
            <div className="typing-preview">{typing || "…"}</div>
          </div>
        </div>

        {/* control column */}
        <div className="control-area" style={{ overflowY: "auto" }}>
          <div className="header-row">
            <h2>Wizard Controls</h2>
            <div className="header-controls">
              <button className="setup-toggle header-btn" onClick={() => setSetupMode((p) => !p)}>
                {setupMode ? "✅ Exit Setup" : "🛠 Setup"}
              </button>
              <button 
                className="header-btn"
                onClick={() => navigator.clipboard.writeText(`${PARTICIPANT_ORIGIN}/chat/${room}`)}
              >
                📋 Copy Link
              </button>
            </div>
          </div>


          {/* pinned templates scroll wrapper */}
          <div style={{ maxHeight: "35vh", overflowY: "auto" }}>
            <PinnedTemplates
              templates={pinnedTemplates}
              setTemplates={setPinnedTemplates}
              setupMode={setupMode}
              onPick={pasteTemplate}
            />
          </div>

          {/* phase selector */}
          <div className="phase-selector">
            {phases.map((p) => (
              <div key={p.id} className={`phase-pill ${p.id === currentPhaseId ? "active" : ""}`}>
                <button onClick={() => setCurrentPhaseId(p.id)} title="Select phase">{p.name}</button>
                {setupMode && (
                  <>
                    <button className="tiny-btn" title="Rename" onClick={() => renamePhase(p.id)}>✏</button>
                    <button className="tiny-btn" title="Delete phase" onClick={() => removePhase(p.id)} disabled={phases.length === 1}>🗑</button>
                  </>
                )}
              </div>
            ))}
            {setupMode && <button className="tiny-btn" title="Add phase" onClick={addPhase}>＋</button>}
          </div>

          {/* phase templates with own scroll */}
          <div style={{ maxHeight: "35vh", overflowY: "auto" }}>
            <TemplateManager
              phases={phases}
              setPhases={setPhases}
              currentPhaseId={currentPhaseId}
              setupMode={setupMode}
              onSend={pasteTemplate}
            />
          </div>

          {/* custom response */}
          {!setupMode && (
            <div className="custom-response">
              <h3>Custom Response</h3>
              <form onSubmit={(e) => { e.preventDefault(); send(draft); }}>
                <textarea
                  ref={textareaRef}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send(draft);
                    }
                  }}
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
