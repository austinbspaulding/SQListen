-- presents every tag type that was not mapped to a dedicated table
-- this query can be useful for debugging with -p, but it will not generate a valid playlist
SELECT DISTINCT key FROM unmapped;