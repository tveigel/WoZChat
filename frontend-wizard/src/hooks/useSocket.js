// frontend-wizard/src/hooks/useSocket.js
import { useEffect } from "react";
import io from "socket.io-client";

// Environment-aware socket connection
const socket = io(
  process.env.NODE_ENV === 'development' 
    ? "http://localhost:5000" 
    : window.location.origin,
  {
    transports: ["websocket"],
    path: "/socket.io"
  }
);

function useSocket(room, setMessages, setTyping, setPinnedTemplates, setPhases, setCurrentPhaseId, prevDict) {
  useEffect(() => {
    if (!room) return;
    
    // Leave any previous room before joining new one
    socket.emit("leave", { room: "previous" });
    
    // Join the new room
    socket.emit("join", { room, type: "wizard" });

    const onMsg = (m) => {
      // Only accept messages for the current room
      if (m.room && m.room !== room) return;
      setMessages((p) => [...p, m]);
    };
    
    const onType = ({ text, room: messageRoom }) => {
      // Only accept typing events for the current room
      if (messageRoom && messageRoom !== room) return;
      setTyping(text);
    };
    
    const onHistory = ({ messages, room: messageRoom }) => {
      // Only accept history for the current room
      if (messageRoom && messageRoom !== room) return;
      setMessages(messages || []);
    };
    
    const onTpls = (dict) => {
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
  }, [room, setMessages, setTyping, setPinnedTemplates, setPhases, setCurrentPhaseId, prevDict]);

  return socket;
}

export default useSocket;