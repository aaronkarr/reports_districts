import pandas as pd
import numpy as np
import os
import sys

pd.set_option({"display.max_rows": 100, "display.max_columns": 50})

# SELECT [ cols ] FROM CURATED_DB.WRAPPERS.VW_GIFT_DESIGNATIONS
# WHERE GIFT_DATE >= TO_TIMESTAMP('2025-01-01');
if len(sys.argv) == 2:
    if os.path.exists(sys.argv[1]):
        gifts_filepath = sys.argv[1]
else:
    gifts_filepath = "data/gift_designations_2025.csv"


churches_filepath = "data/alliance_churches.csv"
# select PROJECT_ID from CURATED_DB.TRANSFORMS.PROJECTS_FEES_AND_EVENTS;
projects_filepath = "data/project_reporting_categories.csv"
output_filepath = "out/gifts_by_month.csv"

usecols = [
    "GIFT_DATE",
    "GIFT_DESIGNATION_ID",
    "CONVERTED_AMOUNT_DESIGNATED",
    "PROJECT_ID",
    "CONTACT_ID",
    "GIFT_CUSTOM_FIELD_VALUES_JSON",
    "CONTACT_TAG_LIST",
    "CONTACT_CUSTOM_FIELD_VALUES_JSON",
]

drop_cols = [
    "GIFT_CUSTOM_FIELD_VALUES_JSON",
    "CONTACT_TAG_LIST",
    "CONTACT_CUSTOM_FIELD_VALUES_JSON",
    "CONVERTED_AMOUNT_DESIGNATED",
    "CHURCH_CODE",
    "CONTACT_ID",
    "SOFT_CREDIT_SELECTION",
    "SOFT_CREDIT_CHURCH",
    "SOFT_CREDIT_CHURCH_CODE",
    "ALLIANCE_CHURCH",
]

dtypes = {
    "GIFT_DESIGNATION_ID": "str",
    "PROJECT_ID": "str",
    "CONTACT_ID": "str",
}


def load_gift_df() -> pd.DataFrame:
    df = pd.read_csv(
        gifts_filepath,
        parse_dates=["GIFT_DATE"],
        usecols=usecols,
        dtype=dtypes,
    )
    df["AMOUNT"] = df.CONVERTED_AMOUNT_DESIGNATED

    # Soft Credit data
    df["SOFT_CREDIT_SELECTION"] = add_custom_col(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit"
    ).eq("Yes")

    df["SOFT_CREDIT_CHURCH"] = add_custom_col(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit Church"
    )
    df["SOFT_CREDIT_CHURCH_CODE"] = df.SOFT_CREDIT_CHURCH.str.extract(r".*\[(.*)\]")

    # Church ID data
    df["CHURCH_CODE"] = add_custom_col(
        df.CONTACT_CUSTOM_FIELD_VALUES_JSON, "Church Code"
    )
    df["ALLIANCE_CHURCH"] = df.CONTACT_TAG_LIST.str.contains(
        "alliance church", case=False
    )

    # Calculated cols for grouping
    df["YEAR"] = df.GIFT_DATE.dt.year
    df["MONTH"] = df.GIFT_DATE.dt.month
    df["CREDIT_TO"] = add_credit_col(df)

    df.drop(columns=drop_cols, inplace=True)
    return df


def add_custom_col(custom_values_col, key) -> pd.Series:
    pattern = rf'.*"{key}":\s*"([^"]+)".*'
    # Add surrounding quotes to null in raw column to align with non-null string format
    null_quotes = custom_values_col.str.replace("null", '"null"')
    # Remove braces and newlines
    trimmed = null_quotes.str.replace(r"[\{\}\n]", "", regex=True)
    series = trimmed.str.replace(pattern, r"\1", regex=True)
    series = series.replace("null", np.nan)
    return series


def tag_to_col(custom_tags_col, key) -> pd.Series:
    pattern = rf'.*"{key}:\s*([^"]+)".*'
    untrimmed = custom_tags_col[custom_tags_col.str.contains(key)]
    # Remove brackets and newlines
    trimmed = untrimmed.str.replace(r"[\[\]\n]", "", regex=True)
    series = trimmed.str.replace(pattern, r"\1", regex=True)
    series = series.replace("null", np.nan)
    return series


def add_credit_col(gift_df) -> pd.Series:
    def get_credit_value(df) -> str:
        if df.ALLIANCE_CHURCH:
            return df.CHURCH_CODE
        if df.SOFT_CREDIT_SELECTION:
            return df.SOFT_CREDIT_CHURCH_CODE
        return "no one"

    series = gift_df.apply(get_credit_value, axis=1)
    return series


