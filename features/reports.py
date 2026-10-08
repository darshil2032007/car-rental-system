# Reporting and Visualization module using pandas and matplotlib
import os
import pandas as pd
import matplotlib
# Use Agg backend for thread-safe, non-GUI headless plotting
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from features import database

# Directory for exporting CSV and Excel reports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def load_bookings_dataframe():
    """
    Fetches all bookings from the database and constructs a clean pandas DataFrame.
    Parses dates and numerical columns.
    """
    raw_data = database.get_all_bookings()
    columns = [
        "booking_id", "customer_id", "vehicle_id", "start_date", "due_date",
        "return_date", "total_amount", "late_fee", "customer_name",
        "brand", "model", "category"
    ]

    if not raw_data:
        # Return empty DataFrame with defined column schema
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(raw_data, columns=columns)

    # Convert date columns using pd.to_datetime
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["due_date"] = pd.to_datetime(df["due_date"])
    df["return_date"] = pd.to_datetime(df["return_date"])

    # Ensure financial numbers are float
    df["total_amount"] = df["total_amount"].astype(float)
    df["late_fee"] = df["late_fee"].astype(float)

    # Add combined vehicle name column for clean display
    df["vehicle_name"] = df["brand"] + " " + df["model"]

    return df


def monthly_revenue(df):
    """
    Aggregates total revenue grouped by return month.
    Returns a DataFrame with ['Month', 'Revenue'].
    """
    if df.empty:
        return pd.DataFrame(columns=["Month", "Revenue"])

    # Consider only completed bookings with return_date and total_amount > 0
    completed = df[df["return_date"].notna() & (df["total_amount"] > 0)].copy()
    if completed.empty:
        return pd.DataFrame(columns=["Month", "Revenue"])

    completed["Month"] = completed["return_date"].dt.strftime("%Y-%m")
    summary = completed.groupby("Month")["total_amount"].sum().reset_index()
    summary.rename(columns={"total_amount": "Revenue"}, inplace=True)
    return summary.sort_values(by="Month")


def top_vehicles(df):
    """
    Calculates total booking count per vehicle.
    Returns a DataFrame sorted descending by booking count.
    """
    if df.empty:
        return pd.DataFrame(columns=["vehicle_name", "category", "booking_count"])

    summary = df.groupby(["vehicle_name", "category"]).size().reset_index(name="booking_count")
    return summary.sort_values(by="booking_count", ascending=False)


def category_distribution():
    """
    Counts available and total vehicles by category from live database.
    Returns a DataFrame with ['category', 'count'].
    """
    vehicles = database.get_all_vehicles()
    if not vehicles:
        return pd.DataFrame(columns=["category", "count"])

    # row format: (vehicle_id, brand, model, category, rate_per_day, status)
    df_v = pd.DataFrame(vehicles, columns=["vehicle_id", "brand", "model", "category", "rate_per_day", "status"])
    summary = df_v.groupby("category").size().reset_index(name="count")
    return summary


# ---------------- MATPLOTLIB PLOTTING FUNCTIONS ----------------

def plot_monthly_revenue(df):
    """
    Creates and returns a matplotlib line chart figure showing monthly revenue.
    Returns None if no data is available.
    """
    rev_df = monthly_revenue(df)
    if rev_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(rev_df["Month"], rev_df["Revenue"], marker="o", color="#2b5c8f", linewidth=2.5, markersize=7)
    ax.set_title("Monthly Revenue Trend", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Revenue (₹)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)

    # Format data labels on points
    for _, row in rev_df.iterrows():
        ax.annotate(f"₹{int(row['Revenue'])}", (row["Month"], row["Revenue"]),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, fontweight="bold")

    fig.tight_layout()
    return fig


def plot_top_vehicles(df):
    """
    Creates and returns a matplotlib bar chart figure of top rented vehicles.
    Returns None if no data is available.
    """
    top_df = top_vehicles(df)
    if top_df.empty:
        return None

    # Limit to top 5 for neat layout
    top_df = top_df.head(5)

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(top_df["vehicle_name"], top_df["booking_count"], color="#3b82f6", width=0.55, edgecolor="#1d4ed8")
    ax.set_title("Most Rented Vehicles", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Vehicle", fontsize=11)
    ax.set_ylabel("Bookings Count", fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Add count labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{int(height)}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    return fig


def plot_category_pie():
    """
    Creates and returns a matplotlib pie chart figure of vehicle categories.
    Returns None if no vehicles exist.
    """
    cat_df = category_distribution()
    if cat_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    colors = ["#4ade80", "#60a5fa", "#f472b6", "#fbbf24", "#a78bfa"]
    ax.pie(
        cat_df["count"],
        labels=cat_df["category"],
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(cat_df)],
        textprops={"fontsize": 11, "fontweight": "medium"}
    )
    ax.set_title("Vehicle Fleet by Category", fontsize=14, fontweight="bold", pad=12)
    fig.tight_layout()
    return fig


def export_reports(df):
    """
    Exports the bookings DataFrame to CSV and Excel (.xlsx) formats.
    Returns dictionary with file paths.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    csv_file = os.path.join(REPORTS_DIR, "bookings.csv")
    xlsx_file = os.path.join(REPORTS_DIR, "bookings.xlsx")

    # Export to CSV
    df.to_csv(csv_file, index=False)

    # Export to Excel using openpyxl engine
    df.to_excel(xlsx_file, index=False, engine="openpyxl")

    return {
        "csv": csv_file,
        "xlsx": xlsx_file
    }
