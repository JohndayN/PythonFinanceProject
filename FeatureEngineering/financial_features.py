import pandas as pd
import numpy as np

def create_financial_features(df):

    df = df.sort_values("year")

    df["roa"] = df["net_income"] / df["total_assets"]
    df["roe"] = df["net_income"] / df["equity"]
    df["debt_to_assets"] = df["total_liabilities"] / df["total_assets"]

    df["revenue_growth"] = df["revenue"].pct_change()

    df["accrual_ratio"] = (
        (df["net_income"] - df["operating_cash_flow"])
        / df["total_assets"]
    )

    df["cf_to_income"] = df["operating_cash_flow"] / df["net_income"]

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    return df