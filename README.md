# SQListen

SQListen is a tool for querying your music. It reads your mp3 metadata into a database, and then converts the resuts of queries into it to .m3u8 playlist files.

# Getting Started

make sure that you have python 3 installed, and then run `pip install -r requirements.txt` in the SQListen directory. After that, you can run SQListen by passing python the sqlisten.py script as an argument.

# Usage

The database schema and mapping is very customizable. If you wish to customize SQListen's behavior, please check out the [configuration](#configuration) section below.

Note that inspect_song.py is a provided script that helps you visualize how your music is getting mapped. Pass it a config file and a song and it will show the mapped values resulting from that song.

The basic usage for SQListen is as follows (this was taken from and can be viewed by passing -h or --help to the script)

`sqlisten.py [-h] [-db DATABASE] [-c CONFIG] [libraries ...]`

-db lets you optionally specify a database file to be created so that you can query it outside of SQListen should you wish. By default SQListen will create an in-memory database.

By default SQListen will load dbconfig.yaml as its config. -c lets you optionally override this to a different file.

libraries... is a list of any number of directories to crawl for songs. If none are provided, SQListen will attempt a search starting at the working directory.

After starting SQListen, it will use the provided values and immediately begin processing your music and feeding it into the database. After it finishes, it will let you run commands from a separate command line repeatedly until you close the program.

`[-h] [-q] [-p] files...`

passing -q will quit sqlisten.

-p will prevent saving playlists and will instead print their outputs to the console. Very helpful for debugging.

files... is a list of any number of files containing a SQLite query. SQListen takes the first selected column of a query's result and turns it into a .m3u8 playlist named after the file containing the query. Passing -p prevents the playlist generation and prints the queries' outputs to the console instead.

# Database Schema

SQListen's database schema is very simple. Most tables have only two columns: filePath and value. The former is the absolute path of a song on your computer and the latter is the value associated with that song. [The tables are defined in a config file that can be customized.](#configuration) Note that one song can generate more than one column in most tables. For example, if a song lists two artists, the artist table would have two rows with that song's filepath, each listing one of the artists. SQListen does set up two [special tables](#special-tables) that are uniqe.

# Configuration

SQListen uses a yaml file to configure various things about how it runs. The dbconfig.yaml in git is a working file that covers the bases of most music libraries, but it can be further extended.

The first item of the config defines the schema of the database. The first two items of the schema let you customize (only) the names of the two [special tables](#special-tables) that SQListen sets up. The third item is a list of table names mapped to the type affinity of its value column. SQLite will attempt to coerce the value of the data in this table to match this type. Setting up numerical tables where applicable makes doing numerical computations convenient.

The second item of the config file defines mappings from tags to a [parser](#parsers), to one or more tables. Usefully, explicitly handled tags will generate a row with a NULL value for songs that don't have a matching tag. Unmapped tags may not have any row for some songs.

# Special Tables

SQListen does set up two special tables. Their columns can't be customized, but you can rename them in the config file if you wish.

The first special table is the unmapped table, where tags that aren't explicitly mapped to other tables go. This is the only table with three columns. In addition to filePath and value, the unmapped table has a key column, which is the name of the tag that the value should be associated with.

The other special table is a duration table. SQListen will extract the length of an mp3 and store it here regardless of whether the duration is actually saved in the song metadata tags. This value is the number of seconds as a float.

# Parsers

SQListen provides 4 parsers at present:
 - The string parser is the default and fallback parser should an error occur. The string parser can handle anything as a string, but if a value is mapped to a table with a numerical type affinity, SQLite will still attempt to coerce it to the matching type. The string parser also respects multiple values in supported tags, and will insert a row for each value in the relevant table.
 - The fraction parser can handle optional fractions that show up in some tags. For example, the track number tag, "TRCK", can optionally have an appended forward slash and another number, representing the total number of tracks on the album. This tag lets you map both values to different tables as numbers, inserting a NULL to the denominator table when the second value is not present
 - The date parser attempts to parse dates from tags, and inserts them into the relevant table as the floating point representation of the Unix Epoch timestamp. This makes comparisons very easy, as they can be numeric. Additionally, the date parser will accept non-standard dates (such as just a year) and will set any undefined parts to the start of the respective time period. This enables tags with just a provided year to map to the first day of that year and still be able to be compared with more specific dates.
 - The skip parser maps a tag to no tables. It prevents its processing, which can speed up processing and clean up output. This is intended for use with attached image metadata, but nothing prevents it from being used elsewhere if you have other tags you want to keep out of your database.

# Extra Help

If you encounter a tag that you don't recognize, you can view the official list of ID3 tags (known formally as frames) here https://web.archive.org/web/20200806134515/https://id3.org/id3v2.4.0-frames

Note that TXXX is the "user defined text information frame", which allows information to be attached to an MP3 that doesn't have a special tag. Any TXXX frame on a song will be exposed as `TXXX:key` where key is an identifier for what that TXXX frame is encoding.

Also note that many frames can appear more than onces on a single song, and that many frames can encode several values with just one instance of a frame.