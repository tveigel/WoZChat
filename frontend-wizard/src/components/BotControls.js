// frontend-wizard/src/components/BotControls.js
import React, { useState, useEffect } from 'react';

// Constants
const API_ORIGIN = process.env.NODE_ENV === 'development' 
  ? "http://localhost:5000" 
  : "";

const BotControls = ({ room, socket }) => {
  const [botStatus, setBotStatus] = useState({
    active: false,
    available: false,
    progress: 'Not started'
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!socket || !room) return;

    // Listen for bot status updates
    const handleBotStatus = (data) => {
      if (data.room === room) {
        setBotStatus({
          active: data.active,
          available: data.available !== false, // Default to true if not specified
          progress: data.progress || data.message || (data.active ? 'Running' : 'Not started')
        });
      }
    };

    socket.on('bot_status_changed', handleBotStatus);

    // Request initial bot status
    fetch(`${API_ORIGIN}/api/bot/${room}/status`)
      .then(r => r.json())
      .then(status => setBotStatus(status))
      .catch(err => console.error('Failed to fetch bot status:', err));

    return () => {
      socket.off('bot_status_changed', handleBotStatus);
    };
  }, [socket, room]);

  const handleStartBot = async () => {
    if (!room || loading) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_ORIGIN}/api/bot/${room}/start`, {
        method: 'POST',
      });
      const data = await response.json();
      
      if (data.status === 'error') {
        alert(`Failed to start bot: ${data.message}`);
      }
    } catch (error) {
      console.error('Error starting bot:', error);
      alert('Failed to start bot: Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleStopBot = async () => {
    if (!room || loading) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_ORIGIN}/api/bot/${room}/stop`, {
        method: 'POST',
      });
      const data = await response.json();
      
      if (data.status === 'error') {
        alert(`Failed to stop bot: ${data.message}`);
      }
    } catch (error) {
      console.error('Error stopping bot:', error);
      alert('Failed to stop bot: Network error');
    } finally {
      setLoading(false);
    }
  };

  if (!botStatus.available) {
    return (
      <div className="bot-controls">
        <h3>🤖 Rule-Based Bot</h3>
        <div className="bot-status unavailable">
          <p>❌ Bot not available</p>
          <small>Check bot configuration and dependencies</small>
        </div>
      </div>
    );
  }

  return (
    <div className="bot-controls">
      <h3>🤖 Rule-Based Bot</h3>
      
      <div className={`bot-status ${botStatus.active ? 'active' : 'inactive'}`}>
        <p>
          <strong>Status:</strong> {botStatus.active ? '🟢 Active' : '🔴 Inactive'}
        </p>
        <p>
          <strong>Progress:</strong> {botStatus.progress}
        </p>
      </div>

      <div className="bot-actions">
        {botStatus.active ? (
          <button
            className="bot-btn stop-btn"
            onClick={handleStopBot}
            disabled={loading}
          >
            {loading ? 'Stopping...' : 'Stop Bot'}
          </button>
        ) : (
          <button
            className="bot-btn start-btn"
            onClick={handleStartBot}
            disabled={loading}
          >
            {loading ? 'Starting...' : 'Start Accident Report Bot'}
          </button>
        )}
      </div>

      <div className="bot-info">
        <small>
          {botStatus.active 
            ? 'The bot is handling participant messages automatically. Stop it to resume manual control.'
            : 'Start the bot to automatically guide the participant through an accident report form.'
          }
        </small>
      </div>
    </div>
  );
};

export default BotControls;
