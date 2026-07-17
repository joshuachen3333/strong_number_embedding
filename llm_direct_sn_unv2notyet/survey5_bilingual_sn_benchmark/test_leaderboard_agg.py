# test_leaderboard_agg.py — run: python3 test_leaderboard_agg.py
import run_leaderboard as RL


def _cell(model, prompt, arm, cov, place, dim=1):
    return {"model": model, "prompt": prompt, "arm": arm,
            "verses": [{"dim": dim, "score": {"coverage": cov, "placement": place}}]}


def main():
    cells = [
        _cell("opus", "terse", "wlc", 0.80, 0.75),
        _cell("sonnet", "terse", "wlc", 0.60, 0.55),
        _cell("opus", "terse", "wlc+ylt", 0.83, 0.78),
    ]
    board = RL.rank_cells(cells)
    assert board[0]["model"] == "opus" and board[0]["arm"] == "wlc+ylt", board
    assert board[-1]["model"] == "sonnet", board

    deltas = RL.paired_deltas(cells, base_arm="wlc")
    d = [x for x in deltas if x["model"] == "opus" and x["arm"] == "wlc+ylt"][0]
    assert abs(d["dcov"] - 0.03) < 1e-9 and abs(d["dplace"] - 0.03) < 1e-9, d
    print("test aggregation OK")

    k1 = RL.cell_key("opus", "prompts/survey5_wlc_v1.0_terse.md", "wlc")
    k2 = RL.cell_key("opus", "prompts/survey5_wlc_v1.0_terse.md", "wlc+ylt")
    assert k1 != k2 and k1.endswith(".json"), (k1, k2)
    print("test cache key OK")


if __name__ == "__main__":
    main()
