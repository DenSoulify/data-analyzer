import pandas as pd

def breakdown(df, amount_col, kind, column, date_col):
    """Total, average, count and share of total per group."""
    if kind == "month":
        key = df[date_col].dt.to_period("M").astype(str)
    else:
        key = df[column]

    result = df.groupby(key)[amount_col].agg(["sum", "mean", "count"])
    total = result["sum"].sum()
    result["share"] = result["sum"] / total * 100 if total else 0.0

    if kind != "month":   # months stay chronological, everything else: biggest first
        result = result.sort_values("sum", ascending=False)
    return result

def count_months(dates):
    """Number of calendar months from the first to the last date, inclusive."""
    first, last = dates.min(), dates.max()
    return (last.year - first.year) * 12 + (last.month - first.month) + 1


def budget_vs_actual(df, amount_col, group_col, date_col,
                     budget_df, budget_group_col, budget_col):
    """Actual spending per group next to its budget for the whole period."""
    months = count_months(df[date_col])

    actual = df.groupby(df[group_col].astype(str).str.strip())[amount_col].sum()
    # budgets are monthly, so scale them to the length of the data
    budget = budget_df.set_index(budget_group_col)[budget_col] * months

    result = pd.DataFrame({"actual": actual, "budget": budget}).fillna(0)
    result["difference"] = result["actual"] - result["budget"]
    # share of budget used; groups with no budget get NaN instead of a divide-by-zero
    result["used"] = result["actual"] / result["budget"].where(result["budget"] > 0) * 100

    return result.sort_values("actual", ascending=False), months