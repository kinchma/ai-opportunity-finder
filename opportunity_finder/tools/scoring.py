"""Exact, coded scoring and roadmap checks. The LLM does not do arithmetic here."""

# Penalties are subtracted from a roadmap's base score (the mean of its ideas' scores, 0..1).
P_DUPLICATE = 0.20        # the same idea twice in one roadmap
P_SAME_PROCESS = 0.03     # two ideas change the same process at once
P_ORDER = 0.05            # foundation (enabler) work placed after ideas that build on it
P_RISK_PER_POINT = 0.03   # per risk point above the owner's limit (doubled for the pilot)
P_BUDGET_PER_POINT = 0.05  # per effort point above the owner's effort budget (capped)
P_BUDGET_MAX = 0.30
P_UNGROUNDED = 0.10       # an idea with no process, practice or website finding behind it
P_PILOT_EFFORT = 0.03     # a high-effort idea in the pilot slot
PILOT_EFFORT_LIMIT = 7


def score_opportunity(value: int, effort: int, risk: int,
                      risk_tolerance: float = 0.5) -> float:
    """value/effort/risk on a 1-10 scale. Returns 0..1, higher is better.

    Lower risk tolerance makes risk count more. TODO: tune weights.
    """
    raw = value - 0.5 * effort - (1.0 - risk_tolerance) * risk
    return round(max(raw, 0.0) / 10, 3)


def risk_limit(risk_tolerance: float = 0.5) -> float:
    """Highest risk rating (1-10) the owner accepts: 2 at tolerance 0, 5 at 0.5, 8 at 1."""
    return round(2 + 6 * max(0.0, min(1.0, risk_tolerance)), 2)


def roadmap_checks(items: list, risk_tolerance: float = 0.5, effort_budget: float | None = None,
                   grounded: dict | None = None) -> list:
    """Exact checks on one roadmap. `items` are the scored ideas in roadmap order (pilot first).

    Returns findings: {code, item, penalty, message}. `item` is the idea a revision should
    replace or move (None when the finding is about the whole roadmap). `grounded` maps an idea
    name to True/False; ideas missing from it are treated as grounded.
    """
    out = []
    names = [o["name"] for o in items]

    def add(code, item, penalty, message, **extra):
        out.append({"code": code, "item": item, "penalty": round(penalty, 3), "message": message, **extra})

    for n in sorted({n for n in names if names.count(n) > 1}):
        add("duplicate", n, P_DUPLICATE, f"'{n}' appears more than once")

    seen = {}
    for o in items:  # the lower-scoring of two ideas on the same process is the one to replace
        proc = o.get("process")
        if not proc:
            continue
        if proc in seen and seen[proc]["name"] != o["name"]:
            weaker = min((seen[proc], o), key=lambda x: x["score"])
            add("duplicate_process", weaker["name"], P_SAME_PROCESS,
                f"two ideas change the same process ({proc}) at once")
        else:
            seen[proc] = o

    first_other = next((i for i, o in enumerate(items) if not o.get("enabler")), None)
    late = [o["name"] for i, o in enumerate(items) if o.get("enabler") and first_other is not None and i > first_other]
    if late:
        add("dependency_order", None, P_ORDER,
            f"foundation work ({', '.join(late)}) is placed after ideas that build on it")

    limit = risk_limit(risk_tolerance)
    for i, o in enumerate(items):
        if o["risk"] > limit:
            over = o["risk"] - limit
            add("risk_above_tolerance", o["name"], P_RISK_PER_POINT * over * (2 if i == 0 else 1),
                f"'{o['name']}' has risk {o['risk']}/10, above the owner's limit of {limit}"
                + (" and it is the pilot" if i == 0 else ""), limit=limit)

    if effort_budget:
        total = sum(o["effort"] for o in items)
        if total > effort_budget:
            costly = max(items, key=lambda o: o["effort"])
            add("over_budget", costly["name"], min(P_BUDGET_PER_POINT * (total - effort_budget), P_BUDGET_MAX),
                f"total effort {total} is above the owner's effort budget of {effort_budget:g}")

    for o in items:
        if o.get("placeholder"):
            add("placeholder", o["name"], P_UNGROUNDED, f"'{o['name']}' is a placeholder idea, not from this business")
        elif grounded is not None and grounded.get(o["name"]) is False:
            add("ungrounded", o["name"], P_UNGROUNDED,
                f"'{o['name']}' has no process, cited practice or website finding behind it")

    if items and items[0]["effort"] >= PILOT_EFFORT_LIMIT and not items[0].get("enabler") \
            and any(o["effort"] < items[0]["effort"] for o in items[1:]):
        add("pilot_effort", None, P_PILOT_EFFORT,
            f"the pilot ('{items[0]['name']}') is high effort ({items[0]['effort']}/10); start with something quicker")
    return out


def score_roadmap(items: list, findings: list, rubric_avg: float | None = None,
                  rubric_weight: float = 0.15) -> dict:
    """Roadmap score = (mean idea score - penalties), then nudged by the Critic model's rubric.

    `rubric_avg` is the mean of the model's 1-5 ratings; 3 is neutral. The model can move the
    coded score by at most +/- rubric_weight, so it can break ties but never override the math.
    """
    base = sum(o["score"] for o in items) / len(items) if items else 0.0
    penalty = sum(f["penalty"] for f in findings)
    coded = max(base - penalty, 0.0)
    mult = 1.0 if rubric_avg is None else 1.0 + rubric_weight * (max(1.0, min(5.0, rubric_avg)) - 3.0) / 2.0
    return {"base_score": round(base, 3), "penalty": round(penalty, 3), "coded_score": round(coded, 3),
            "score": round(coded * mult, 3)}


def coded_roadmap_checks(opportunities: list, budget: float | None = None) -> float:
    """Kept for older callers: duplicate-name penalty only. New code uses roadmap_checks."""
    return P_DUPLICATE if len(set(opportunities)) != len(opportunities) else 0.0
