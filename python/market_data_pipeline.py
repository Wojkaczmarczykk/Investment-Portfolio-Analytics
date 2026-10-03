"""
Market Data ETL Pipeline

Downloads current mWIG40 components from Bankier.pl,
retrieves historical market data from Yahoo Finance,
and stores incremental updates in SQL Server.

The pipeline also downloads benchmark data for:
- S&P 500
- NASDAQ 100
- KOSPI

Data range:
current year + two complete historical years.
"""

import pandas as pd
import yfinance as yf
import urllib.parse
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta


print("START SCRIPT")


# ============================================================
# SQL SERVER CONNECTION
# ============================================================

server = r'localhost\SQLEXPRESS'
database = 'mWIG40_Portfolio'

params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={params}"
)


# ============================================================
# DATE RANGE
# ============================================================

today = datetime.now().date()
current_year = today.year

# Current year + two full historical years
start_date = datetime(current_year - 2, 1, 1).date()


# ============================================================
# GET CURRENT mWIG40 COMPONENTS FROM BANKIER.PL
# ============================================================

print("\nGetting current mWIG40 components from Bankier.pl...")

bankier_url = (
    "https://www.bankier.pl/inwestowanie/profile/quote.html?symbol=MWIG40"
)

try:
    tables = pd.read_html(bankier_url)

    mwig_table = None

    for table in tables:
        if "Ticker" in table.columns:
            mwig_table = table
            break

    if mwig_table is None:
        raise Exception("Could not find mWIG40 table containing 'Ticker'.")

    tickers = (
        mwig_table["Ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
        .dropna()
        .tolist()
    )

    # Remove duplicates while keeping original order
    tickers = list(dict.fromkeys(tickers))

    print(f"Found {len(tickers)} mWIG40 components.")

except Exception as e:
    print(f"ERROR while getting mWIG40 components: {e}")
    raise


# ============================================================
# mWIG40 STOCK DATA
# ============================================================

df_final = pd.DataFrame()

print("\nDownloading mWIG40 stock data...")


for ticker in tickers:

    yahoo_ticker = ticker + ".WA"

    try:

        # ----------------------------------------------------
        # Check last available date in SQL Server
        # ----------------------------------------------------

        with engine.connect() as conn:

            result = conn.execute(
                text(
                    """
                    SELECT MAX(Date)
                    FROM Fact_StockPrices
                    WHERE Ticker = :ticker
                    """
                ),
                {"ticker": ticker}
            ).scalar()

        if result is None:

            download_start = start_date

        else:

            last_date = pd.to_datetime(result).date()
            download_start = last_date + timedelta(days=1)

        # ----------------------------------------------------
        # Skip if data is already up to date
        # ----------------------------------------------------

        if download_start > today:

            print(f"{ticker}: already up to date.")
            continue

        print(
            f"{ticker}: downloading from {download_start}..."
        )

        # ----------------------------------------------------
        # Download data from Yahoo Finance
        # ----------------------------------------------------

        df = yf.download(
            yahoo_ticker,
            start=download_start,
            end=today + timedelta(days=1),
            progress=False,
            auto_adjust=False,
            actions=False,
            threads=False
        )

        if df.empty:

            print(f"{ticker}: no new data.")
            continue

        # ----------------------------------------------------
        # Handle MultiIndex returned by yfinance
        # ----------------------------------------------------

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        # ----------------------------------------------------
        # Prepare dataframe
        # ----------------------------------------------------

        df = df.reset_index()

        df["Ticker"] = ticker
        df["IndexName"] = "mWIG40"

        # Rename columns if necessary
        df = df.rename(
            columns={
                "Date": "Date",
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Volume": "Volume"
            }
        )

        # Remove AdjustedClose if returned
        if "AdjustedClose" in df.columns:

            df = df.drop(columns=["AdjustedClose"])

        # Convert Date
        df["Date"] = pd.to_datetime(df["Date"])

        # ----------------------------------------------------
        # Append to final dataframe
        # ----------------------------------------------------

        df_final = pd.concat(
            [df_final, df],
            ignore_index=True
        )

        print(
            f"{ticker}: {len(df)} rows downloaded."
        )

    except Exception as e:

        print(
            f"{ticker}: ERROR - {e}"
        )


# ============================================================
# SAVE mWIG40 DATA TO SQL SERVER
# ============================================================

if not df_final.empty:

    print(
        f"\nSaving {len(df_final)} mWIG40 rows to SQL Server..."
    )

    df_final.to_sql(
        "Fact_StockPrices",
        engine,
        if_exists="append",
        index=False
    )

    print("mWIG40 data saved successfully.")

else:

    print("\nNo new mWIG40 data to save.")


# ============================================================
# CLEAN OLD mWIG40 DATA
# ============================================================

print("\nCleaning old mWIG40 data...")

with engine.begin() as conn:

    conn.execute(
        text(
            """
            DELETE FROM Fact_StockPrices
            WHERE Date < :start_date
            """
        ),
        {"start_date": start_date}
    )

print("Old mWIG40 data cleaned.")


# ============================================================
# BENCHMARK INDICES
# ============================================================

indices = {
    "SP500": "^GSPC",
    "NASDAQ100": "^NDX",
    "KOSPI": "^KS11"
}


df_indices_final = pd.DataFrame()

print("\nDownloading benchmark indices...")


for index_name, yahoo_ticker in indices.items():

    try:

        # ----------------------------------------------------
        # Check last available date in SQL Server
        # ----------------------------------------------------

        with engine.connect() as conn:

            result = conn.execute(
                text(
                    """
                    SELECT MAX(Date)
                    FROM Fact_Indices
                    WHERE IndexName = :index_name
                    """
                ),
                {"index_name": index_name}
            ).scalar()

        if result is None:

            download_start = start_date

        else:

            last_date = pd.to_datetime(result).date()
            download_start = last_date + timedelta(days=1)

        # ----------------------------------------------------
        # Skip if data is already up to date
        # ----------------------------------------------------

        if download_start > today:

            print(
                f"{index_name}: already up to date."
            )

            continue

        print(
            f"{index_name}: downloading from {download_start}..."
        )

        # ----------------------------------------------------
        # Download index data
        # ----------------------------------------------------

        df = yf.download(
            yahoo_ticker,
            start=download_start,
            end=today + timedelta(days=1),
            progress=False,
            auto_adjust=False,
            actions=False,
            threads=False
        )

        if df.empty:

            print(
                f"{index_name}: no new data."
            )

            continue

        # ----------------------------------------------------
        # Handle MultiIndex
        # ----------------------------------------------------

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        # ----------------------------------------------------
        # Prepare dataframe
        # ----------------------------------------------------

        df = df.reset_index()

        df = df[
            [
                "Date",
                "Close"
            ]
        ]

        df["IndexName"] = index_name

        df["Date"] = pd.to_datetime(
            df["Date"]
        )

        # ----------------------------------------------------
        # Append to final dataframe
        # ----------------------------------------------------

        df_indices_final = pd.concat(
            [
                df_indices_final,
                df
            ],
            ignore_index=True
        )

        print(
            f"{index_name}: {len(df)} rows downloaded."
        )

    except Exception as e:

        print(
            f"{index_name}: ERROR - {e}"
        )


# ============================================================
# SAVE INDEX DATA TO SQL SERVER
# ============================================================

if not df_indices_final.empty:

    print(
        f"\nSaving {len(df_indices_final)} index rows to SQL Server..."
    )

    df_indices_final.to_sql(
        "Fact_Indices",
        engine,
        if_exists="append",
        index=False
    )

    print(
        "Index data saved successfully."
    )

else:

    print(
        "\nNo new index data to save."
    )


# ============================================================
# CLEAN OLD INDEX DATA
# ============================================================

print("\nCleaning old index data...")

with engine.begin() as conn:

    conn.execute(
        text(
            """
            DELETE FROM Fact_Indices
            WHERE Date < :start_date
            """
        ),
        {"start_date": start_date}
    )

print("Old index data cleaned.")


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n========================================")
print("ETL PROCESS FINISHED")
print("========================================")

print(f"Data start date: {start_date}")
print(f"Data end date:   {today}")

print(
    f"mWIG40 rows processed: {len(df_final)}"
)

print(
    f"Index rows processed:  {len(df_indices_final)}"
)

print("========================================")


input("\nPress Enter to exit...")
