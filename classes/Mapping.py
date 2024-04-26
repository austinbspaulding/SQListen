from datetime import datetime
from typing import Any, List

from os.path import splitext

import mutagen.mp3

class Mapping:
    def __init__(self) -> None:
        self.mappedRows: List[Mapping.MappedRow] = []
        self.unmappedRows: List[Mapping.UnmappedRow] = []

    def addMappedRow(self, tableName: str, filePath: str, value: Any):
        self.mappedRows.append(Mapping.MappedRow(tableName, filePath, value))

    def addUnmappedRow(self, tableName: str, key: str, filePath: str, value: Any):
        self.unmappedRows.append(Mapping.UnmappedRow(tableName, key, filePath, value))

    class MappedRow:
        def __init__(self, tableName: str, filePath: str, value: Any):
            self.tableName = tableName
            self.filePath = filePath
            self.value = value

        def getTuple(self):
            return (self.filePath, self.value)

        def __str__(self):
            value = str(self.value)
            if self.value is None:
                value = "NULL"
            return f"{self.tableName:30.30} {self.filePath:50.50} {value:50.50}"
        
    class UnmappedRow:
        def __init__(self, tableName: str, key: str, filePath: str, value: Any):
            self.tableName = tableName
            self.key = key
            self.filePath = filePath
            self.value = value

        def getTuple(self):
            return (self.filePath, self.key, self.value)

        def __str__(self):
            value = str(self.value)
            if self.value is None:
                value = "NULL"
            return f"{self.tableName:30.30} {self.key:30.30} {self.filePath:50.50} {value:50.50}"

    def __str__(self):
        out = "mapped rows:\n"
        out += f"{'table':30.30} {'path':50.50} {'value':50.50}\n"
        for row in self.mappedRows:
            out += str(row) + "\n"
        
        out += "\n" "unmapped Rows:" "\n"
        out += f"{"table":30.30} {"key":30.30} {"path":50.50} {"value":50.50}\n"
        for row in self.unmappedRows:
            out += str(row) + "\n"

        return out

def __splitFraction(fraction: str):
    out: List[int | None] = list(map(int, fraction.split("/")))
    while len(out) < 2:
        out.append(None)

    return out

def __parseDateFrame(frame) -> List[str]:
    dates: List[str] = []
    for date in frame.text:
        kwargs = {}
        for key in "year month day hour minute second".split():
            attr = getattr(date, key)
            if attr is not None:
                kwargs[key] = attr
        
        for key in "month day".split():
            attr = kwargs.get(key)
            if attr is None:
                kwargs[key] = 1
        
        dates.append(str(datetime(**kwargs)))
    
    return dates

def mapFile(filePath: str, config: Any) -> Mapping:
    try:
        if (splitext(filePath)[1].lower() == ".mp3"):
            return __mapMP3(filePath, config)
    except BaseException as exc:
        if issubclass(type(exc), KeyboardInterrupt):  # allows ending the program while still catching any other exception below
            raise exc
        print(f'file "{filePath}" not fully processed due to error: {exc}')
    return Mapping()

def __mapMP3(filePath: str, config: Any) -> Mapping:
    mp3Config = config["filetypes"]["mp3"]
    out = Mapping()
    mp3 = mutagen.mp3.MP3(filePath)

    songDuration: float = mp3.info.length # type: ignore
    out.addMappedRow(config["schema"][1], filePath, songDuration)

    id3: ID3 = mp3.tags # type: ignore

    keys = set()

    for key in id3:
        keys.add(key)

    for key in mp3Config:
        keys.add(key)

    for key in keys:
        if key in mp3Config:
            parser = mp3Config[key].get("parser")
            map_to = mp3Config[key].get("map_to")
        else:
            parser = "default"
            map_to = config["schema"][0]

        frames = id3.getall(key)

        # insert null values into mapped tables where a song has no value
        if len(frames) == 0:
            if parser == "skip":
                pass
            elif parser == "fraction":
                for i in range(2):
                    out.addMappedRow(str(map_to[i]), filePath, None)
            else:
                out.addMappedRow(str(map_to), filePath, None)
            continue
        
        for frame in frames:
            try:
                if parser == "string":
                    for value in frame.text:
                        out.addMappedRow(str(map_to), filePath, str(value))
                elif parser == "fraction":
                    parts = __splitFraction(str(frame))
                    for i in range(2):
                        out.addMappedRow(str(map_to[i]), filePath, parts[i])
                elif parser == "date":
                    for date in __parseDateFrame(frame):
                        out.addMappedRow(str(map_to), filePath, date)
                elif parser == "skip":
                    continue
                else:
                    if parser != "default":
                        print(f'mp3 tag {key} has unrecognized parser "{parser}"')
                        print("using default parser")
                    try:
                        for value in frame.text:
                            out.addUnmappedRow(str(map_to), key, filePath, str(value))
                    except:
                        out.addUnmappedRow(str(map_to), key, filePath, str(frame))
            except BaseException as exc:
                print(f'error while processing key {key} of mp3 {filePath}: {exc}')
                print("attempting to insert it as a string")

                # makes it so that failed fractions insert the coerced string value into both intended tables
                if type(map_to) is not list:
                    map_to = [map_to]
                
                for table in map_to:

                    out.addMappedRow(table, filePath, str(frame)) # type: ignore
    return out