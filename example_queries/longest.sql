--presents the 15 longest songs in your library
SELECT filePath, value
FROM duration
ORDER BY value DESC
LIMIT 15;