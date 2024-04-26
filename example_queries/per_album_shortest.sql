-- presents the shortest song from each album
SELECT
    filePath,
    duration,
    album
FROM (
    SELECT
        duration.filePath AS filePath,
        duration.value AS duration,
        album.value AS album
    FROM duration
    LEFT JOIN album
    on duration.filePath = album.filePath
    ORDER BY album.value, duration.value
)
GROUP BY album;