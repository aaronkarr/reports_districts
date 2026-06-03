import pandas as pd
import numpy as np

pd.set_option({"display.max_rows": 100, "display.max_columns": 50})

gifts_filepath = "data/gift_designations_2025.csv"
churches_filepath = "data/alliance_churches.csv"
projects_filepath = "data/project_reporting_categories.csv"

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


def load_gift_df():
    df = pd.read_csv(
        gifts_filepath,
        parse_dates=["GIFT_DATE"],
        usecols=usecols,
        dtype=dtypes,
    )
    df["AMOUNT"] = df.CONVERTED_AMOUNT_DESIGNATED
    # df["REVENUE_STREAM"] = add_custom_field(
    #     df.PROJECT_CUSTOM_FIELD_VALUES_JSON, "Revenue Stream"
    # )
    df["SOFT_CREDIT_SELECTION"] = add_custom_col(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit"
    ).eq("Yes")
    df["SOFT_CREDIT_CHURCH"] = add_custom_col(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit Church"
    )
    df["SOFT_CREDIT_CHURCH_CODE"] = df.SOFT_CREDIT_CHURCH.str.extract(r".*\[(.*)\]")
    df["CHURCH_CODE"] = add_custom_col(
        df.CONTACT_CUSTOM_FIELD_VALUES_JSON, "Church Code"
    )
    # df["CHURCH_DISTRICT"] = tag_to_col(df.CONTACT_TAG_LIST, "District")
    df["ALLIANCE_CHURCH"] = df.CONTACT_TAG_LIST.str.contains(
        "alliance church", case=False
    )
    df["YEAR"] = df.GIFT_DATE.dt.year
    df["MONTH"] = df.GIFT_DATE.dt.month
    df["CREDIT_TO"] = add_credit_col(df)

    df.drop(columns=drop_cols, inplace=True)
    return df


def add_custom_col(custom_values_col, key):
    pattern = rf'.*"{key}":\s*"([^"]+)".*'
    # Add surrounding quotes to null in raw column to align with non-null string format
    null_quotes = custom_values_col.str.replace("null", '"null"')
    # Remove braces and newlines
    trimmed = null_quotes.str.replace(r"[\{\}\n]", "", regex=True)
    series = trimmed.str.replace(pattern, r"\1", regex=True)
    series = series.replace("null", np.nan)
    return series


def tag_to_col(custom_tags_col, key):
    pattern = rf'.*"{key}:\s*([^"]+)".*'
    untrimmed = custom_tags_col[custom_tags_col.str.contains(key)]
    # Remove brackets and newlines
    trimmed = untrimmed.str.replace(r"[\[\]\n]", "", regex=True)
    series = trimmed.str.replace(pattern, r"\1", regex=True)
    series = series.replace("null", np.nan)
    return series


def add_credit_col(gift_df):
    def get_credit_value(df):
        if df.ALLIANCE_CHURCH:
            return df.CHURCH_CODE
        if df.SOFT_CREDIT_SELECTION:
            return df.SOFT_CREDIT_CHURCH_CODE
        return "no one"

    series = gift_df.apply(get_credit_value, axis=1)
    return series


def merge_and_group_by_month(gifts_df, churches_df, projects_df):
    merged = pd.merge(gifts_df, projects_df, how="left", on="PROJECT_ID")
    gifts_by_month = (
        merged[
            [
                "YEAR",
                "MONTH",
                "CREDIT_TO",
                # "CHURCH_NAME",
                # "CHURCH_CODE",
                # "CHURCH_STATUS",
                # "DISTRICT_NAME",
                # "ASSOCIATION_NAME",
                "AMOUNT",
                "CATEGORY",
            ]
        ]
        .groupby(
            [
                "YEAR",
                "MONTH",
                "CREDIT_TO",
                # "CHURCH_NAME",
                # "CHURCH_CODE",
                # "CHURCH_STATUS",
                # "DISTRICT_NAME",
                # "ASSOCIATION_NAME",
                "AMOUNT",
                "CATEGORY",
            ],
            as_index=False,
            dropna=False,
        )
        .agg({"AMOUNT": "sum"})
    )
    gifts_by_month = pd.merge(
        gifts_by_month,
        churches_df,
        how="outer",
        left_on="CREDIT_TO",
        right_on="CHURCH_CODE",
    )
    # gifts_by_month = gifts_by_month.astype({"MONTH": "int", "YEAR": "int"})
    # print(gifts_by_category[gifts_by_category.CATEGORY.isna()])
    # gifts_by_month.CREDIT_TO.rename("CHURCH_CODE")
    return gifts_by_month


# def generate_reports(gifts_by_month_df):
#         for month in gifts_by_month_df.MONTH:
#             for district in gifts_by_month_df.DISTRICT_NAME:


def main():
    gifts = load_gift_df()

    churches = pd.read_csv(churches_filepath)
    projects = pd.read_csv(projects_filepath, dtype={"PROJECT_ID": "string"})

    gifts_by_month = merge_and_group_by_month(gifts, churches, projects)

    # gifts_by_month = pd.merge(
    #     churches,
    #     gifts_by_month,
    #     how="outer",
    #     left_on="CHURCH_CODE",
    #     right_on="CREDIT_TO",
    # )
    # gifts_by_month = gifts_by_month.merge(projects, how="left", on=["PROJECT_ID"])

    # gifts_by_month.to_csv("out/gifts_by_month_with_cat.csv")
    print(gifts.info())
    print("--------")
    print(gifts_by_month.info())
    print("--------")
    print("--------")
    print(f"gifts total:          {gifts.AMOUNT.sum()}")
    # print(f"merged total:         {merged.AMOUNT.sum()}")
    print(f"gifts_by_month total: {gifts_by_month.AMOUNT.sum()}")
    gifts_by_month.to_csv("out/gifts_by_month.csv")
    print("--------")
    print(
        gifts_by_month[
            gifts_by_month.CATEGORY.isna() & gifts_by_month.AMOUNT > 0
        ].head()
    )


if __name__ == "__main__":
    main()
