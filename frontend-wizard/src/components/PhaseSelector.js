// frontend-wizard/src/components/PhaseSelector.js
import React from "react";

function PhaseSelector({ 
  phases, 
  currentPhaseId, 
  setCurrentPhaseId, 
  setupMode, 
  onAddPhase, 
  onRenamePhase, 
  onRemovePhase 
}) {
  return (
    <div className="phase-selector">
      {phases.map((p) => (
        <div key={p.id} className={`phase-pill ${p.id === currentPhaseId ? "active" : ""}`}>
          <button onClick={() => setCurrentPhaseId(p.id)} title="Select phase">
            {p.name}
          </button>
          {setupMode && (
            <>
              <button className="tiny-btn" title="Rename" onClick={() => onRenamePhase(p.id)}>
                ✏
              </button>
              <button 
                className="tiny-btn" 
                title="Delete phase" 
                onClick={() => onRemovePhase(p.id)} 
                disabled={phases.length === 1}
              >
                🗑
              </button>
            </>
          )}
        </div>
      ))}
      {setupMode && (
        <button className="tiny-btn" title="Add phase" onClick={onAddPhase}>
          ＋
        </button>
      )}
    </div>
  );
}

export default PhaseSelector;