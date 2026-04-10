# Top 10 Cuisine Types Query Results

**Table:** `ubereats_dev.bronze.mongo_items`
**Query Date:** 2025-12-03

## Results

| Rank | Cuisine Type | Count |
|------|--------------|-------|
| 1    | Italian      | 7,180 |
| 2    | Mexican      | 7,177 |
| 3    | Japanese     | 7,083 |
| 4    | Chinese      | 7,072 |
| 5    | Indian       | 7,048 |
| 6    | American     | 6,995 |
| 7    | French       | 6,942 |

## Summary

The query returned **7 distinct cuisine types** from the `ubereats_dev.bronze.mongo_items` table. The top cuisine type is **Italian** with 7,180 items, followed closely by **Mexican** with 7,177 items.

## Query Details

```sql
SELECT
    cuisine_type,
    COUNT(*) as count
FROM ubereats_dev.bronze.mongo_items
WHERE cuisine_type IS NOT NULL
GROUP BY cuisine_type
ORDER BY count DESC
LIMIT 10
```

## Notes

- Connection: Databricks Connect (serverless)
- Query executed successfully on first attempt
- All cuisine types had non-null values
