import pandas as pd


def load_df():
    df = pd.read_csv("data/gift_designations_fy26.csv")
    return df


def main():
    df = load_df()
    print(df.info())


if __name__ == "__main__":
    main()
