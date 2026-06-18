"""XBRL concept -> clean line-item map.

First concept in `concepts` that has data wins (fallbacks handle reporting
differences across companies/years). `kind` drives the parse rule:
  - 'duration' facts span a period (income / cash-flow) -> require a full year.
  - 'instant'  facts are a point in time (balance sheet)  -> taken at year-end.

This map is the contract the golden test pins. Changing it can change numbers
users see, so treat edits as data changes, not cosmetics.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LineItemSpec:
    statement_type: str  # 'income' | 'balance' | 'cash_flow'
    line_item: str
    concepts: tuple[str, ...]
    kind: str  # 'duration' | 'instant'


LINE_ITEMS: tuple[LineItemSpec, ...] = (
    # --- Income statement (duration) ---
    LineItemSpec(
        "income",
        "Revenue",
        (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        ),
        "duration",
    ),
    LineItemSpec(
        "income",
        "CostOfRevenue",
        ("CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"),
        "duration",
    ),
    LineItemSpec("income", "GrossProfit", ("GrossProfit",), "duration"),
    LineItemSpec("income", "OperatingIncome", ("OperatingIncomeLoss",), "duration"),
    LineItemSpec("income", "NetIncome", ("NetIncomeLoss",), "duration"),
    # --- Balance sheet (instant) ---
    LineItemSpec("balance", "TotalAssets", ("Assets",), "instant"),
    LineItemSpec("balance", "CurrentAssets", ("AssetsCurrent",), "instant"),
    LineItemSpec("balance", "TotalLiabilities", ("Liabilities",), "instant"),
    LineItemSpec("balance", "CurrentLiabilities", ("LiabilitiesCurrent",), "instant"),
    LineItemSpec(
        "balance",
        "StockholdersEquity",
        (
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ),
        "instant",
    ),
    LineItemSpec(
        "balance",
        "CashAndEquivalents",
        ("CashAndCashEquivalentsAtCarryingValue",),
        "instant",
    ),
    # --- Cash flow (duration) ---
    LineItemSpec(
        "cash_flow",
        "OperatingCashFlow",
        (
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ),
        "duration",
    ),
    LineItemSpec(
        "cash_flow",
        "InvestingCashFlow",
        (
            "NetCashProvidedByUsedInInvestingActivities",
            "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
        ),
        "duration",
    ),
    LineItemSpec(
        "cash_flow",
        "FinancingCashFlow",
        (
            "NetCashProvidedByUsedInFinancingActivities",
            "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
        ),
        "duration",
    ),
    LineItemSpec(
        "cash_flow",
        "CapitalExpenditures",
        ("PaymentsToAcquirePropertyPlantAndEquipment",),
        "duration",
    ),
)

# Display order per statement for the company page.
STATEMENT_ORDER: tuple[str, ...] = ("income", "balance", "cash_flow")
