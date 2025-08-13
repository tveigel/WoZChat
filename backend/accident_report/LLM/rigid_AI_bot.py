# backend/accident_report/LLM/rigid_AI_bot.py
from __future__ import annotations
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Annotated
from typing_extensions import TypedDict, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage

# Import LLM config - handle both direct execution and package imports
try:
    from .llm_config import llm
except ImportError:
    from llm_config import llm

# Reuse the validator only (source of truth)
try:
    from ..rule_based.validator import validate_answer
except ImportError:
    try:
        from backend.accident_report.rule_based.validator import validate_answer
    except ImportError:
        # For direct execution, add parent directories to path
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        from rule_based.validator import validate_answer


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

class AIBotState(TypedDict, total=False):
    messages: Annotated[list, add_messages]

    # questionnaire + navigation
    questions: List[Dict[str, Any]]
    q_index: int                     # index in main questions
    current_qid: Optional[str]

    # data & progress
    form_title: str
    form_data: Dict[str, Any]
    questions_completed: List[str]
    done: bool

    # group handling
    current_group: Optional[Dict[str, Any]]
    group_field_index: int
    group_data: Dict[str, Any]

    # repeat group handling
    current_repeat: Optional[Dict[str, Any]]
    repeat_field_index: int
    repeat_instance_index: int
    repeat_instances: List[Dict[str, Any]]      # completed instances
    current_instance: Dict[str, Any]
    expected_instances: Optional[int]

    # control
    retry_count: int
    last_error: Optional[str]

    # llm helpers
    rephrased_question: Optional[str]
    clarifying_question: Optional[str]
    needs_clarification: bool
    parse_candidate: Any
    parse_confidence: float
    original_user_input: Optional[str]  # Store original input for clarification context

    # reference time for relative dates ("two days ago"), times, etc.
    reference_datetime: str  # ISO string


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

REPHRASE_SYSTEM = """\
You write the next SINGLE user-facing question for a traffic accident report.
Be concise, friendly, and ask only ONE thing. If options exist, list them as bullets.
If helpful, give ONE short example. Do not answer for the user.
If within a repeating group (like vehicles), prefix with 'Vehicle N – '.
"""

EXTRACT_SYSTEM = """\
You normalize the user's reply to the current field and decide if clarification is needed.
Return ONLY JSON with keys:
- normalized: string (the exact canonical answer your validator would accept; e.g. "Turning-Left", "Other: 4 vehicles", "2025-06-12", "14:35", "yes", "no", "30")
- needs_clarification: boolean
- clarifying_question: string or null (ONE short follow-up)
- confidence: number [0..1]
Rules:
- If reply is ambiguous, set needs_clarification=true and propose a targeted clarifying_question.
- For time, prefer HH:MM 24-hour. If only '2' is given, ask "AM or PM?" or propose HH:MM choices.
- For relative dates ("two days ago"), convert using the provided REFERENCE_DATETIME.
- For single_choice with other_specify, use format "Other: <text>" for non-listed values.
- For multiple_choice, return comma-separated option texts (may include "Other: <text>").
- For tables/repeat elements when asked, return JSON arrays/objects per the field schema IDs.
- If input starts with "Original:" it contains both original input and clarification - combine them intelligently.
  Example: "Original: 2, Clarification: am" should normalize to "02:00" for time fields.
Do not include explanations outside the JSON.
"""

