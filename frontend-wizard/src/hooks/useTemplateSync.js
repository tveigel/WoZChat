// frontend-wizard/src/hooks/useTemplateSync.js
import { useEffect } from "react";

// Constants
const API_ORIGIN = process.env.NODE_ENV === 'development' 
  ? "http://localhost:5000" 
  : "";

function useTemplateSync(phases, pinnedTemplates, initialLoad, prevDict) {
  const toDict = (ph, pin) => {
    const out = {};
    ph.forEach(({ name, templates }) => {
      const cat = name || "General";
      out[cat] = {};
      templates.forEach(({ id, text }) => (out[cat][id] = text));
    });
    out.Pinned = {};
    pin.forEach(({ id, text }) => (out.Pinned[id] = text));
    return out;
  };

  useEffect(() => {
    if (initialLoad.current) { 
      initialLoad.current = false; 
      return; 
    }
    
    const next = toDict(phases, pinnedTemplates);
    const prev = prevDict.current;

    // additions/updates
    for (const [cat, items] of Object.entries(next)) {
      for (const [key, text] of Object.entries(items)) {
        if (!prev[cat] || prev[cat][key] !== text) {
          fetch(`${API_ORIGIN}/api/templates/item`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: cat, key, value: text }),
          }).catch(console.error);
        }
      }
    }
    
    // deletions
    for (const [cat, items] of Object.entries(prev)) {
      for (const key of Object.keys(items)) {
        if (!next[cat] || !(key in next[cat])) {
          fetch(`${API_ORIGIN}/api/templates/${encodeURIComponent(cat)}/${encodeURIComponent(key)}`, { 
            method: "DELETE" 
          }).catch(console.error);
        }
      }
    }

    prevDict.current = next;
  }, [phases, pinnedTemplates, initialLoad, prevDict]);
}

export default useTemplateSync;