from datetime import datetime
import mutagen
import mutagen.id3
import mutagen.mp3
import yaml

from typing import List

def getConfig(configFileName: str):
    with open(configFileName) as stream:
        return yaml.safe_load(stream)

def typedFile(toOpen) -> None | mutagen.FileType: # type: ignore
    return mutagen.File(toOpen) # type: ignore

def getFrameValues(frame) -> List[str]:
    if issubclass(type(frame), mutagen.id3.NumericPartTextFrame): # type: ignore
        return [+frame]
    elif issubclass(type(frame), mutagen.id3.NumericTextFrame): # type: ignore
        return [+frame]
    elif issubclass(type(frame), mutagen.id3.TimeStampTextFrame): # type: ignore
        # return list(map(lambda x : x.text, frame.text))
        out: List[str] = []
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
            
            out.append(str(datetime(**kwargs)))
        return out
            
    elif issubclass(type(frame), mutagen.id3.TextFrame):  # type: ignore
        out = []
        for s in frame.text:
            # print(s)
            out.append(str(s))
        return out
        return list(map(str, frame.text)) # type: ignore
    # print(f"base: {type(frame)}")
    return [str(frame)]