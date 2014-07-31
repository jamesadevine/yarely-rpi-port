import hashlib
import os
import sqlite3
import time
import urllib.request
from yarely.frontend.core import platform
from yarely.frontend.core.config import YarelyConfig

YARLEY_ROOT = '/Users/bholanath/proj/yarely/frontend/core'
CONFIG_ROOT = os.path.join(YARLEY_ROOT, 'config', 'samples')
CONFIG_PATH = os.path.join(CONFIG_ROOT, 'yarely.cfg')

CREATE_INDEX_RECORD = """CREATE TABLE IF NOT EXISTS {table} (
                            index_id INTEGER PRIMARY KEY, index_name TEXT,
                            index_path TEXT, index_date TEXT, eTag TEXT,
                            last_modified TEXT, index_size INTEGER,
                            index_use INTEGER
                         )"""

DELETE_INDEX_RECORD = """DELETE FROM {table}
                         WHERE index_path = '{index_record}'"""

INSERT_INDEX_RECORD = """INSERT INTO {table} (
                            index_id, index_name, index_path, index_date, eTag,
                            last_modified, index_size, index_use)
                         VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)"""

SELECT_COUNT_INDEX_RECORD = """SELECT count(index_id)
                               FROM {table}"""

SELECT_ETAG_RECORD = 'SELECT eTag FROM {table} WHERE eTag LIKE {etag_value}'

SELECT_LRU_RECORD = """SELECT
                            index_id, index_path, index_size,
                            SUM(index_size) as lru_release_size
                       FROM {table}
                       WHERE index_use IN (
                            SELECT MIN(index_use) FROM {table}
                       )"""

SELECT_SUM_INDEX_RECORD = """SELECT SUM(index_size) as current_cache_size
                             FROM {table}"""


class ConfigError(Exception):
    """Raised when a config error occurs."""
    pass


class ConfigParsingError(ConfigError):
    """Raised when a config parsing error occurs."""
    pass


class DatabaseHandlerError(Exception):
    """Raised when a Database error occurs."""
    pass


class DatabaseSqlCommandError(DatabaseHandlerError):
    """Raised when a Database SQL command error occurs."""
    pass


class DatabaseSqlExecuteError(DatabaseHandlerError):
    """Raised when a Database sql execute error occurs."""
    pass


class FileError(Exception):
    """Raised when a File error occurs."""
    pass


class HTTPFetchError(Exception):
    """Raised when a HTTP fetch error occurs."""
    pass


class HTTPFetchUrlError(HTTPFetchError):
    """Raised when a HTTP URL Fetch error occurs."""
    pass


class HTTPMD5Error(HTTPFetchError):
    """Raised when a HTTP MD5 Fetch error occurs."""
    pass


