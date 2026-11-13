from pathlib import Path

import numpy as np
import pandas as pd
# CSV randomizer to test out the program without actual data.
rng = np.random.default_rng(42)  # fixed seed -> same data every run, now the seed is randomized each time the program is run

# category -> (min amount, max amount, vendors)
CATEGORIES = {
    "Software":       (300, 4000, ["Microsoft", "Atlassian", "Adobe", "Slack"]),
    "Hardware":       (300, 6000, ["Dell", "Lenovo", "Apple"]),
    "Cloud services": (800, 5000, ["AWS", "Azure", "Google Cloud"]),
    "Consulting":     (1000, 8000, ["Accenture", "Deloitte", "Local Consulting Oy"]),
    "Advertising":    (500, 7000, ["Google Ads", "Meta Ads", "LinkedIn"]),
    "Events":         (800, 9000, ["Eventful Oy", "Messukeskus", "Conference Co"]),
    "Travel":         (150, 2500, ["Finnair", "VR", "Booking.com"]),
    "Training":       (200, 3000, ["Udemy", "Coursera", "Local Academy"]),
    "Recruitment":    (500, 5000, ["Oikotie", "LinkedIn", "Recruit Partners"]),
    "Equipment":      (400, 7000, ["Fastems", "Toolmaster", "Industrial Supply"]),
    "Maintenance":    (200, 3500, ["ServiceCo", "FixIt Oy", "Kone"]),
    "Supplies":       (50, 900, ["Staples", "Lyreco", "Tokmanni"]),
}
FIXED_CATEGORIES = {"Software", "Cloud services"}

# department -> {category: transactions per month}
DEPARTMENTS = {
    "IT":         {"Software": 3, "Hardware": 1, "Cloud services": 3, "Consulting": 1},
    "Marketing":  {"Advertising": 4, "Software": 1, "Consulting": 1, "Events": 1, "Travel": 1},
    "Sales":      {"Travel": 4, "Events": 1, "Software": 1, "Training": 1},
    "HR":         {"Recruitment": 3, "Training": 2, "Software": 1, "Consulting": 1},
    "Finance":    {"Software": 2, "Consulting": 2, "Training": 1},
    "Operations": {"Equipment": 3, "Maintenance": 3, "Travel": 1, "Supplies": 3},
}


def generate_transactions():
    months = pd.period_range("2025-01", "2026-10", freq="M")
    rows = []
    for i, month in enumerate(months):
        growth = 1 + 0.01 * i                         # costs creep up over time
        seasonal = 1.15 if month.month >= 10 else 1.0  # Q4 is more expensive
        for dept, cats in DEPARTMENTS.items():
            for cat, n_transactions in cats.items():
                low, high, vendors = CATEGORIES[cat]
                for _ in range(n_transactions):
                    day = int(rng.integers(0, month.days_in_month))
                    rows.append({
                        "Date": month.start_time + pd.Timedelta(days=day),
                        "Department": dept,
                        "Category": cat,
                        "Vendor": rng.choice(vendors),
                        "Cost_Type": "Fixed" if cat in FIXED_CATEGORIES else "Variable",
                        "Amount": round(rng.uniform(low, high) * growth * seasonal, 2),
                    })
    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    return df


def generate_budgets(transactions):
    # Monthly budget per department, based on actual average +/- noise.
    monthly = transactions.groupby("Department")["Amount"].sum() / 22  # 22 months
    budgets = (monthly * rng.uniform(0.9, 1.1, len(monthly)) / 500).round() * 500
    return budgets.rename("Monthly_Budget").reset_index()

# Creates data folder and CSV files inside it from transactions and budgets
if __name__ == "__main__":
    out = Path("data")
    out.mkdir(exist_ok=True)

    transactions = generate_transactions()
    transactions.to_csv(out / "cost_transactions.csv", index=False)
    generate_budgets(transactions).to_csv(out / "department_budgets.csv", index=False)

    print(f"Created {len(transactions)} transactions in {out.resolve()}")