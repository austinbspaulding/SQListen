from datetime import datetime
import os
import sqlite3
from typing import Any, Dict, List, Tuple
import mutagen
import mutagen.mp3

from multiprocessing import Pool

from mutagen.mp3 import MP3
from mutagen.id3 import ID3

from classes.Mapping import Mapping, mapFile

from utils import getConfig


class TagDB:

    config: Any
    conn: sqlite3.Connection
    dbName: str

    def __init__(self, configFileName: str, dbName: str | None = None):
        self.config = getConfig(configFileName)

        if dbName is None:
            self.dbName = ":memory:"
        else:
            self.dbName = dbName
        
        self.conn = sqlite3.connect(self.dbName)
        self.conn.row_factory = sqlite3.Row

        # handle default table
        sql = f"""
            CREATE TABLE {self.config["schema"][0]} (
                filePath TEXT,
                key TEXT,
                value TEXT,
                PRIMARY KEY (filePath, key, value)
            );
        """
        self.queryDB(sql)

        def createTagTable(tableName: str, valueType: str):
            sql = f"""
                CREATE TABLE {tableName} (
                    filePath TEXT,
                    value {valueType},
                    PRIMARY KEY (filePath, value)
                );
            """
            self.conn.execute(sql)

        # handle duration table
        createTagTable(self.config["schema"][1], "REAL")

        for key in self.config["schema"][2]:
            val = self.config["schema"][2][key]
            createTagTable(key, val) # type: ignore

        self.conn.commit()

    def __addMappings(self, mappings: List[Mapping]):
        unmappedRows: List[Tuple[str, str, Any]] = []
        mappedRows: Dict[str, List[Tuple[str, Any]]] = {}

        for mapping in mappings:
            for uRow in mapping.unmappedRows:
                unmappedRows.append(uRow.getTuple())

            for mRow in mapping.mappedRows:
                if mappedRows.get(mRow.tableName, None) is None:
                    mappedRows[mRow.tableName] = []
                mappedRows[mRow.tableName].append(mRow.getTuple())

        self.__insertIntoDefaultTable(unmappedRows)

        for key in mappedRows:
            self.__insertIntoTagTable(key, mappedRows[key])
                
    def __insertIntoDefaultTable(self, rows: List[Tuple[str, str, Any]]):
        sql = f"""
            INSERT INTO {self.config["schema"][0]}
                ( filePath, key, value )
            VALUES
                ( ? , ?, ? )
            ;
        """

        cursor = self.conn.cursor()
        cursor.executemany(sql, rows)
        cursor.connection.commit()
        cursor.close()

    def __insertIntoTagTable(self, tableName: str, rows: List[Tuple[str, Any]]):
        sql = f"""
            INSERT INTO {tableName}
                ( filePath, value )
            VALUES
                ( ? , ? )
            ;
        """

        cursor = self.conn.cursor()
        cursor.executemany(sql, rows)
        cursor.connection.commit()
        cursor.close()
    
    def addLibrary(self, libraryPath: str) -> None:
        if not os.path.isdir(libraryPath):
            print(f'"{libraryPath}" is not a valid directory')
            exit(1)

        print(f"processing library {libraryPath}")
        mapArgs: List[Tuple[str, Any]] = []
        for curDirPath, _, fileNames in os.walk(libraryPath):
            for fileName in fileNames:
                fileName = os.path.join(curDirPath, fileName)
                if os.path.splitext(fileName)[1].lower() == ".mp3":
                    mapArgs.append((fileName, self.config))

        print(f"found {len(mapArgs)} valid files. processing...")

        self.conn.cursor()
        with Pool() as p:
            mappings = p.starmap(mapFile, mapArgs)
        self.__addMappings(mappings)
        
    def closeDB(self):
        self.conn.close()

    def queryDB(self, sql: str, parameters: Tuple = ()) -> list[sqlite3.Row]:

        if parameters is None:
            parameters = ()

        out = []
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, parameters)
            out = cursor.fetchall()
            cursor.close()
        except sqlite3.IntegrityError as e:
            print(f"integrity error: {e}")
            print(f"occurred while passing {parameters} to query {sql}")

        return out
