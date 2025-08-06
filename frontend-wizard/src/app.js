// frontend‑wizard/src/app.js – Refactored with component separation
// Maintains all existing functionality while improving code organization

import React, { useState, useEffect, useRef } from "react";
import "./app.css";

// Components
import ChatArea from "./components/ChatArea";
import WizardControls from "./components/WizardControls";
import PinnedTemplates from "./components/PinnedTemplates";
import PhaseSelector from "./components/PhaseSelector";
import TemplateManager from "./TemplateManager";
import CustomResponse from "./components/CustomResponse";
import BotControls from "./components/BotControls";

// Custom Hooks
import useSocket from "./hooks/useSocket";
import useTemplateSync from "./hooks/useTemplateSync";

// Constants
const API_ORIGIN = process.env.NODE_ENV === 'development' 
  ? "http://localhost:5000" 
  : "";

// ─────────────────────────────────────────────────────────────────────────────
// MAIN WIZARD COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  /* state */
  const parts = window.location.pathname.split("/");
  const last = parts.pop();
  const [room] = useState((last && last !== "wizard") ? last : null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [typing, setTyping] = useState("");

  const [phases, setPhases] = useState([]);
  const [currentPhaseId, setCurrentPhaseId] = useState(null);
  const [pinnedTemplates, setPinnedTemplates] = useState([]);
  const [setupMode, setSetupMode] = useState(false);

  /* refs */
  const textareaRef = useRef(null);
  const initialLoad = useRef(true);
  const prevDict = useRef({});

  /* ───────── room bootstrap */
  useEffect(() => {
    if (room) return;
    fetch(`${API_ORIGIN}/api/new_room`, { method: "POST" })
      .then((r) => r.json())
      .then(({ room: id }) => (window.location.pathname = `/wizard/${id}`));
  }, [room]);

  /* ───────── custom hooks */
  const socket = useSocket(room, setMessages, setTyping, setPinnedTemplates, setPhases, setCurrentPhaseId, prevDict);
  useTemplateSync(phases, pinnedTemplates, initialLoad, prevDict);

  /* ───────── message handlers */
  const send = (txt) => {
    if (!txt.trim()) return;
    socket.emit("wizard_response", { room, text: txt });
    setDraft("");
  };

  const pasteTemplate = (txt) => {
    setDraft(txt);
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  /* ───────── phase management */
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

  /* ───────── UI */
  if (!room) return <p>Creating room…</p>;

  return (
    <div className="App">
      {/* grid override: 1fr 2fr keeps chat ≤33% */}
      <div className="wizard-panel" style={{ gridTemplateColumns: "1fr 2fr" }}>
        
        {/* chat column */}
        <ChatArea 
          messages={messages}
          typing={typing}
          room={room}
        />

        {/* control column */}
        <div className="control-area" style={{ overflowY: "auto" }}>
          <WizardControls 
            setupMode={setupMode}
            setSetupMode={setSetupMode}
            room={room}
          />

          {/* bot controls */}
          <BotControls room={room} socket={socket} />

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
          <PhaseSelector
            phases={phases}
            currentPhaseId={currentPhaseId}
            setCurrentPhaseId={setCurrentPhaseId}
            setupMode={setupMode}
            onAddPhase={addPhase}
            onRenamePhase={renamePhase}
            onRemovePhase={removePhase}
          />

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
            <CustomResponse
              draft={draft}
              setDraft={setDraft}
              onSend={send}
              textareaRef={textareaRef}
            />
          )}
        </div>
      </div>
    </div>
  );
}
