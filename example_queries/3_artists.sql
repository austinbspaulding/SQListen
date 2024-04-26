-- presents all songs that have exactly 3 artists
SELECT
    filePath,
    group_concat(value, ', ') AS artists
FROM artist
GROUP BY filePath
HAVING COUNT(1) = 3
ORDER BY filePath;