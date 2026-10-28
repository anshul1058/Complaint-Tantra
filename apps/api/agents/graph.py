from typing import TypedDict


class CaseState(TypedDict, total=False):
    case: dict
    intake: dict | None
    triage: dict | None
    overlaps: list | None
    web: dict | None
    brief: dict | None
    needs_review: bool


def intake_agent(state: CaseState):
    from agents.ai_member import run_intake

    case = state.get("case") or {}
    try:
        out = run_intake(case)
    except Exception:
        from agents import _rule_intake

        out = _rule_intake(case)
    return {"intake": out, "needs_review": bool(out.get("needs_review"))}


def triage_agent(state: CaseState):
    from agents.ai_member import run_triage

    case = state.get("case") or {}
    intake = state.get("intake")
    try:
        out = run_triage(case, intake)
    except Exception:
        from agents import _rule_triage

        out = _rule_triage(case, intake)
    needs = state.get("needs_review") or bool(out.get("needs_review"))
    return {"triage": out, "needs_review": needs}


def overlap_agent(state: CaseState):
    # Overlap is handled by services in async path; provide stub
    return {"overlaps": []}


def web_intel_agent(state: CaseState):
    from agents.web_intel import run_web_intel

    case = state.get("case") or {}
    inst = {"name": case.get("raw_institution") or case.get("institution_name")}
    try:
        out = run_web_intel(inst)
    except Exception:
        out = {"findings": [], "reputation_risk": 0.0, "needs_review": True}
    needs = state.get("needs_review") or bool(out.get("needs_review"))
    return {"web": out, "needs_review": needs}


def briefing_agent(state: CaseState):
    from agents.briefing import write_brief

    case = state.get("case") or {}
    try:
        out = write_brief(case, state)
    except Exception:
        out = {"case_brief": "", "needs_review": True}
    needs = state.get("needs_review") or bool(out.get("needs_review"))
    return {"brief": out, "needs_review": needs}


def build_graph():
    from langgraph.graph import END, StateGraph

    g = StateGraph(CaseState)
    g.add_node("intake", intake_agent)
    g.add_node("triage", triage_agent)
    g.add_node("overlap", overlap_agent)
    g.add_node("web_intel", web_intel_agent)
    g.add_node("brief", briefing_agent)

    g.set_entry_point("intake")
    g.add_edge("intake", "triage")
    g.add_edge("intake", "overlap")
    g.add_edge("intake", "web_intel")
    # Fan-in join: each parallel branch must have its own edge into brief
    g.add_edge("triage", "brief")
    g.add_edge("overlap", "brief")
    g.add_edge("web_intel", "brief")
    g.add_edge("brief", END)
    return g.compile()


def get_graph():
    """Lazy compile so import never fails if langgraph isn't installed (offline path)."""
    global graph
    if graph is None:
        graph = build_graph()
    return graph


graph = None
