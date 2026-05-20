import pandas as pd

pd.set_option({"display.max_rows": 100, "display.max_columns": 50})

filepath = "data/gift_designations_fy26.csv"


def load_df():
    df = pd.read_csv(filepath)
    # df["REVENUE_STREAM"] = df.PROJECT_CUSTOM_FIELD_VALUES_JSON.str.replace(
    #     r'[\{\}"\n]', "", regex=True
    # )
    # df.REVENUE_STREAM = df.REVENUE_STREAM.str.replace(
    #     r".*Revenue Stream: (\w+)", r"\1", regex=True
    # )

    return df


def add_custom_field(custom_values_col, key):
    pattern = rf".*{key}: (\w+)"
    # repl = r"\1"
    trimmed = custom_values_col.str.replace(r'[\{\}"\n]', "", regex=True)
    series = trimmed.str.replace(pattern, r"\1", regex=True)
    return series


def main():
    df = load_df()
    df["REVENUE_STREAM"] = add_custom_field(
        df.PROJECT_CUSTOM_FIELD_VALUES_JSON, "Revenue Stream"
    )
    df["SOFT_CREDIT_SELECTION"] = add_custom_field(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit"
    )
    df["SOFT_CREDIT_CHURCH"] = add_custom_field(
        df.GIFT_CUSTOM_FIELD_VALUES_JSON, "Soft Credit Church"
    )

    print(df.REVENUE_STREAM.value_counts())
    print(df.SOFT_CREDIT_SELECTION.value_counts())
    print(df.SOFT_CREDIT_CHURCH.value_counts())


if __name__ == "__main__":
    main()
