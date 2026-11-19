from opportunity_finder.summaries import left_out_ideas, pruned_rows


def opp(name, score, process="P", value=5, effort=3, risk=2):
    return {"name": name, "score": score, "process": process, "value": value, "effort": effort, "risk": risk}


def test_left_out_excludes_picks_and_orders_by_score():
    opps = [opp("A", 0.5, "x"), opp("B", 0.4, "y"), opp("C", 0.3, "z"), opp("D", 0.2, "w")]
    rows = left_out_ideas(opps, ["A", "B"])
    assert [r["name"] for r in rows] == ["C", "D"]
    assert "below the lowest pick" in rows[0]["reason"]


def test_same_process_reason_and_close_call():
    opps = [opp("A", 0.5, "x"), opp("B", 0.46, "x")]
    row = left_out_ideas(opps, ["A"])[0]
    assert "Same process as A" in row["reason"] and "close call" in row["reason"]


def test_level_score_gets_roadmap_size_reason_and_empty_cases():
    opps = [opp("A", 0.5, "x"), opp("B", 0.5, "y")]
    assert "at most 1" in left_out_ideas(opps, ["A"])[0]["reason"]
    assert left_out_ideas(opps, ["nope"]) == []
    assert left_out_ideas(opps, ["A", "B"]) == []


def test_pruned_rows_translate_angles():
    rows = pruned_rows([{"id": "quick_win", "angle": "quick_win", "score": 0.37, "reason": "ranked below top 3"}])
    assert rows[0]["strategy"] == "Lowest-effort ideas first" and rows[0]["why dropped"] == "ranked below top 3"
    assert pruned_rows([]) == []
