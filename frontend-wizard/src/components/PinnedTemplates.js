// frontend-wizard/src/components/PinnedTemplates.js
import React, { useState, useRef } from "react";

function PinnedTemplates({ templates, setTemplates, setupMode, onPick }) {
  const [editIdx, setEditIdx] = useState(null);
  const [draft, setDraft] = useState("");

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
  const dragTo = useRef(null);
  const endDrag = () => {
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
          onDragEnter={() => (dragTo.current = i)}
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

export default PinnedTemplates;