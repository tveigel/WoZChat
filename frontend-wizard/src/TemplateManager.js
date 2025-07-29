// frontend‑wizard/src/TemplateManager.js
//
// Template list for the currently‑selected phase.
// ‑ Normal mode: click → send
// ‑ Setup  mode: drag‑sort, tiny ✏/🗑, “＋” to add

import React, { useRef, useState } from "react";
import "./app.css";

export default function TemplateManager({
  phases,
  setPhases,
  currentPhaseId,
  setupMode,
  onSend,
}) {
  /* ───────── helpers ───────── */
  const phaseIdx = phases.findIndex((p) => p.id === currentPhaseId);
  let templates = phases[phaseIdx]?.templates ?? [];

  // Accept the case where templates accidentally come in as an object
  if (!Array.isArray(templates)) {
    templates = Object.entries(templates).map(([id, val]) => ({
      id,
      text: typeof val === "string" ? val : JSON.stringify(val),
    }));
  }

  const updateTemplates = (next) =>
    setPhases(
      phases.map((p, i) =>
        i === phaseIdx ? { ...p, templates: next } : p
      )
    );

  /* ───────── add / edit ───────── */
  const [editIdx, setEditIdx] = useState(null); // null ⇒ none, "new" ⇒ add
  const [draft, setDraft] = useState("");

  const commitEdit = () => {
    if (!draft.trim()) return;
    let next = [...templates];
    if (editIdx === "new") {
      next.push({ id: Date.now().toString(), text: draft.trim() });
    } else {
      next[editIdx] = { ...next[editIdx], text: draft.trim() };
    }
    updateTemplates(next);
    setEditIdx(null);
    setDraft("");
  };

  const removeTemplate = (idx) => {
    const next = [...templates];
    next.splice(idx, 1);
    updateTemplates(next);
  };

  /* ───────── drag‑&‑drop ───────── */
  const dragFrom = useRef(null);
  const dragTo = useRef(null);

  const handleDragEnd = () => {
    if (
      dragFrom.current === null ||
      dragTo.current === null ||
      dragFrom.current === dragTo.current
    ) {
      dragFrom.current = dragTo.current = null;
      return;
    }
    const next = [...templates];
    const [moved] = next.splice(dragFrom.current, 1);
    next.splice(dragTo.current, 0, moved);
    updateTemplates(next);
    dragFrom.current = dragTo.current = null;
  };

  /* ───────── render ───────── */
  return (
    <div className="templates">
      <h3>
        Templates{" "}
        {setupMode && (
          <button
            className="tiny-btn"
            title="Add template"
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
          onDragEnter={() => (dragTo.current = i)}
          onDragEnd={handleDragEnd}
        >
          {/* ───── normal mode: quick‑send button ───── */}
          {!setupMode && (
            <button
              className="template-btn"
              onClick={() => onSend(t.text)}
              title="Send template"
            >
              {t.text}
            </button>
          )}

          {/* ───── setup mode view / edit ───── */}
          {setupMode &&
            (editIdx === i ? (
              <>
                <input
                  className="template-input"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  autoFocus
                />
                <button className="tiny-btn" onClick={commitEdit} title="Save">
                  ✔
                </button>
                <button
                  className="tiny-btn"
                  onClick={() => setEditIdx(null)}
                  title="Cancel"
                >
                  ✖
                </button>
              </>
            ) : (
              <>
                <span className="template-text">{t.text}</span>
                <button
                  className="tiny-btn"
                  onClick={() => {
                    setEditIdx(i);
                    setDraft(t.text);
                  }}
                  title="Edit"
                >
                  ✏
                </button>
                <button
                  className="tiny-btn"
                  onClick={() => removeTemplate(i)}
                  title="Delete"
                >
                  🗑
                </button>
              </>
            ))}
        </div>
      ))}

      {/* inline “add new” row */}
      {setupMode && editIdx === "new" && (
        <div className="template-row">
          <input
            className="template-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="New template…"
            autoFocus
          />
          <button className="tiny-btn" onClick={commitEdit} title="Add">
            ✔
          </button>
          <button
            className="tiny-btn"
            onClick={() => setEditIdx(null)}
            title="Cancel"
          >
            ✖
          </button>
        </div>
      )}
    </div>
  );
}
