USE [mWIG40_Portfolio]
GO

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

CREATE TABLE [dbo].[DimCompany]
(
    [CompanyKey] [int] IDENTITY(1,1) NOT NULL,
    [Ticker] [varchar](20) NOT NULL,
    [CompanyName] [varchar](150) NOT NULL,
    [Sector] [varchar](100) NULL,
    [Industry] [varchar](100) NULL,
    [City] [varchar](100) NULL,
    [Region] [varchar](100) NULL,
    [Country] [varchar](100) NULL,
    [FoundedYear] [smallint] NULL,
    [GPWListingYear] [smallint] NULL,
    [Market] [varchar](50) NULL,
    [IndexName] [varchar](50) NULL,
    [WebsiteURL] [varchar](255) NULL,
    [LogoURL] [varchar](500) NULL,

    CONSTRAINT [PK_DimCompany]
        PRIMARY KEY CLUSTERED
        ([CompanyKey] ASC),

    CONSTRAINT [UQ_DimCompany_Ticker]
        UNIQUE NONCLUSTERED
        ([Ticker] ASC)
)
GO


CREATE TABLE [dbo].[DimDate]
(
    [DateKey] [int] NOT NULL,
    [FullDate] [date] NOT NULL,
    [Year] [int] NOT NULL,
    [Quarter] [int] NOT NULL,
    [Month] [int] NOT NULL,
    [MonthName] [nvarchar](20) NOT NULL,
    [WeekOfYear] [int] NOT NULL,
    [DayOfMonth] [int] NOT NULL,
    [DayOfWeek] [int] NOT NULL,
    [DayName] [nvarchar](20) NOT NULL,
    [IsWeekend] [bit] NOT NULL,
    [IsTradingDay] [bit] NOT NULL,

    CONSTRAINT [PK_DimDate]
        PRIMARY KEY CLUSTERED
        ([DateKey] ASC),

    CONSTRAINT [UQ_DimDate_FullDate]
        UNIQUE NONCLUSTERED
        ([FullDate] ASC)
)
GO


CREATE TABLE [dbo].[DimTransactionType]
(
    [TransactionTypeKey] [int] NOT NULL,
    [TransactionTypeName] [varchar](20) NOT NULL,

    CONSTRAINT [PK_DimTransactionType]
        PRIMARY KEY CLUSTERED
        ([TransactionTypeKey] ASC),

    CONSTRAINT [UQ_DimTransactionType_Name]
        UNIQUE NONCLUSTERED
        ([TransactionTypeName] ASC)
)
GO


-- ============================================================
-- FACT TABLES
-- ============================================================

CREATE TABLE [dbo].[Fact_StockPrices]
(
    [Date] [datetime] NULL,
    [Close] [float] NULL,
    [High] [float] NULL,
    [Low] [float] NULL,
    [Open] [float] NULL,
    [Volume] [bigint] NULL,
    [Ticker] [varchar](20) NOT NULL,
    [IndexName] [varchar](max) NULL,

    CONSTRAINT [UQ_FactStockPrices_Ticker_Date]
        UNIQUE NONCLUSTERED
        ([Ticker] ASC, [Date] ASC)
)
GO


CREATE TABLE [dbo].[Fact_Indices]
(
    [Date] [datetime] NULL,
    [Close] [float] NULL,
    [IndexName] [varchar](50) NOT NULL,

    CONSTRAINT [UQ_FactIndices_IndexName_Date]
        UNIQUE NONCLUSTERED
        ([IndexName] ASC, [Date] ASC)
)
GO


CREATE TABLE [dbo].[Fact_Transactions]
(
    [TransactionID] [int] IDENTITY(1,1) NOT NULL,
    [Date] [date] NOT NULL,
    [Ticker] [varchar](20) NOT NULL,
    [TransactionTypeKey] [int] NOT NULL,
    [Quantity] [decimal](18,4) NOT NULL,
    [Price] [decimal](18,4) NOT NULL,
    [Commission] [decimal](18,4) NOT NULL
        CONSTRAINT [DF_FactTransactions_Commission] DEFAULT ((0)),

    CONSTRAINT [PK_Fact_Transactions]
        PRIMARY KEY CLUSTERED
        ([TransactionID] ASC)
)
GO


CREATE TABLE [dbo].[Fact_Dividends]
(
    [DividendID] [int] IDENTITY(1,1) NOT NULL,
    [Date] [date] NOT NULL,
    [Ticker] [varchar](20) NOT NULL,
    [DividendPerShare] [decimal](18,4) NOT NULL,
    [Shares] [decimal](18,4) NOT NULL,
    [TotalDividend] AS ([DividendPerShare] * [Shares]) PERSISTED,
    [RecordDate] [date] NOT NULL,

    CONSTRAINT [PK_Fact_Dividends]
        PRIMARY KEY CLUSTERED
        ([DividendID] ASC)
)
GO


-- ============================================================
-- CONFIGURATION TABLE
-- ============================================================

CREATE TABLE [dbo].[PortfolioSettings]
(
    [Date] [date] NOT NULL,
    [Type] [varchar](50) NOT NULL,
    [Amount] [decimal](18,2) NOT NULL
)
GO


-- ============================================================
-- FOREIGN KEYS
-- ============================================================

ALTER TABLE [dbo].[Fact_Dividends]
    WITH CHECK ADD CONSTRAINT [FK_FactDividends_Company]
    FOREIGN KEY ([Ticker])
    REFERENCES [dbo].[DimCompany] ([Ticker])
GO

ALTER TABLE [dbo].[Fact_Dividends]
    CHECK CONSTRAINT [FK_FactDividends_Company]
GO


ALTER TABLE [dbo].[Fact_Transactions]
    WITH CHECK ADD CONSTRAINT [FK_FactTransactions_Company]
    FOREIGN KEY ([Ticker])
    REFERENCES [dbo].[DimCompany] ([Ticker])
GO

ALTER TABLE [dbo].[Fact_Transactions]
    CHECK CONSTRAINT [FK_FactTransactions_Company]
GO


ALTER TABLE [dbo].[Fact_Transactions]
    WITH CHECK ADD CONSTRAINT [FK_FactTransactions_TransactionType]
    FOREIGN KEY ([TransactionTypeKey])
    REFERENCES [dbo].[DimTransactionType] ([TransactionTypeKey])
GO

ALTER TABLE [dbo].[Fact_Transactions]
    CHECK CONSTRAINT [FK_FactTransactions_TransactionType]
GO
