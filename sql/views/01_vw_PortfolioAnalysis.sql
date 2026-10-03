USE [mWIG40_Portfolio]
GO

CREATE VIEW [dbo].[vw_PortfolioAnalysis]
AS

WITH Transactions AS
(
    SELECT
        T.TransactionID,
        T.Date,
        T.Ticker,
        C.CompanyName,
        C.Sector,
        TT.TransactionTypeName AS TransactionType,
        T.Quantity,
        T.Price,
        T.Commission,

        -- Gross transaction value
        T.Quantity * T.Price AS GrossValue,

        -- Change in number of shares
        CASE
            WHEN T.TransactionTypeKey = 1
                THEN T.Quantity
            WHEN T.TransactionTypeKey = 2
                THEN -T.Quantity
        END AS ShareChange,

        -- Cash flow impact
        CASE
            WHEN T.TransactionTypeKey = 1
                THEN -(T.Quantity * T.Price) - T.Commission
            WHEN T.TransactionTypeKey = 2
                THEN (T.Quantity * T.Price) - T.Commission
        END AS CashImpact

    FROM Fact_Transactions T

    LEFT JOIN DimCompany C
        ON T.Ticker = C.Ticker

    LEFT JOIN DimTransactionType TT
        ON T.TransactionTypeKey = TT.TransactionTypeKey
),

Analysis AS
(
    SELECT
        *,

        -- Cumulative number of shares held
        SUM(ShareChange) OVER
        (
            PARTITION BY Ticker
            ORDER BY Date, TransactionID
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS SharesHeld,

        -- Cumulative portfolio cash flow
        SUM(CashImpact) OVER
        (
            ORDER BY Date, TransactionID
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS CumulativeCashFlow,

        -- Previous transaction price
        LAG(Price) OVER
        (
            PARTITION BY Ticker
            ORDER BY Date, TransactionID
        ) AS PreviousTransactionPrice

    FROM Transactions
)

SELECT
    *,
    Price - PreviousTransactionPrice
        AS PriceChangeFromPreviousTransaction

FROM Analysis;
GO
