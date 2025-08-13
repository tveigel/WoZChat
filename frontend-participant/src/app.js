// frontend-participant/src/app.js
import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import "./app.css";

// Simple markdown-style formatter for bot messages
const formatMessage = (text) => {
  if (typeof text !== 'string') return text;
  
  // Split by lines to handle different formatting per line
  const lines = text.split('\n');
  const formattedLines = lines.map((line, index) => {
    let formattedLine = line;
    
    // Handle bold text **text**
    formattedLine = formattedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text *text* (but not when surrounded by **)
    formattedLine = formattedLine.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');
    
    // Handle bullet points • or - at start of line (with potential whitespace)
    if (/^\s*[•\-]\s/.test(line)) {
      const cleanLine = formattedLine.replace(/^\s*[•\-]\s*/, '');
      return (
        <div key={index} className="bullet-point">
          <span dangerouslySetInnerHTML={{ __html: cleanLine }} />
        </div>
      );
    }
    
    // Handle error messages with ❌
    if (line.includes('❌')) {
      return (
        <div key={index} className="error-message">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    }
    
    // Handle progress indicators
    if (line.includes('Progress:') || line.includes('*Progress:')) {
      return (
        <div key={index} className="progress-indicator">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    }
    
    // Empty lines for spacing
    if (line.trim() === '') {
      return <div key={index} className="empty-line">&nbsp;</div>;
    }
    
    // Regular line with potential formatting
    if (formattedLine !== line) {
      return (
        <div key={index}>
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    }
    
    return <div key={index}>{line}</div>;
  });
  
  return <div className="formatted-message">{formattedLines}</div>;
};

// Component for rendering clickable UI elements
const UIComponent = ({ uiData, onSelect, isCurrentQuestion = true }) => {
  const [selectedOptions, setSelectedOptions] = useState([]);
  const [otherText, setOtherText] = useState('');
  const [showOtherInput, setShowOtherInput] = useState(false);

  if (!uiData || uiData.type !== 'clickable_choice') {
    return null;
  }

  const handleOptionClick = (option) => {
    // Only allow clicks on current questions
    // Previous questions should not be clickable
    if (!isCurrentQuestion) {
      return; // Disabled - users should use "change reply" command
    }

    // Current question logic (unchanged)
    if (uiData.allow_multiple) {
      setSelectedOptions(prev => {
        if (prev.includes(option)) {
          return prev.filter(o => o !== option);
        } else {
          return [...prev, option];
        }
      });
    } else {
      setSelectedOptions([option]);
      if (option.toLowerCase() === 'other' && uiData.allow_other) {
        setShowOtherInput(true);
      } else {
        setShowOtherInput(false);
        // Auto-submit for single choice (except when "Other" needs specification)
        setTimeout(() => handleSubmit([option], ''), 100);
      }
    }
  };

  const handleSubmit = (options = selectedOptions, otherValue = otherText) => {
    if (options.length === 0) return;

    const response = {
      type: 'choice_selection',
      selected_options: options,
      other_text: otherValue
    };
    
    onSelect(JSON.stringify(response));
  };

  const isSelected = (option) => selectedOptions.includes(option);

  return (
    <div className={`ui-component ${!isCurrentQuestion ? 'previous-question' : ''}`}>
      {!isCurrentQuestion && (
        <div className="edit-indicator">
          💡 Previous answer - Type "change reply" to edit
        </div>
      )}
      
      <div className="ui-instructions">
        {uiData.instructions}
      </div>
      
      <div className="ui-options">
        {uiData.options.map((option, index) => (
          <button
            key={index}
            className={`ui-option-button ${isSelected(option) ? 'selected' : ''} ${!isCurrentQuestion ? 'previous-question-option' : ''}`}
            onClick={() => handleOptionClick(option)}
            disabled={!isCurrentQuestion}
          >
            {uiData.allow_multiple && isCurrentQuestion && (
              <span className="checkbox">
                {isSelected(option) ? '☑' : '☐'}
              </span>
            )}
            {option}
          </button>
        ))}
      </div>

      {showOtherInput && isCurrentQuestion && (
        <div className="other-input-container">
          <input
            type="text"
            placeholder="Please specify..."
            value={otherText}
            onChange={(e) => setOtherText(e.target.value)}
            className="other-input"
            autoFocus
          />
        </div>
      )}

      {isCurrentQuestion && uiData.allow_multiple && selectedOptions.length > 0 && (
        <div className="ui-submit-container">
          <button
            className="ui-submit-button"
            onClick={() => handleSubmit()}
          >
            Submit Selection{selectedOptions.length > 1 ? 's' : ''}
          </button>
        </div>
      )}

      {isCurrentQuestion && showOtherInput && otherText.trim() && (
        <div className="ui-submit-container">
          <button
            className="ui-submit-button"
            onClick={() => handleSubmit(['Other'], otherText)}
          >
            Submit
          </button>
        </div>
      )}
    </div>
  );
};

// Component for rendering complete bot messages with UI
const BotMessage = ({ message, onUISelect, isLatestBotMessage = false }) => {
  // Try to parse message text as UI message
  let uiMessage = null;
  let displayText = message.text;
  
  try {
    if (typeof message.text === 'string' && message.text.trim().startsWith('{')) {
      const parsed = JSON.parse(message.text);
      if (parsed.sender === 'bot' && parsed.ui_component) {
        uiMessage = parsed;
        displayText = parsed.text;
      }
    }
  } catch (e) {
    // Not a UI message, use original text
  }

  const isCurrentQuestion = uiMessage && uiMessage.ui_component && uiMessage.ui_component.is_current_question && isLatestBotMessage;

  return (
    <>
      <div className="message-content">
        {formatMessage(displayText)}
      </div>
      {uiMessage && uiMessage.ui_component && (
        <UIComponent 
          uiData={uiMessage.ui_component} 
          onSelect={onUISelect}
          isCurrentQuestion={isCurrentQuestion}
        />
      )}
    </>
  );
};

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

/* little marketing‑style status lines the user sees while waiting */
const WAITING_HINTS = [
  "Thinking…",
  "Consulting the form wizard…",
  "Matching your reply to the form…",
  "Retrieving relevant information…",
  "Generating a response",
  "Just one moment…",
  "Almost there…",
  "Your form wizard is working hard…",
];

export default function App() {
  /* ─────────────────────────────── state */
  const [room] = useState(
    window.location.pathname.split("/").pop()
  );                                         // /chat/<room>
  const [messages, setMessages] = useState([]);
  const [current, setCurrent] = useState("");
  const [wizardTyping, setWizardTyping] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [waitingHint, setWaitingHint] = useState(WAITING_HINTS[0]);

  /* refs */
  const bottomRef        = useRef(null);
  const listRef          = useRef(null);
  const autoScrollRef    = useRef(true);     // track if user is at bottom
  const waitingTimerRef  = useRef(null);
  const inputRef         = useRef(null);

  /* ─────────────────────────────── socket life‑cycle */
  useEffect(() => {
    socket.emit("join", { room, type: "participant" });

    socket.on("message_history", ({ messages }) => {
      setMessages(messages || []);
    });

    socket.on("new_message", (msg) => {
      if (msg.sender === "wizard") {
        // replace any existing streaming message
        setMessages((prev) => [
          ...prev.filter((m) => m.sender !== "wizard_streaming"),
          msg,
        ]);
        setWizardTyping(false);
        stopWaitingAnimation();
        // Refocus input after wizard response
        setTimeout(() => inputRef.current?.focus(), 100);
      } else if (msg.sender === "bot") {
        // Handle bot messages - add them directly to the message list
        setMessages((prev) => [
          ...prev.filter((m) => m.sender !== "wizard_streaming"),
          msg,
        ]);
        setWizardTyping(false);
        stopWaitingAnimation();
        // Refocus input after bot response
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    });

    socket.on("stream_chunk", ({ word, is_last }) => {
      setWizardTyping(true);
      stopWaitingAnimation();                // hide “AI is processing…”
      setMessages((prev) => {
        const last = prev.at(-1);
        if (last?.sender === "wizard_streaming") {
          last.text += ` ${word}`;
          return [...prev.slice(0, -1), last];
        }
        return [...prev, { sender: "wizard_streaming", text: word }];
      });
      if (is_last) {
        setWizardTyping(false);
        // Refocus input after streaming completes
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    });

    return () => socket.emit("leave", { room });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [room]);

  /* smart autoscroll: scroll to bottom for new messages */
  useEffect(() => {
    // Always scroll to bottom when new messages arrive or when waiting/typing states change
    const shouldScroll = autoScrollRef.current || waiting || wizardTyping;
    if (shouldScroll) {
      // Use requestAnimationFrame to ensure DOM has updated
      requestAnimationFrame(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
      });
    }
  }, [messages, wizardTyping, waiting]);

  /* detect manual scrolls and update auto-scroll preference */
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    
    const handleScroll = () => {
      const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 50;
      autoScrollRef.current = nearBottom;
    };
    
    el.addEventListener("scroll", handleScroll);
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  /* Initial focus on input when component mounts */
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /* ─────────────────────────────── participant actions */
  const send = (e) => {
    e.preventDefault();
    if (!current.trim() || waiting) return;

    setMessages((p) => [...p, { sender: "participant", text: current }]);
    socket.emit("participant_message", { room, text: current });
    socket.emit("participant_typing", { room, text: "" });
    setCurrent("");
    startWaitingAnimation();
    
    // Ensure we scroll to bottom after sending
    autoScrollRef.current = true;
  };

  const handleUISelection = (selectionData) => {
    // Display the selection as a participant message
    let displayText = selectionData;
    try {
      const parsed = JSON.parse(selectionData);
      if (parsed.type === 'choice_selection') {
        if (parsed.selected_options.length === 1 && !parsed.other_text) {
          displayText = parsed.selected_options[0];
        } else if (parsed.selected_options.includes('Other') && parsed.other_text) {
          displayText = `Other: ${parsed.other_text}`;
        } else if (parsed.selected_options.length > 1) {
          displayText = parsed.selected_options.join(', ');
        }
      }
    } catch (e) {
      // Use original data as fallback
    }

    setMessages((p) => [...p, { sender: "participant", text: displayText }]);
    socket.emit("participant_message", { room, text: selectionData });
    startWaitingAnimation();
    
    // Ensure we scroll to bottom after sending
    autoScrollRef.current = true;
  };

  /* ─────────────────────────────── waiting animation helpers */
  const startWaitingAnimation = () => {
    setWaiting(true);
    setWaitingHint(WAITING_HINTS[0]);
    let i = 1;
    waitingTimerRef.current = setInterval(() => {
      setWaitingHint(WAITING_HINTS[i % WAITING_HINTS.length]);
      i += 1;
    }, 2700); // change hint every 3 seconds
  };

  const stopWaitingAnimation = () => {
    if (waitingTimerRef.current) clearInterval(waitingTimerRef.current);
    waitingTimerRef.current = null;
    setWaiting(false);
    // Ensure we scroll to bottom when responses arrive
    autoScrollRef.current = true;
  };

  /* ─────────────────────────────── UI */
  return (
    <div className="App">
      <div className="chat-header">
        <h2>🧙‍♂️ Form Wizard Assistant</h2>
        <p>I'm here to help you fill out forms by asking you questions and entering your responses accordingly. Let's get started!</p>
      </div>
      
      <div className="chat-window">
        <div ref={listRef} className="messages">
          {messages.map((m, i) => {
            const isLatestBotMessage = m.sender === 'bot' && 
              i === messages.findLastIndex(msg => msg.sender === 'bot');
              
            return (
              <div key={i} className={`message ${m.sender}`}>
                {(m.sender === "wizard" || m.sender === "wizard_streaming" || m.sender === "bot") && (
                  <span className="wizard-emoji">
                    {m.sender === "bot" ? "🤖" : "🧙‍♂️"}
                  </span>
                )}
                {m.sender === "bot" ? (
                  <BotMessage 
                    message={m} 
                    onUISelect={handleUISelection}
                    isLatestBotMessage={isLatestBotMessage}
                  />
                ) : (
                  <div className="message-content">
                    {typeof m.text === 'object'
                      ? <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                          {JSON.stringify(m.text, null, 2)}
                        </pre>
                      : (m.sender === "wizard" || m.sender === "wizard_streaming") 
                        ? formatMessage(m.text)
                        : m.text}
                  </div>
                )}
              </div>
            );
          })}

          {waiting && !wizardTyping && (
            <div className="waiting-indicator">
              <div className="spinner" />
              {waitingHint}
            </div>
          )}

          {wizardTyping && (
            <div className="message wizard typing-indicator">
              <span className="wizard-emoji">🧙‍♂️</span>
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* sticky input bar */}
        <form className="message-form" onSubmit={send}>
          <input
            ref={inputRef}
            value={current}
            onChange={(e) => {
              setCurrent(e.target.value);
              socket.emit("participant_typing", {
                room,
                text: e.target.value,
              });
            }}
            placeholder="Type your message…"
          />
          <button disabled={waiting || !current.trim()}>Send</button>
        </form>
      </div>
    </div>
  );
}