CLARIFY_FALLBACK = "Could you clarify with the exact value I'm asking for?"


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _safe_json(s: str) -> Optional[Dict[str, Any]]:
    if not s:
        return None
    m = re.search(r"\{.*\}", s, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def _gold_hint(q_def: Dict[str, Any]) -> str:
    if "gold_standard" not in q_def:
        return ""
    try:
        return "\nGOLD_STANDARD_HINT: " + json.dumps(q_def["gold_standard"], ensure_ascii=False)
    except Exception:
        return ""

def _options_hint(q_def: Dict[str, Any]) -> str:
    if q_def.get("type") in ("single_choice", "multiple_choice"):
        return "\nOPTIONS: " + ", ".join(q_def.get("options", []))
    return ""

def _target_format(q_def: Dict[str, Any]) -> str:
    t = q_def.get("type")
    if t == "date":
        return "YYYY-MM-DD (use REFERENCE_DATETIME for relative dates)"
    if t == "time":
        return "HH:MM (24-hour)"
    if t == "number":
        return "a number with no units"
    if t == "boolean":
        return "yes or no"
    if t == "single_choice":
        return "one option text (or 'Other: <text>' if allowed)"
    if t == "multiple_choice":
        return "comma-separated option texts (and 'Other: <text>' if needed)"
    if t == "group":
        return "JSON object for the sub-field only (we ask one field at a time)"
    if t == "repeat_group":
        return "We ask one sub-field of one instance at a time"
    if t == "table":
        return "JSON array of row objects (columns by ID)"
    return "a short text answer"

def _ref_time_hint(reference_iso: str) -> str:
    return f"\nREFERENCE_DATETIME: {reference_iso}"

def _prev_answers_hint(state: AIBotState) -> str:
    data = state.get("form_data", {})
    if not data:
        return ""
    # keep prompt small: take first 6 items
    keys = list(data.keys())[:6]
    subset = {k: data[k] for k in keys}
    try:
        return "\nPREVIOUS_ANSWERS: " + json.dumps(subset, ensure_ascii=False)
    except Exception:
        return ""

def _candidate_to_validator_string(candidate: Any, q_def: Dict[str, Any]) -> str:
    t = q_def.get("type")
    if candidate is None:
        return ""

    if isinstance(candidate, (int, float)):
        return str(candidate)
    if isinstance(candidate, bool):
        return "yes" if candidate else "no"
    if isinstance(candidate, list):
        return ", ".join(map(str, candidate))

    s = str(candidate).strip()

    if t in ("single_choice", "multiple_choice") and q_def.get("other_specify"):
        # normalize "other ..." → "Other: ..."
        if re.match(r"^\s*other(?:\s*[:\-])?\s*", s, flags=re.I):
            rest = re.sub(r"^\s*other(?:\s*[:\-])?\s*", "", s, flags=re.I).strip()
            s = f"Other: {rest}" if rest else "Other:"

    return s

def _load_questions(default_path: Optional[str] = None) -> Dict[str, Any]:
    if default_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        default_path = os.path.join(here, "..", "questionnaire", "questions.json")
    path = os.path.abspath(default_path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─────────────────────────────────────────────────────────────────────────────
# LLM adapters
# ─────────────────────────────────────────────────────────────────────────────

def llm_rephrase_question(state: AIBotState, q_def: Dict[str, Any], prefix: str = "") -> str:
    user = {
        "role": "user",
        "content": (
            "Rephrase this question.\n\n"
            f"QUESTION_DEF: {json.dumps(q_def, ensure_ascii=False)}\n"
            f"TARGET_FORMAT: {_target_format(q_def)}"
            f"{_options_hint(q_def)}"
            f"{_gold_hint(q_def)}"
            f"{_prev_answers_hint(state)}"
        )
    }
    out = llm.invoke([{"role": "system", "content": REPHRASE_SYSTEM}, user])
    text = out.content if hasattr(out, "content") else str(out)
    return (prefix + text.strip()).strip()

def llm_extract_normalize(state: AIBotState, q_def: Dict[str, Any], user_text: str) -> Dict[str, Any]:
    user = {
        "role": "user",
        "content": (
            "Normalize the user's reply for validator input.\n\n"
            f"QUESTION_DEF: {json.dumps(q_def, ensure_ascii=False)}\n"
            f"TARGET_FORMAT: {_target_format(q_def)}\n"
            f"USER_REPLY: {json.dumps(user_text, ensure_ascii=False)}"
            f"{_options_hint(q_def)}"
            f"{_gold_hint(q_def)}"
            f"{_prev_answers_hint(state)}"
            f"{_ref_time_hint(state.get('reference_datetime', _now_iso()))}"
        )
    }
    out = llm.invoke([{"role": "system", "content": EXTRACT_SYSTEM}, user])
    text = out.content if hasattr(out, "content") else str(out)
    data = _safe_json(text) or {}
    return {
        "normalized": data.get("normalized"),
        "needs_clarification": bool(data.get("needs_clarification", False)),
        "clarifying_question": data.get("clarifying_question") or None,
        "confidence": float(data.get("confidence", 0.0)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Workflow
# ─────────────────────────────────────────────────────────────────────────────

class AIBotWorkflow:
    """
    Standalone AI form bot for traffic accident reports.
    • Builds prompts from the JSON schema
    • Accepts ambiguous replies and normalizes them
    • Asks smart follow-ups when needed
    • Uses validator.py as final truth
    """

    def __init__(self, questions_file: Optional[str] = None, *, interactive: bool = True,
                 reference_datetime: Optional[str] = None):
        qdata = _load_questions(questions_file)
        self.questions_data = qdata
        self.questions = qdata["questions"]
        self.title = qdata.get("title", "Accident Report Form")

        self.interactive = interactive
        self.reference_datetime = reference_datetime or _now_iso()

        self.graph_builder = StateGraph(AIBotState)
        self.memory = InMemorySaver()
        self._build_graph()

    # ───────────── graph nodes

    def start(self, state: AIBotState) -> AIBotState:
        print(f"\n🏁 {self.title}")
        print("I'll guide you and handle ambiguous inputs (e.g., 'two days ago').")
        return {
            "messages": [],
            "questions": self.questions,
            "q_index": 0,
            "current_qid": self.questions[0]["id"],
            "form_title": self.title,
            "form_data": {},
            "questions_completed": [],
            "done": False,
            "current_group": None,
            "group_field_index": 0,
            "group_data": {},
            "current_repeat": None,
            "repeat_field_index": 0,
            "repeat_instance_index": 0,
            "repeat_instances": [],
            "current_instance": {},
            "expected_instances": None,
            "retry_count": 0,
            "last_error": None,
            "rephrased_question": None,
            "clarifying_question": None,
            "needs_clarification": False,
            "parse_candidate": None,
            "parse_confidence": 0.0,
            "original_user_input": None,
            "reference_datetime": self.reference_datetime,
        }

    def ask(self, state: AIBotState) -> AIBotState:
        q_def = self._active_qdef(state)
        if not q_def:
            return state

        prefix = self._repeat_prefix(state)
        try:
            rephrased = llm_rephrase_question(state, q_def, prefix=prefix)
        except Exception:
            rephrased = (prefix + q_def["question"]).strip()

        if state.get("retry_count", 0) and state.get("last_error"):
            print(f"\n❌ {state['last_error']}\n")

        print(f"❓ {rephrased}")
        
        # Show what we parsed from the last answer (if any)
        if state.get("parse_candidate") is not None:
            print(f"   📝 (I understood: {state.get('parse_candidate')})")
        
        # If web mode, we pause here (no stdin)
        return {**state, "rephrased_question": rephrased}  # no mutation for web pause

    def get_user(self, state: AIBotState) -> AIBotState:
        if not self.interactive:
            return state
        text = input("\n👤 Your answer: ").strip()
        return {"messages": state.get("messages", []) + [HumanMessage(content=text)]}

    def interpret(self, state: AIBotState) -> AIBotState:
        if not state.get("messages"):
            return state
        
        user_text = state["messages"][-1].content
        q_def = self._active_qdef(state)
        if not q_def:
            return state

        # If we're in a clarification flow, combine original input with clarification
        if state.get("needs_clarification") and state.get("original_user_input"):
            combined_input = f"Original: {state['original_user_input']}, Clarification: {user_text}"
            print(f"   🔗 Combining: {state['original_user_input']} + {user_text}")
        else:
            combined_input = user_text

        out = {}
        try:
            out = llm_extract_normalize(state, q_def, combined_input)
        except Exception:
            out = {"normalized": None, "needs_clarification": True, "clarifying_question": CLARIFY_FALLBACK, "confidence": 0.0}

        # Needs clarification → ask once, do not validate yet
        if out.get("needs_clarification") and not state.get("needs_clarification"):
            # First time asking for clarification - store original input
            clar = out.get("clarifying_question") or CLARIFY_FALLBACK
            print(f"\n🔎 {clar}")
            return {
                **state,
                "retry_count": state.get("retry_count", 0) + 1,
                "last_error": None,
                "needs_clarification": True,
                "clarifying_question": clar,
                "parse_candidate": out.get("normalized"),
                "parse_confidence": out.get("confidence", 0.0),
                "original_user_input": user_text,  # Store the original input
            }
        elif out.get("needs_clarification") and state.get("needs_clarification"):
            # Still needs clarification after combining - give up and use fallback
            clar = CLARIFY_FALLBACK
            print(f"\n🔎 {clar}")
            return {
                **state,
                "retry_count": state.get("retry_count", 0) + 1,
                "last_error": None,
                "needs_clarification": True,
                "clarifying_question": clar,
                "parse_candidate": out.get("normalized"),
                "parse_confidence": out.get("confidence", 0.0),
                "original_user_input": None,  # Reset
            }

        candidate = out.get("normalized")
        norm_str = _candidate_to_validator_string(candidate, q_def)

        # Replace the last user message with the normalized string so validate() can use it
        updated_msgs = state.get("messages", [])[:-1] + [HumanMessage(content=norm_str)]
        return {
            **state,
            "messages": updated_msgs,
            "needs_clarification": False,
            "clarifying_question": None,
            "parse_candidate": candidate,
            "parse_confidence": out.get("confidence", 0.0),
            "original_user_input": None,  # Reset after successful processing
        }

    def validate_and_route(self, state: AIBotState) -> AIBotState:
        # If we just asked for clarification, re-ask rather than validate
        if state.get("needs_clarification"):
            return state  # route → retry ask

        if not state.get("messages"):
            return state

        q_def = self._active_qdef(state)
        if not q_def:
            return state

        norm_in = state["messages"][-1].content
        ok, either = validate_answer(q_def, norm_in)

        if not ok:
            # validator failed → retry & give its hint
            return {
                **state,
                "retry_count": state.get("retry_count", 0) + 1,
                "last_error": f"Invalid input: {either}. Please try again.",
            }

        # validator passed → commit to data structure based on where we are
        value = either
        next_state = {**state, "retry_count": 0, "last_error": None}

        # repeat group?
        if state.get("current_repeat"):
            cr = state["current_repeat"]
            fields = cr["fields"]
            fld_idx = state.get("repeat_field_index", 0)
            fld = fields[fld_idx]
            new_instance = {**state.get("current_instance", {}), fld["id"]: value}
            next_state["current_instance"] = new_instance  # type: ignore

            if fld_idx + 1 < len(fields):
                # move to next field in same vehicle
                next_state["repeat_field_index"] = fld_idx + 1  # type: ignore
                return next_state
            else:
                # finish this instance
                instances = list(state.get("repeat_instances", [])) + [new_instance]
                next_state["repeat_instances"] = instances  # type: ignore

                expected = self._expected_repeat_instances(next_state)  # compute lazily
                inst_idx = state.get("repeat_instance_index", 0)

                # start next instance if expected not met
                if expected is not None and len(instances) < expected:
                    next_state["repeat_instance_index"] = inst_idx + 1  # type: ignore
                    next_state["repeat_field_index"] = 0               # type: ignore
                    next_state["current_instance"] = {}                # type: ignore
                    return next_state
                else:
                    # commit the whole repeat group to form_data
                    form_data = dict(state.get("form_data", {}))
                    form_data[state["current_qid"]] = instances  # type: ignore
                    completed = list(state.get("questions_completed", []))
                    if state["current_qid"] not in completed:
                        completed.append(state["current_qid"])    # type: ignore

                    next_state.update({
                        "form_data": form_data,
                        "questions_completed": completed,
                        "current_repeat": None,
                        "repeat_field_index": 0,
                        "repeat_instance_index": 0,
                        "repeat_instances": [],
                        "current_instance": {},
                    })
                    # move to next main question or finish
                    return self._advance_main(next_state)

        # group?
        if state.get("current_group"):
            cg = state["current_group"]
            fields = cg["fields"]
            fld_idx = state.get("group_field_index", 0)
            fld = fields[fld_idx]
            new_group = {**state.get("group_data", {}), fld["id"]: value}
            next_state["group_data"] = new_group  # type: ignore

            if fld_idx + 1 < len(fields):
                next_state["group_field_index"] = fld_idx + 1  # type: ignore
                return next_state
            else:
                # finish group → commit to form_data
                form_data = dict(state.get("form_data", {}))
                form_data[state["current_qid"]] = new_group     # type: ignore
                completed = list(state.get("questions_completed", []))
                if state["current_qid"] not in completed:
                    completed.append(state["current_qid"])       # type: ignore

                next_state.update({
                    "form_data": form_data,
                    "questions_completed": completed,
                    "current_group": None,
                    "group_field_index": 0,
                    "group_data": {},
                })
                return self._advance_main(next_state)

        # regular main field commit
        form_data = dict(state.get("form_data", {}))
        form_data[state["current_qid"]] = value  # type: ignore

        completed = list(state.get("questions_completed", []))
        if state["current_qid"] not in completed:
            completed.append(state["current_qid"])  # type: ignore

        next_state.update({"form_data": form_data, "questions_completed": completed})

        # if boolean with followup_if_yes
        if q_def.get("type") == "boolean" and value is True and "followup_if_yes" in q_def:
            # switch to follow-up qdef (subquestion stands alone)
            fup = q_def["followup_if_yes"]
            next_state["current_qid"] = fup["id"]  # type: ignore
            # model handles tables: validator expects JSON array for 'table'
            return next_state

        # if starting a group
        if q_def.get("type") == "group":
            next_state["current_group"] = q_def     # type: ignore
            next_state["group_field_index"] = 0     # type: ignore
            next_state["group_data"] = {}           # type: ignore
            return next_state

        # if starting a repeat group
        if q_def.get("type") == "repeat_group":
            next_state["current_repeat"] = q_def    # type: ignore
            next_state["repeat_field_index"] = 0    # type: ignore
            next_state["repeat_instance_index"] = 0 # type: ignore
            next_state["repeat_instances"] = []     # type: ignore
            next_state["current_instance"] = {}     # type: ignore
            return next_state

        # otherwise advance main
        return self._advance_main(next_state)

    def complete(self, state: AIBotState) -> AIBotState:
        print("\n🎉 Form completed successfully!\n")
        print("📋 Summary:")
        for qid, ans in state.get("form_data", {}).items():
            print(f"• {qid}: {ans}")
        # Save
        out = {
            "form_title": state.get("form_title", "Accident Report"),
            "completion_date": datetime.now(timezone.utc).date().isoformat(),
            "responses": state.get("form_data", {}),
        }
        with open("completed_form.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False, default=str)
        print("\n💾 Saved to completed_form.json")
        return {**state, "done": True}

    # ───────────── routing helpers

    def _advance_main(self, state: AIBotState) -> AIBotState:
        idx = state.get("q_index", 0)
        if idx >= len(state.get("questions", [])) - 1:
            return {**state, "done": True}
        nxt = state["questions"][idx + 1]
        return {
            **state,
            "q_index": idx + 1,
            "current_qid": nxt["id"],
        }

    def _active_qdef(self, state: AIBotState) -> Optional[Dict[str, Any]]:
        # repeat?
        if state.get("current_repeat"):
            rg = state["current_repeat"]
            fidx = state.get("repeat_field_index", 0)
            fields = rg.get("fields", [])
            if 0 <= fidx < len(fields):
                return fields[fidx]
            return None
        # group?
        if state.get("current_group"):
            gq = state["current_group"]
            fidx = state.get("group_field_index", 0)
            fields = gq.get("fields", [])
            if 0 <= fidx < len(fields):
                return fields[fidx]
            return None
        # follow-up (stored by id) or main
        qid = state.get("current_qid")
        if not qid:
            return None
        for q in state["questions"]:
            if q["id"] == qid:
                return q
            if "followup_if_yes" in q and q["followup_if_yes"]["id"] == qid:
                return q["followup_if_yes"]
        return None

    def _repeat_prefix(self, state: AIBotState) -> str:
        if state.get("current_repeat"):
            return f"Vehicle {state.get('repeat_instance_index', 0) + 1} – "
        return ""

    def _expected_repeat_instances(self, state: AIBotState) -> Optional[int]:
        # infer from number_of_vehicles_involved if present
        ans = state.get("form_data", {}).get("number_of_vehicles_involved")
        if isinstance(ans, dict):  # when single_choice with Other
            choice = ans.get("choice")
            if choice and choice.isdigit():
                return int(choice)
            other = ans.get("other")
            try:
                return int(re.findall(r"\d+", str(other or ""))[0])
            except Exception:
                return None
        if isinstance(ans, str) and ans.isdigit():
            return int(ans)
        return None

    # ───────────── graph build

    def _build_graph(self):
        gb = self.graph_builder

        gb.add_node("start", self.start)
        gb.add_node("ask", self.ask)
        gb.add_node("get_user", self.get_user if self.interactive else (lambda s: s))
        gb.add_node("interpret", self.interpret)
        gb.add_node("validate_and_route", self.validate_and_route)
        gb.add_node("complete", self.complete)

        gb.add_edge(START, "start")
        gb.add_edge("start", "ask")

        if self.interactive:
            gb.add_edge("ask", "get_user")
            gb.add_edge("get_user", "interpret")
        else:
            # web mode: after ask, we stop (frontend sends user text later),
            # and the driver should resume at 'interpret'
            pass

        # conditional edges after interpret/validate
        def router(state: AIBotState) -> Literal["ask", "validate_and_route", "complete"]:
            if state.get("done"):
                return "complete"
            # If we asked a clarifier, just ask again (stay on ask)
            if state.get("needs_clarification"):
                return "ask"
            # if we haven't validated yet, do it
            return "validate_and_route"

        gb.add_conditional_edges("interpret", router,
                                 {"ask": "ask", "validate_and_route": "validate_and_route", "complete": "complete"})

        def after_validate(state: AIBotState) -> Literal["ask", "complete"]:
            if state.get("done"):
                return "complete"
            return "ask"

        gb.add_conditional_edges("validate_and_route", after_validate, {"ask": "ask", "complete": "complete"})
        gb.add_edge("complete", END)

    def compile_graph(self):
        return self.graph_builder.compile(checkpointer=self.memory)


    # CLI runner
    def run(self):
        graph = self.compile_graph()
        image_data = graph.get_graph().draw_mermaid_png()
        with open("form_workflow_graph.png", "wb") as f:
            f.write(image_data)
        cfg = {"configurable": {"thread_id": "ai_form_session"}, "recursion_limit": 100}
        try:
            for ev in graph.stream({}, config=cfg):
                for _, node_state in ev.items():
                    if node_state.get("done"):
                        return
        except KeyboardInterrupt:
            print("\n⏹️  Interrupted. Progress saved to memory.")


# ─────────────────────────────────────────────────────────────────────────────
# Script entry
# ─────────────────────────────────────────────────────────────────────────────

def main():
    bot = AIBotWorkflow(interactive=True)
    bot.run()

if __name__ == "__main__":
    main()
