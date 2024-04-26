import argparse
import sqlite3
import os
import os.path

from classes.TagDB import TagDB
import argparse

from os.path import isfile, splitext

def next_file(path):
    if not isfile(path):
        return path
    else:
        i = 1
        prefix, type = splitext(path)
        while isfile(f"{prefix}_{i}{type}"):
            i += 1
        return f"{prefix}_{i}{type}"

argParser = argparse.ArgumentParser(
    description = "A tool for querying your music",
)

argParser.add_argument(
    "-db",
    "--database",
    default=":memory:",
    help="By default, SQListen will created an in-memory database. Passing this argument will override that and create a database on disk"
)

argParser.add_argument(
    "-c",
    "--config",
    default=None,
    help="The config file for the database to use. This defaults to dbconfig.yaml in the SQListen directory"
)

argParser.add_argument(
    "libraries",
    help="The directories to recursively search for songs. If none are provided, the working directory will be searched",
    nargs="*",
)

interactiveParser = argparse.ArgumentParser(
    usage="[-h] [-q] [-p] files...",
    epilog = "SQListen will attempt to find a selected row called filePath for use in playlist creation. "
    + "If it fails, it will use the first column that contains a valid file path",
    add_help=False
)

interactiveParser.add_argument(
    "-h",
    "--help",
    help="shows this help message",
    action="store_true",
)

interactiveParser.add_argument(
    "-q",
    "--quit",
    help="closes SQListen",
    action="store_true",
)

interactiveParser.add_argument(
    "-p",
    "--print",
    action="store_true",
    help="disables saving and prints the output of queries to stdout instead",
)

interactiveParser.add_argument(
    "files",
    help="the files containing the sql queries to run on the database",
    nargs="*",
)

if __name__ == "__main__":
    try:
        parsed = argParser.parse_args()

        if parsed.database != ":memory:":
            if os.path.splitext(parsed.database)[1].lower() != ".db":
                print("use the db extension for database files")
                exit(1)
            if os.path.isfile(parsed.database):
                os.remove(parsed.database)

        if parsed.config is None:
            parsed.config = os.path.join(__file__, "../dbconfig.yaml")

        if len(parsed.libraries) == 0:
            parsed.libraries.append(os.getcwd())

        db = TagDB(parsed.config, parsed.database)

        for dir in parsed.libraries:
            db.addLibrary(dir)

        interactiveParser.print_usage()
        while True:
            try:
                parsed = interactiveParser.parse_args(input().split())
            except SystemExit:
                continue #don't allow the parser to exit the program

            if parsed.help:
                interactiveParser.print_help()
                continue

            if parsed.quit:
                break

            if len(parsed.files) == 0:
                print("you must include at least one file")
                interactiveParser.print_help()
                continue

            #do error checking up front to make sure that an error message
            #doesn't get lost during a print output while processing multiple files
            badFile = False
            for fName in parsed.files:
                if not isfile(fName):
                    print(f'"{fName}" is not a file')
                    badFile = True
            if badFile:
                continue

            for fName in parsed.files:
                with open(fName) as f:
                    try:
                        query = f.read()
                    except Exception as e:
                        print(f'error reading {fName}: {e}')
                        continue

                print(f"running query {fName}")

                try:
                    out = db.queryDB(query)
                except sqlite3.DatabaseError as e:
                    print(f'error with query: {e}')
                    continue

                print(f'"{fName}" generated {len(out)} rows')

                if len(out) == 0:
                    print("because no rows were generated, no playlist will be created.")
                    continue

                if parsed.print:
                    for i, row in enumerate(out):
                        print(f"\nrow {i + 1}:")
                        for col in row.keys():
                            print(f"{col}: {row[col]}")
                    continue

                fileCol = -1
                try:
                    fileCol = out[0].keys().index("filePath")
                except ValueError:
                    for i, col in enumerate(out[0]):
                        if isfile(col):
                            fileColIndex = i
                            break

                if fileCol == -1:
                    print("no obvious filenames were selected. output playlist is probably invalid.")
                    fileCol = 0

                # get the extensionless name of the query file
                outFile = os.path.split(os.path.splitext(fName)[0])[1]

                outFile = next_file(outFile + ".m3u8")

                with open(outFile, mode="w", encoding="utf-8") as f:
                    print(f'saving to "{outFile}"\n')
                    delim = ""
                    for row in out:
                        f.write(delim + row[fileCol])
                        delim = "\n"

    except Exception as exc:
        if 'db' in globals():
            db.closeDB()  # type: ignore
        raise exc