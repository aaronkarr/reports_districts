import pandas as pd
import numpy as np

pd.set_option({"display.max_rows": 100, "display.max_columns": 50})

filepath = "data/gift_designations_fy26.csv"
cols = [
    "ID",
    "GIFT_ID",
    # "FT_GIFT_ID",
    "GIFT_DATE",
    "GIFT_CUSTOM_FIELD_VALUES_JSON",
    "GIFT_DESIGNATION_ID",
    "CONVERTED_AMOUNT_DESIGNATED",
    # "DM_PROJECT_ID",
    "PROJECT_ID",
    "PROJECT_NAME",
    "PROJECT_TYPE",
    # "LOCATION",
    "PROJECT_CUSTOM_FIELD_VALUES_JSON",
    "CONTACT_ID",
    # "DM_CONTACT_ID",
    "CONTACT_NAME",
    "CONTACT_TYPE",
    "CONTACT_TAG_LIST",
    "CONTACT_CUSTOM_FIELD_VALUES_JSON",
    "PASSTHROUGH_CONTACT_ID",
    # "DM_PASSTHROUGH_CONTACT_ID",
    "PASSTHROUGH_CONTACT_NAME",
    "PASSTHROUGH_CONTACT_TYPE",
    "PASSTHROUGH_CONTACT_TAG_LIST",
    "PASSTHROUGH_CONTACT_CUSTOM_FIELD_VALUES_JSON",
    "GIFT_CREATED_AT_UTC",
]

drop_cols = [
    "GIFT_CUSTOM_FIELD_VALUES_JSON",
    "PROJECT_CUSTOM_FIELD_VALUES_JSON",
    "CONTACT_TAG_LIST",
    "CONTACT_CUSTOM_FIELD_VALUES_JSON",
    "PASSTHROUGH_CONTACT_TAG_LIST",
    "PASSTHROUGH_CONTACT_CUSTOM_FIELD_VALUES_JSON",
]


def load_df():
    df = pd.read_csv(filepath, usecols=cols)
    df["REVENUE_STREAM"] = add_custom_field(
        df.PROJECT_CUSTOM_FIELD_VALUES_JSON, "Revenue Stream"
    )
    df["SOFT_CREDIT_SELECTION"] = add_custom_field(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit"
    )
    df["SOFT_CREDIT_CHURCH"] = add_custom_field(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit Church"
    )
    df["CHURCH_CODE"] = add_custom_field(
        df.CONTACT_CUSTOM_FIELD_VALUES_JSON, "Church Code"
    )
    df["CHURCH_DISTRICT"] = tag_to_col(df.CONTACT_TAG_LIST, "District")
    df["ALLIANCE_CHURCH"] = df.CONTACT_TAG_LIST.str.contains(
        "alliance church", case=False
    )
    df.drop(columns=drop_cols, inplace=True)
    return df


def add_custom_field(custom_values_col, key):
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


def main():
    df = load_df()

    # print(
    #     df[df.SOFT_CREDIT_SELECTION != "Yes"][
    #         ["CONTACT_NAME", "SOFT_CREDIT_CHURCH"]
    #     ].value_counts()
    # )
    by_district = df.groupby(["CHURCH_DISTRICT", "CHURCH_CODE"])[
        ["CONVERTED_AMOUNT_DESIGNATED"]
    ].sum()
    # by_district.to_csv("out/by_district.csv")
    by_rev_stream = df.groupby(["REVENUE_STREAM"], dropna=False)[
        "CONVERTED_AMOUNT_DESIGNATED"
    ].sum()
    print(by_rev_stream)
    by_streamless_project = (
        df[df.REVENUE_STREAM.isna()]
        .groupby("PROJECT_NAME")["CONVERTED_AMOUNT_DESIGNATED"]
        .sum()
    )
    print(by_streamless_project)
    print("----------")
    print(df.columns)


if __name__ == "__main__":
    main()
