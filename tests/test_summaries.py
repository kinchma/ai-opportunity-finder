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


def test_score_index_is_min_max_between_worst_and_best_and_never_reorders():
    from opportunity_finder.tools.scoring import (best_possible_score, idea_index, index_band, score_index,
                                                  score_opportunity, worst_possible_score)
    from opportunity_finder.summaries import ranking_rows, score_scale_note
    assert best_possible_score(0.5) == 0.9 and best_possible_score(0.4) == 0.89
    assert worst_possible_score(0.4) == -1.0
    assert score_index(0.89, 0.4) == 100 and score_index(-1.0, 0.4) == 0 and score_index(None, 0.4) is None
    # the Nov 17 Laurel Run ideas: 60/49/36 on the old share-of-best scale
    assert [idea_index({"value": v, "effort": e, "risk": r}, 0.4) for v, e, r in ((9, 5, 2), (7, 4, 1), (8, 6, 3))] == [81, 76, 70]
    assert idea_index({"value": 1, "effort": 10, "risk": 10}, 0.4) == 0      # below the stored 0 floor
    assert idea_index({"score": 0.53}, 0.4) == 81                             # falls back to the score
    assert [index_band(i) for i in (81, 80, 79, 65, 64, 50, 49, 0)] == [
        "Strong fit", "Strong fit", "Good fit", "Good fit", "Possible", "Possible", "Weak fit", "Weak fit"]
    assert index_band(None) == ""
    opps = [{"name": "A", "value": 9, "effort": 7, "risk": 3, "score": score_opportunity(9, 7, 3, 0.4)},
            {"name": "B", "value": 7, "effort": 5, "risk": 2, "score": score_opportunity(7, 5, 2, 0.4)},
            {"name": "C", "value": 5, "effort": 8, "risk": 6, "score": score_opportunity(5, 8, 6, 0.4)}]
    rows = ranking_rows(opps, 0.4)
    assert [r["opportunity"] for r in rows] == ["A", "B", "C"]            # ranked by score, as before
    idx = [r["index (0-100)"] for r in rows]
    assert idx == sorted(idx, reverse=True) and rows[0]["fit"] == "Good fit"   # same order as the scores
    assert "worst idea possible" in score_scale_note(0.4) and "80+ strong fit" in score_scale_note(0.4)
