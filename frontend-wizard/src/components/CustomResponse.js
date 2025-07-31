// frontend-wizard/src/components/CustomResponse.js
import React from "react";

function CustomResponse({ draft, setDraft, onSend, textareaRef }) {
  const sendCheckmark = () => {
    onSend("✅");
  };

  return (
    <div className="custom-response">
      <h3>Custom Response</h3>
      <form onSubmit={(e) => { e.preventDefault(); onSend(draft); }}>
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend(draft);
            }
          }}
          placeholder="Type a custom response…"
        />
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button type="submit">Send Response</button>
          <button 
            type="button" 
            onClick={sendCheckmark}
            style={{ 
              backgroundColor: "#28a745", 
              color: "white", 
              border: "none", 
              padding: "8px 12px", 
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "16px"
            }}
            title="Send green checkmark"
          >
            ✅
          </button>
        </div>
      </form>
    </div>
  );
}

export default CustomResponse;