import pandas as pd

gifts = pd.read_csv("data/gift_designations_2025.csv")
print(gifts.CONTACT_TYPE.value_counts())
print("----------")
districts_gifts = gifts[gifts.CONTACT_TYPE == "District"][
    ["GIFT_DATE", "CONTACT_NAME", "PROJECT_NAME", "CONVERTED_AMOUNT_DESIGNATED"]
]
print(districts_gifts.CONTACT_NAME.value_counts())
print("----------")
print(districts_gifts.CONVERTED_AMOUNT_DESIGNATED.sum())
