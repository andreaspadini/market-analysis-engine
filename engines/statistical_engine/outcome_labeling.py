from __future__ import annotations

import pandas as pd


def append_breakout_outcome(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    bt = out["breakout_type"].astype("string").fillna("")

    outcome = pd.Series("true_breakout", index=out.index, dtype="object")
    outcome.loc[bt == "false_breakout"] = "false_breakout"
    outcome.loc[bt == "failed_follow_through"] = "failed_follow_through"

    out["breakout_outcome"] = outcome

    return out