class DatabaseHandler():
    """Handles database requests."""

    def __init__(self, conn, cursor):
        self._cache_db_table_name = None
        self.config = YarelyConfig(CONFIG_PATH)
        self.conn = conn
        self.cursor = cursor
        self._database_process_config()
        self.INDEX_USE_COUNT = 0

    def _database_process_config(self):
        """Update database configuration from a YarelyConfig instance."""

        # Parses cache config and returns the cache table name.
        try:
            self._cache_db_table_name = self.config.get("CacheMetaStorage",
                                                        "IndexTable")
        except Exception as e:
            msg = 'Could not parse config file to retrieve IndexTable'
            raise ConfigParsingError(msg) from e

    def db_create_db(self, sql):
        """Create database from SQL statement."""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except DatabaseHandlerError as error:
            msg = 'Database execute exception while commit sql: ' + sql
            raise DatabaseSqlExecuteError(msg) from error

    def db_add_content(self, fname, db_path, etag, last_modified, f_size):
        """Add a new cache index record to metadata database."""

        try:
            today = time.strftime("%A, %B %d, %Y")
            sql = INSERT_INDEX_RECORD.format(table=self._cache_db_table_name)
            self.cursor.execute(sql, (fname, db_path, today, etag,
                                      last_modified, f_size,
                                      self.INDEX_USE_COUNT))
            self.conn.commit()
        except DatabaseHandlerError as error:
            msg = 'Could not insert cache index entry.'
            raise DatabaseSqlExecuteError(msg) from error

    def db_search_etag(self, e_tag_search):
        """Look for index in database coresponding to the Etag."""

        try:
            sql = SELECT_ETAG_RECORD.format(table=self._cache_db_table_name,
                  etag_value=e_tag_search)
            self.cursor.execute(sql)
            if len(self.cursor.fetchall()) > 0:
                return True
        except Exception as e:
            msg = 'Could not retrieve etag from cache index table'
            raise DatabaseSqlCommandError(msg) from e

    def db_cache_size(self):
        """Returns size of index entries from database."""

        try:
            sql = SELECT_SUM_INDEX_RECORD.format(
                  table=self._cache_db_table_name)
            self.cursor.execute(sql)
            current_cache_items = self.cursor.fetchall()
        except DatabaseHandlerError as error:
            msg = 'Could not get total index size from index table'
            raise DatabaseSqlExecuteError(msg) from error

        current_cache_size = 0

        for item_size in current_cache_items:
            if len(current_cache_items) > 0:
                current_cache_size = item_size[0]
                if current_cache_size is None:
                    current_cache_size = 0

        return current_cache_size

    def db_lru(self, new_file_size, cache_size):
        """Remove the least recently used file from the cache index
        database.

        """

        # boolean returning true from db_lru if new_file can be saved in
        # file.
        file_to_save = False
        # check total disk space on cache from database.
        current_db_cache_size = self.db_cache_size()
        # check total disk space on cache from database.
        # delete lru if new cache size is greater than available.
        new_cache_size = int(new_file_size) + int(current_db_cache_size)
        lru_not_reached = True

        # if new file received is greater than cache size - do not save
        if new_file_size > int(cache_size):
            lru_not_reached = False
        # if enough space after adding file no need to use lru
        if new_cache_size < int(cache_size):
            lru_not_reached = False
            file_to_save = True

        # Remove least recently used index. Loops through the cache to
        # remove LRU index till the new index can be saved.
        while lru_not_reached:
            try:
                sql = SELECT_LRU_RECORD.format(table=self._cache_db_table_name)
                self.cursor.execute(sql)
                lru_entries = self.cursor.fetchall()
                sql_count = SELECT_COUNT_INDEX_RECORD.format(
                                     table=self._cache_db_table_name)
                self.cursor.execute(sql_count)
                entries_count = self.cursor.fetchall()
                if len(entries_count) >= len(lru_entries):
                    for item in lru_entries:
                        # check for 0 cache - in which case it
                        # returns item[1] none
                        if item[1] != None:
                            # item[1] returns path of lru file.
                            os.remove(item[1])
                            try:
                                sql = DELETE_INDEX_RECORD.format(
                                      table=self._cache_db_table_name,
                                      index_record=item[1])
                                self.cursor.execute(sql)
                                self.conn.commit()
                            except DatabaseHandlerError as error:
                                msg = 'Could not delete cache index entry'
                                raise DatabaseSqlExecuteError(msg) from error

                        # In db-cache is empty exit loop
                        else:
                            lru_not_reached = False
                            file_to_save = True
                            break
                        # check if released sufficient cache to save file
                        new_cache_size = self.db_cache_size()
                        update_size = int(new_file_size) + int(new_cache_size)
                        # cache is enough to save, exit loop
                        if (int(cache_size) - update_size) > 0:
                            lru_not_reached = False
                            file_to_save = True
            except DatabaseHandlerError as error:
                msg = 'Error in loop while looking for LRU.'
                raise DatabaseSqlExecuteError(msg) from error
        return file_to_save


