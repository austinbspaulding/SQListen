import argparse

argParser = argparse.ArgumentParser(
    prog = "SQListen",
    description = "A tool for querying your music",
    epilog = "As long as the first selected output column of a query contains filepaths, the query will create a valid playlist.",
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
    help="the directories to recursively search for songs",
    nargs="+",
)

parsed = argParser.parse_args()

print(parsed)