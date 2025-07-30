// frontend-wizard/src/components/CustomResponse.js
import React from "react";

function CustomResponse({ draft, setDraft, onSend, textareaRef }) {
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
        <button type="submit">Send Response</button>
      </form>
    </div>
  );
}

export default CustomResponse;