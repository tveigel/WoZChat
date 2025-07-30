// frontend-wizard/src/components/WizardControls.js
import React from "react";

function WizardControls({ setupMode, setSetupMode, room }) {
  const handleCopyLink = () => {
    if (!room) {
      alert("No room available yet!");
      return;
    }
    
    // Smart URL generation that works in both dev and production
    let participantUrl;
    if (window.location.hostname === 'localhost') {
      // Development: participant runs on port 3000
      participantUrl = `http://localhost:3000/chat/${room}`;
    } else {
      // Production: same origin
      participantUrl = `${window.location.origin}/chat/${room}`;
    }
    
    navigator.clipboard.writeText(participantUrl).then(() => {
      // Visual feedback
      const btn = document.activeElement;
      const originalText = btn.textContent;
      btn.textContent = "✅ Copied!";
      setTimeout(() => {
        btn.textContent = originalText;
      }, 2000);
    }).catch(err => {
      console.error('Failed to copy: ', err);
      // Fallback: show the URL in an alert
      alert(`Participant link: ${participantUrl}`);
    });
  };

  return (
    <div className="header-row">
      <h2>Wizard Controls</h2>
      <div className="header-controls">
        <button className="setup-toggle header-btn" onClick={() => setSetupMode((p) => !p)}>
          {setupMode ? "✅ Exit Setup" : "🛠 Setup"}
        </button>
        <button className="header-btn" onClick={handleCopyLink}>
          📋 Copy Link
        </button>
      </div>
    </div>
  );
}

export default WizardControls;