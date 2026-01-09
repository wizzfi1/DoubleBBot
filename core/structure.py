def is_swing_low(df, i):
    if i <= 0 or i >= len(df) - 1:
        return False
    return (
        df.iloc[i]["low"] < df.iloc[i - 1]["low"]
        and df.iloc[i]["low"] < df.iloc[i + 1]["low"]
    )


def is_swing_high(df, i):
    if i <= 0 or i >= len(df) - 1:
        return False
    return (
        df.iloc[i]["high"] > df.iloc[i - 1]["high"]
        and df.iloc[i]["high"] > df.iloc[i + 1]["high"]
    )
