import pandas as pd
import numpy as np

pd.set_option({"display.max_rows": 100, "display.max_columns": 50})

filepath = "data/gift_designations_fy26.csv"


def load_df():
    df = pd.read_csv(filepath)
    df["REVENUE_STREAM"] = add_custom_field(
        df.PROJECT_CUSTOM_FIELD_VALUES_JSON, "Revenue Stream"
    )
    df["SOFT_CREDIT_SELECTION"] = add_custom_field(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit"
    )
    df["SOFT_CREDIT_CHURCH"] = add_custom_field(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit Church"
    )
    df["CHURCH_DISTRICT"] = tag_to_col(df.CONTACT_TAG_LIST, "District")
    df["ALLIANCE_CHURCH"] = df.CONTACT_TAG_LIST.str.contains(
        "alliance church", case=False
    )
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
    print("------")
    print(df.CHURCH_DISTRICT.value_counts())
    print("------")
    print(df[["ALLIANCE_CHURCH", "CONTACT_TYPE"]].value_counts())


if __name__ == "__main__":
    main()
