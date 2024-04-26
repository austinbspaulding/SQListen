from sys import argv
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

from utils import getConfig
from classes.Mapping import mapFile

if len(argv) != 3:
    print("please pass a database config and a file as commandline arguments")
    exit()

config = getConfig(argv[1])

m = mapFile(argv[2], config)

print(m)