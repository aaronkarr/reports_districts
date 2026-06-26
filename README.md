Sample query for input file:

```
SELECT
    GIFT_DATE,
    GIFT_DESIGNATION_ID,
    CONVERTED_AMOUNT_DESIGNATED,
    PROJECT_ID,
    CONTACT_ID,
    GIFT_CUSTOM_FIELD_VALUES_JSON,
    CONTACT_TAG_LIST,
    CONTACT_CUSTOM_FIELD_VALUES_JSON
FROM CURATED_DB.WRAPPERS.VW_GIFT_DESIGNATIONS
    WHERE GIFT_DATE >= TO_TIMESTAMP('2025-01-01');
```
Also required:
- Alliance churches with Contact ID, Church Code, District, Association
- All projects with Project Code and Category



main.py accepts an argument for input csv file, defaulted to "data/gift_designations_2025.csv".

Reports output to 'out/' created/found in cwd.
- Gifts_by_month file contains sum of giving by month for every month in the most recent year in the source, grouped by financial engagement category, church, and credit type.
- Report files include district comparison, district summaries, and association summaries for each month in the most recent year

TODO: Include all Alliance churches, even if there are no giving records associated
TODO: Review inclusion criteria for churches with multiple membership in district/association 