def merge_and_group_by_month(gifts_df, churches_df, projects_df) -> pd.DataFrame:
    merged = pd.merge(gifts_df, projects_df, how="left", on="PROJECT_ID")
    gifts_by_month = (
        merged[
            [
                "YEAR",
                "MONTH",
                "CREDIT_TO",
                "CATEGORY",
                "AMOUNT",
            ]
        ]
        .groupby(
            [
                "YEAR",
                "MONTH",
                "CATEGORY",
                "CREDIT_TO",
            ],
            as_index=False,
            dropna=False,
        )
        .agg({"AMOUNT": "sum"})
    )

    gifts_by_month["YTD_AMOUNT"] = (
        gifts_by_month.groupby(["YEAR", "CATEGORY", "CREDIT_TO"])["AMOUNT"]
        .cumsum()
        .round(2)
    )
    gifts_by_month["AMOUNT_LAST_YEAR"] = gifts_by_month.groupby(
        ["CATEGORY", "CREDIT_TO"]
    )["AMOUNT"].shift(12)
    gifts_by_month["YTD_LAST_YEAR"] = gifts_by_month.groupby(["CATEGORY", "CREDIT_TO"])[
        "YTD_AMOUNT"
    ].shift(12)

    # join church info
    # TODO include churches without contributions
    gifts_by_month = pd.merge(
        gifts_by_month,
        churches_df,
        how="left",
        left_on="CREDIT_TO",
        right_on="CHURCH_CODE",
    )
    gifts_by_month.drop(columns="CONTACT_ID", inplace=True)

    return gifts_by_month


def generate_reports(gifts_by_month_df):
    this_year = gifts_by_month_df.YEAR.max()
    months = gifts_by_month_df[gifts_by_month_df["YEAR"] == this_year].MONTH.unique()
    districts = list(gifts_by_month_df.DISTRICT_NAME.dropna().unique())
    associations = list(gifts_by_month_df.ASSOCIATION_NAME.dropna().unique())
    for month in months:
        gifts_this_month = gifts_by_month_df[gifts_by_month_df.MONTH == month]
        district_comparison = (
            gifts_this_month[
                [
                    "DISTRICT_NAME",
                    "CATEGORY",
                    "AMOUNT",
                    "YTD_AMOUNT",
                    "AMOUNT_LAST_YEAR",
                    "YTD_LAST_YEAR",
                ]
            ]
            .groupby(["DISTRICT_NAME", "CATEGORY"])
            .sum()
        )
        district_comparison_name = f"out/District Comparison {month}-{this_year}.csv"
        district_comparison.to_csv(district_comparison_name)
        association_comparison = (
            gifts_this_month[
                [
                    "ASSOCIATION_NAME",
                    "CATEGORY",
                    "AMOUNT",
                    "YTD_AMOUNT",
                    "AMOUNT_LAST_YEAR",
                    "YTD_LAST_YEAR",
                ]
            ]
            .groupby(["ASSOCIATION_NAME", "CATEGORY"])
            .sum()
        )
        assocation_comparison_name = (
            f"out/Assocation Comparison {month}-{this_year}.csv"
        )
        association_comparison.to_csv(assocation_comparison_name)
        for district in districts:
            print("---------")
            print(district)
            print("---------")
            district_summary = gifts_by_month_df[
                gifts_by_month_df["DISTRICT_NAME"].str.startswith(district)
                & gifts_by_month_df["MONTH"]
                == month
            ]
            district_summary_name = (
                f"out/Giving Summary - {district} {month}-{this_year}.csv"
            )
            district_summary.to_csv(district_summary_name)
        for association in associations:
            association_summary = gifts_by_month_df[
                gifts_by_month_df["ASSOCIATION_NAME"].str.startswith(association)
                & gifts_by_month_df["MONTH"]
                == month
            ]
            association_summary_name = (
                f"out/Giving Summary - {association} {month}-{this_year}.csv"
            )
            association_summary.to_csv(association_summary_name)


def main() -> None:
    print("Loading dataframes from input...\n")
    gifts = load_gift_df()

    churches = pd.read_csv(churches_filepath)
    projects = pd.read_csv(projects_filepath, dtype={"PROJECT_ID": "string"})

    gifts_by_month = merge_and_group_by_month(gifts, churches, projects)
    print("Loaded!\n")
    print(gifts_by_month.info())
    print("----------")
    user_input = input("Save output file? [y/N]")
    if user_input == "y":
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        gifts_by_month.to_csv(output_filepath)
        print("File saved!")
    else:
        print("All that for nothing")

    user_input = input("Generate reports? [y/N] ")
    if user_input == "y":
        generate_reports(gifts_by_month)
        print("Reports generated!")
    else:
        print("Exiting.")


if __name__ == "__main__":
    main()