class HandleHTTP:
    """A handler for caching resources over HTTP."""

    def __init__(self):
        self.config = YarelyConfig(CONFIG_PATH)
        self._cache_db_name = None
        self._cache_db_table_name = None
        self._cache_size = None
        self._db_loc = None
        self.MD5_HASH_BLOCK_SIZE = 4096
        self._disk_space_size = None
        self._process_config()

    def _process_config(self):
        """Update cache configuration from a YarelyConfig instance."""

        # Parses cache config and returns the cache dabase name.
        try:
            self._cache_db_name = self.config.get("CacheMetaStorage",
                                                  "metastorepath")
        except Exception as e:
            msg = 'Could not parse config to retrieve metastorepath'
            raise ConfigParsingError(msg) from e

        # Parses max cache size and returns size in bytes.
        try:
            self._cache_size = self.config.getint("CacheFileStorage",
                                                  "MaxCacheSize")
        except Exception as e:
            msg = 'Could not parse config to retrieve MaxCacheSize'
            raise ConfigParsingError(msg) from e

       # Parses cache config and returns the cache table name.
        try:
            self._cache_db_table_name = self.config.get("CacheMetaStorage",
                                                        "IndexTable")
        except Exception as e:
            msg = 'Could not parse config to retrieve IndexTable'
            raise ConfigParsingError(msg) from e

        # Parses cache config and returns the cache database location path.
        try:
            self._db_loc = self.config.get("CacheFileStorage",
                                           "CacheLocation")
        except Exception as e:
            msg = 'Could not parse config to retrieve CacheLocation'
            raise ConfigParsingError(msg) from e

        # Parses cache config and returns the disk space available.
        try:
            self._disk_space_size = int(platform.get_available_space_in_bytes(
                                 self.config.get("CacheFileStorage",
                                                 "CacheLocation")))
        except Exception as e:
            msg = 'Could not parse config to retrieve CacheLocation to get' \
                  'disk space size'
            raise ConfigParsingError(msg) from e

    def check_file_exists(self, url, file_name):
        """Return True if file already exists and MD5 of new file
           and old file are the same.

        """
        try:
            cache_directory = self._db_loc
            cache_loc = os.path.join(cache_directory, file_name)
            if os.path.exists(cache_loc):
                remote_file_hash = self.get_remote_md5_sum(url)
                local_file_hash = self.md5_checksum(cache_loc)
                return self.md5_comparator(local_file_hash, remote_file_hash)
            else:
                # File does not exist
                return False
        except Exception as error:
            msg = 'Exception raised on check_file_exists()'
            raise FileError(msg) from error

    def extract_url_name(self, url):
        """Return name file. It is returned as string."""
        return''.join(url.split('/')[-1])

    def fetch_url(self, url):
        """Return HTTP Opener of URL."""
        # Fetch url from server
        req = urllib.request.Request(url)
        try:
            opener = urllib.request.urlopen(req)
            return opener
        except Exception as e:
            msg = 'Wrong URL'
            raise HTTPFetchUrlError(msg) from e

    def fetch_http(self, url):
        """Fetch http request and save it if it does not exits.  """
        # 1. Check if disk space available is greater than cache allocated in
        #    config.
        # 2. Extract url and get file opener from url.
        # 3. Get last modified date, Etag, size of file.
        # 4. Check if etag or last modified-date are same in cache directory.
        # 5. Use LRU if file size after adding is greater than cache size.
        if self._disk_space_size > int(self._cache_size):
            try:
                fetch_file_name = self.extract_url_name(url)
                fetch_file_opener = self.fetch_url(url)
                # if fetch file opener is not empty, url valid
                if fetch_file_opener != False:
                    # get etag of new file
                    fetch_file_etag = self.get_etag(fetch_file_opener)
                    # get last modified date of file
                    fetch_file_last_modified = self.get_last_modified(
                                                    fetch_file_etag,
                                                    fetch_file_opener)
                    # get the remote file size
                    fetch_file_size = int(fetch_file_opener.headers.get(
                                          'Content-Length'))
                    # check if file is not already present
                    if self.check_file_exists(url, fetch_file_name) == False:
                        # save request to local cache directory and keep a
                        # record in the database file been fetched
                        self.save_request(fetch_file_name, self._db_loc,
                                          fetch_file_opener,
                                          fetch_file_etag,
                                          fetch_file_last_modified,
                                          fetch_file_size)
                    return True
            except Exception as e:
                msg = 'Failed to fetch http request'
                raise HTTPFetchError(msg) from e

    def get_etag(self, opener):
        """Return eTag from URL received."""
        if opener != 0:
            return opener.headers.get('ETag')
        return False

    def get_last_modified(self, etag, opener):
        """Return last modified time of URL received."""
        nextRequestHeaders = {}
        if etag:
            nextRequestHeaders['If-None-Match'] = etag[0]
            modified = opener.headers.get('last-modified')
        return modified

    def get_remote_md5_sum(self, url):
        """Return MD5 of remote URL file."""
        try:
            req = urllib.request.Request(url)
            remote = 0
        except Exception as error:
            msg = 'Wrong URL Request.'
            raise HTTPFetchError(msg) from error
            return False
        try:
            remote = urllib.request.urlopen(req)
        except Exception as e:
            msg = 'Wrong URL Open Request.'
            raise HTTPFetchError(msg) from e
            return False
        try:
            hash = hashlib.md5()
            total_read = 0
            # get block size to read
            block_file = self.MD5_HASH_BLOCK_SIZE
            # retrieve max size of index
            max_index_space = self._cache_size
            while True:
                data = remote.read(block_file)
                total_read += block_file

                if not data or total_read > max_index_space:
                    break

                hash.update(data)

                return hash.hexdigest()
        except Exception as error:
            msg = 'Exception raised in reading MD5 hash.'
            raise HTTPMD5Error(msg) from error

    def md5_checksum(self, file_path):
        """Return MD5 hash of file stored locally."""
        try:
            with open(file_path, 'rb') as remote:
                hash = hashlib.md5()
                total_read = 0
                # get block size to read
                block_file = self.MD5_HASH_BLOCK_SIZE
                # retrieve platform max disk space
                max_index_space = self._cache_size
                while True:
                    data = remote.read(block_file)
                    total_read += block_file

                    if not data or total_read > max_index_space:
                        break

                    hash.update(data)

                    return hash.hexdigest()
        except Exception as error:
            msg = 'Exception raised in md5_checksum().'
            raise HTTPMD5Error(msg) from error

    def md5_comparator(self, current_content, new_content):
        """ Return true if new content and local
        content MD5 is same """
        if current_content == new_content:
            return True

    def save_request(self, fname, loc_path, content, etag,
                     last_modified, f_size):
        """Save content url contents to disk."""
        try:
            conn = sqlite3.connect(self._cache_db_name)
            cursor = conn.cursor()
            database_handler = DatabaseHandler(conn, cursor)
            # create database and index table if it does not exist
            sql = CREATE_INDEX_RECORD.format(table=self._cache_db_table_name)
            database_handler.db_create_db(sql)
            if database_handler.db_search_etag(etag) != True:
                # Add new contents to database if there is space in cache only
                if database_handler.db_lru(f_size, self._cache_size) == True:
                    open(os.path.join(loc_path, fname), 'wb').write(
                         content.read())

                    database_handler.db_add_content(fname, os.path.join(
                                                    loc_path, fname), etag,
                                                    last_modified, f_size)
        except Exception as e:
            msg = 'Raise Error in save_request()'
            raise HTTPFetchUrlError(msg) from e
