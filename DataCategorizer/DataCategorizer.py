#Built in libraries
import os
import glob
from shutil import move
from shutil import copy
from sys import getfilesystemencoding
import re
import sqlite3
import hashlib
import tarfile
from random import randint
from random import shuffle
from time import sleep

#Third party libraries
import magic
from tqdm import tqdm

class DataCategorizer:
    """
    Provides methods for organizing and searching through files. 
    """
    def __init__(self, working_dir, dump_dir):
        #Provided to the class
        self.working_dir = working_dir # Base directory we are working from
        self.dump_dir = dump_dir # Directory containing the files we intend to work with
        self.db = os.path.join(self.working_dir, "ExcavationPack.db")
        self.system_encoding = getfilesystemencoding()

    def _load_values(self):
        # States
        self.categorizing = self._sql_select_state_category("Categorizing")
        self.categorized = self._sql_select_state_category("Categorized")
        self.processing = self._sql_select_state_category("Processing")
        self.processed = self._sql_select_state_category("Processed")
        self.error = self._sql_select_state_category("Error")

        # Data Categories
        self.gzip = self._sql_select_data_category("Gzip")
        self.excel = self._sql_select_data_category("Excel")
        self.excellegacy = self._sql_select_data_category("ExcelLegacy")
        self.pdf = self._sql_select_data_category("Pdf")
        self.plaintext = self._sql_select_data_category("Plaintext")
        self.word = self._sql_select_data_category("Word")
        self.notsupported = self._sql_select_data_category("NotSupported")
        self.notdetermined = self._sql_select_data_category("NotDetermined")
        self.duplicate = self._sql_select_data_category("Duplicate")
        # self.uncompressed = self._sql_select_data_category("Uncompressed")

    def _rename_file(self, filename):
        """
        Renames file using 'safe' characters.
        This is useful when operations need to be performed on files but fail due to special characters in the filename.
        Returns either a new file name or a boolean of False
        """
        file_dir = os.path.split(filename)[0]
        file_basename = os.path.split(filename)[1]
        safe_characters = "([^\\w\\.\\-_]|^[\\W_])" #Negate these character sets. In other words, everything but these will be replaced later. 
        # Regex Notes
        # [^\w\.\-_] # negate all of the characters in the set. In other words, these characters are allowed
        # | # or
        # ^[\W_] # negate if it starts with any of the characters in the set. In other words, cannot start with these characters
        # extra \'s necessary in Python to escape characters
        clean_file_basename = re.sub(safe_characters, "", file_basename)
        new_filename = os.path.join(file_dir, clean_file_basename)
        
        if re.search(safe_characters, file_basename):
            if (len(filename) > 260):
                # Handling long filepaths
                # Reference: https://bugs.python.org/issue18199
                filename = "\\\\?\\" + filename
            try:
                os.rename(filename, new_filename)
                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Success]{}".format(self._rename_file.__name__,filename))
                    log_file.write('\n')
                return new_filename
            except FileExistsError as e:
                # for some reason, some files get copied and look like they don't exist in the file explorer. Look at them with 'll' they show. 
                # just deleting them in this case
                os.remove(filename)
                return new_filename 
            except Exception as e:
                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Failed]{} --- {}".format(self._rename_file.__name__,filename, str(e)))
                    log_file.write('\n')
                return False # Probably should so somthing different here? Not sure the best solution. 
        else:
            return False

    def _sql_select_state(self, FileHash):
        """
        Used to check the state of the data.
        If found, returns the state, otherwise an empty list.
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""SELECT StateID FROM state WHERE FileHash = "{FileHash}";"""
            cursor.execute(sql)
            state = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_state.__name__))
                log_file.write('\n')
            if state:
                state = state[0][0]
            return state 
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_select_state.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_select_state_category(self, StateCategory):
        """
        Used to check the state of the data
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""SELECT ID FROM state_categories WHERE StateCategory = "{StateCategory}";"""
            cursor.execute(sql)
            state_id = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_state_category.__name__))
                log_file.write('\n')
            return state_id[0][0]
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- StateCategory {}".format(self._sql_select_state_category.__name__, str(e), StateCategory))
                log_file.write('\n')
            return False

    def _sql_select_data_category(self, DataCategory):
        """
        Used to check the state of the data
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""SELECT ID FROM data_categories WHERE DataCategory = "{DataCategory}";"""
            cursor.execute(sql)
            data_id = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_data_category.__name__))
                log_file.write('\n')
            return data_id[0][0]
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- DataCategory {}".format(self._sql_select_data_category.__name__, str(e),DataCategory))
                log_file.write('\n')
            return False

    def _sql_select_all_state(self, StateID):
        """
        Selects and returns the FileName and FileHash from the database for all entries with a specific StateID
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""
            SELECT FileHash
            FROM state 
            WHERE StateID = {StateID};"""
            cursor.execute(sql)
            files = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_all_state.__name__))
                log_file.write('\n')
            return files
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_select_all_state.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_select_all_category(self, DataCategoryID):
        """
        Selects and returns the FileName and FileHash from the database for all entries with a specific DataCategoryID
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""
            SELECT FileHash, FileName
            FROM categorization 
            WHERE DataCategoryID = {DataCategoryID};"""
            cursor.execute(sql)
            files = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_all_category.__name__))
                log_file.write('\n')
            return files
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_select_all_category.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_select_filename_exist(self, FileName):
        """
        Checks if a filename exist
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""
            SELECT EXISTS(SELECT 1 FROM categorization WHERE FileName="{FileName}")
            ;"""
            cursor.execute(sql)
            file_status = cursor.fetchall()[0][0] # select statement returns a tuple inside a list
            conn.close()
            if file_status:
                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Success] Exists in Database! {}".format(self._sql_select_filename_exist.__name__, FileName))
                    log_file.write('\n')
                return file_status
            else:
                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Success] Does NOT Exist in Database! {}".format(self._sql_select_filename_exist.__name__, FileName))
                    log_file.write('\n')
                return file_status

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- {}".format(self._sql_select_filename_exist.__name__, str(e), FileName))
                log_file.write('\n')
            return False

    def _sql_select_filehash_exist(self, FileHash):
        """
        Checks if a filename exist
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""
            SELECT EXISTS(SELECT 1 FROM categorization WHERE FileHash="{FileHash}")
            ;"""
            cursor.execute(sql)
            file_status = cursor.fetchall()[0][0] # select statement returns a tuple inside a list
            # file_status = cursor.fetchall() # select statement returns a tuple inside a list
            conn.close()
            if file_status:
                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Success] Exists in Database! {}".format(self._sql_select_filehash_exist.__name__, FileHash))
                    log_file.write('\n')
                return file_status
            else:
                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Success] Does NOT Exist in Database! {}".format(self._sql_select_filehash_exist.__name__, FileHash))
                    log_file.write('\n')
                return file_status

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- {}".format(self._sql_select_filehash_exist.__name__, str(e), FileHash))
                log_file.write('\n')
            return False

    def _sql_insert_category_filehash(self, FileHash, FileName, DataCategoryID):
        try:
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            sql = f"""INSERT OR IGNORE INTO categorization VALUES (NULL, "{FileHash}", "{FileName}", {DataCategoryID});"""
            cursor.execute(sql)
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{} --- {}".format(self._sql_insert_category_filehash.__name__,DataCategoryID ,FileName))
                log_file.write('\n')
            return True
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- {}".format(self._sql_insert_category_filehash.__name__,FileName, str(e)))
                log_file.write('\n')
            return False

    def _sql_insert_category_filename(self, FileName, DataCategoryID):
        try:
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            sql = f"""INSERT OR IGNORE INTO categorization VALUES (NULL, NULL, "{FileName}", {DataCategoryID});"""
            cursor.execute(sql)
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{} --- {}".format(self._sql_insert_category_filename.__name__,DataCategoryID ,FileName))
                log_file.write('\n')
            return True
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- {}".format(self._sql_insert_category_filename.__name__,FileName, str(e)))
                log_file.write('\n')
            return False

    def _sql_insert_state(self, FileHash, State):

        try:
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            sql = f"""INSERT OR IGNORE INTO state VALUES ("{FileHash}", "{State}");"""
            cursor.execute(sql)
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_insert_state.__name__))
                log_file.write('\n')
            return True
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_insert_state.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_insert_data_categories(self):

        try:
            data_categories = ("Plaintext", "Pdf", "Excel", "ExcelLegacy", "Word", "Gzip", "NotSupported", "NotDetermined", "Duplicate", "Uncompressed")
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            for category in data_categories:    
                sql = f"""INSERT OR IGNORE INTO data_categories VALUES (NULL, "{category}");"""
                cursor.execute(sql)
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_insert_data_categories.__name__))
                log_file.write('\n')
            return True
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_insert_data_categories.__name__, str(e)))
                log_file.write('\n')
            return False
 
    def _sql_insert_state_categories(self):

        try:
            data_categories = ("Categorizing", "Categorized", "Processing", "Processed", "Error")
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            for category in data_categories:    
                sql = f"""INSERT OR IGNORE INTO state_categories VALUES (NULL, "{category}");"""
                cursor.execute(sql)
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_insert_state_categories.__name__))
                log_file.write('\n')
            return True
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_insert_state_categories.__name__, str(e)))
                log_file.write('\n')
            return False
 
    def _sql_update_categorization_status(self, status):
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            #Data to Update
            sql = f"""
            UPDATE categorization_status
            SET AllCategorized = {status}
            """
            cursor.execute(sql)
            # Commit and Close
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_update_categorization_status.__name__))
                log_file.write('\n')
            return True

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_update_categorization_status.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_update_state(self, FileHash, StateID):
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            #Data to Update
            sql = f"""
            UPDATE state
            SET StateID = {StateID}
            WHERE FileHash = "{FileHash}"
            """
            cursor.execute(sql)
            # Commit and Close
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_update_state.__name__))
                log_file.write('\n')
            return True

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_update_state.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_update_category_byhash(self, FileHash, DataCategoryID):
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            #Data to Update
            sql = f"""
            UPDATE categorization
            SET DataCategoryID = {DataCategoryID}
            WHERE FileHash = "{FileHash}"
            """
            cursor.execute(sql)
            # Commit and Close
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{} --- {}".format(self._sql_update_category_byhash.__name__, DataCategoryID, FileHash))
                log_file.write('\n')
            return True
        
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_update_category_byhash.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_update_category_byname(self, FileName, DataCategoryID):
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            #Data to Update
            sql = f"""
            UPDATE categorization
            SET DataCategoryID = {DataCategoryID}
            WHERE FileName = "{FileName}" AND FileHash is NULL
            """
            cursor.execute(sql)
            # Commit and Close
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{} --- {}".format(self._sql_update_category_byname.__name__, DataCategoryID, FileName))
                log_file.write('\n')
            return True

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_update_category_byname.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_update_category_filehash(self, FileHash, FileName):
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            #Data to Update
            sql = f"""
            UPDATE OR IGNORE categorization
            SET FileHash = "{FileHash}"
            WHERE FileName = "{FileName}"
            """
            cursor.execute(sql)
            # Commit and Close
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{}".format(self._sql_update_category_filehash.__name__, FileHash))
                log_file.write('\n')
            return True
        
        ### Found that using Integrity error checking made database transactions VERY slow, caused continuous locks
        # except sqlite3.IntegrityError:
        #     self._sql_update_category_byname(FileName, self.duplicate)
        #     with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
        #         log_file.write("[{} Success] Due to an Integrity Error, the file was marked as a duplicate --- {}".format(self._sql_update_category_filehash.__name__, FileName))
        #         log_file.write('\n')
        #     return True

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_update_category_filehash.__name__, str(e)))
                log_file.write('\n')
            return False

    def _generate_filenames(self, directory):
        """
        Simple function to generate filenames based on the files within the provided directory
        """
        try:
            # filename_gen = glob.iglob(directory + '/**/*.*', recursive=True) #Generator for the filenames, recursively searches for all files in the directory.
            filename_gen = glob.glob(directory + '/**/*.*', recursive=True) #Generator for the filenames, recursively searches for all files in the directory.
            shuffle(filename_gen) # Put into a random order, makes it less likely that processors will begin on the same file
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._generate_filenames.__name__))
                log_file.write('\n')
            return filename_gen
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._generate_filenames.__name__, str(e)))
                log_file.write('\n')
            return False

    def _get_file_magic(self, filename):
        """
        Detects the file type using a Python wrapper for libmagic
        """
        try:
            filetype = magic.from_file(filename)
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{} --- {}".format(self._get_file_magic.__name__,filename, filetype))
                log_file.write('\n')
            return filetype
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- {}".format(self._get_file_magic.__name__,filename, str(e)))
                log_file.write('\n')
            return False

    def _create_dirs(self):
        """
        Creates the required directories for all functions in the class.
        """
        try:
            self.output_dir = os.path.join(self.working_dir, "Output")
            self.results_dir = os.path.join(self.output_dir, "Results") # Directory to place results
            self.log_file = os.path.join(self.output_dir, "log_datacategorizer.txt") # Used for error logging
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
            if not os.path.exists(self.results_dir):
                os.mkdir(self.results_dir) 

            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._create_dirs.__name__))
                log_file.write('\n')
            return True

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._create_dirs.__name__, str(e)))
                log_file.write('\n')
            return False

    def _create_db(self):
        try:
            if not os.path.isfile(self.db):
                conn = sqlite3.connect(self.db)
                conn.execute('pragma journal_mode=wal')
                cursor = conn.cursor()

                # Create tables
                create_table_data_categories = """
                CREATE TABLE data_categories (
                    ID INTEGER PRIMARY KEY,
                    DataCategory TEXT
                );
                """
                create_table_state_categories = """
                CREATE TABLE state_categories (
                    ID INTEGER PRIMARY KEY,
                    StateCategory TEXT
                );
                """
                create_table_categorization = """
                CREATE TABLE categorization (
                    ID INTEGER PRIMARY KEY,
                    FileHash TEXT UNIQUE,
                    FileName TEXT UNIQUE,
                    DataCategoryID INTEGER,
                    FOREIGN KEY (DataCategoryID)
                        REFERENCES data_categories(ID) 
                );
                """
                create_table_state = """
                CREATE TABLE state (
                    FileHash TEXT PRIMARY KEY,
                    StateID INTEGER,
                    FOREIGN KEY (FileHash)
                        REFERENCES categorization(FileHash)
                    FOREIGN KEY (StateID)
                        REFERENCES create_table_state_categories(ID)
                );
                """
                create_table_statistics = """
                CREATE TABLE statistics (
                    FileHash TEXT PRIMARY KEY,
                    ProcessingStartTime TEXT,
                    ProcessingEndTime TEXT,
                    ElapsedTime TEXT,
                    FOREIGN KEY (FileHash)
                        REFERENCES  categorization(FileHash)
                );
                """
                create_table_categorization_status = """
                CREATE TABLE categorization_status (
                    AllCategorized INTEGER
                );
                """

                cursor.execute(create_table_data_categories)
                cursor.execute(create_table_state_categories)
                cursor.execute(create_table_categorization)
                cursor.execute(create_table_state)
                cursor.execute(create_table_statistics)
                cursor.execute(create_table_categorization_status)

                # Set starting value for categorization_status
                sql = """INSERT INTO categorization_status VALUES (0);"""
                cursor.execute(sql)
                conn.commit()
                conn.close()

                self._sql_insert_data_categories()
                self._sql_insert_state_categories()

                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Success]".format(self._create_db.__name__))
                    log_file.write('\n')
                return True

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._create_db.__name__, str(e)))
                log_file.write('\n')
            return False

    def _hash_file(self, filename):
        """
        This function returns the SHA-1 hash
        of the file passed into it
        """
        try: 
            # make a hash object
            h = hashlib.sha1()

            # open file for reading in binary mode
            with open(filename,'rb') as file:

                # loop till the end of the file
                chunk = 0
                while chunk != b'':
                    # read only 1024 bytes at a time
                    chunk = file.read(1024)
                    h.update(chunk)

            # return the hex representation of digest
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._hash_file.__name__))
                log_file.write('\n')
            return h.hexdigest()

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- {}".format(self._hash_file.__name__,filename, str(e)))
                log_file.write('\n')
            return filename
   
    def _uncompress_gzip(self, filename, filehash):
        """
        Uncompresses the file and saves to the destination directory
        """
        try:
            destination_dir = os.path.join(os.path.dirname(filename), "Uncompressed", os.path.basename(filename.split(".")[0]))
            tar = tarfile.open(filename)
            members = tar.getmembers() # Contents of the compressed file
            tar.extractall(members=tqdm(members, desc=f"Uncompressing {filename}"), path=destination_dir) # Uncompress and use a progress bar
            tar.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{}".format(self._uncompress_gzip.__name__,filename))
                log_file.write('\n')
            return destination_dir

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{} --- {}".format(self._uncompress_gzip.__name__,filename, str(e)))
                log_file.write('\n')
            return False

    def _load_filenames(self, my_directory=None):
        
        # See if the file needed to be renamed. 
        # Since multiple instances of this container can run at once, may get errors trying to rename files
        try:
            # Decreases likelyhood that multiple processors start on the same file
            delay = randint(5,20)
            sleep(delay)
            
            if my_directory:
                filename_gen = self._generate_filenames(my_directory)
            else:
                filename_gen = self._generate_filenames(self.dump_dir)
                
            for filename in filename_gen:
                self._rename_file(filename) 

            # Load files into database
            # Explicitly renaming files first and then making a new filename generator avoids
            # other processors trying to work on files that have been renamed
            if my_directory:
                filename_gen = self._generate_filenames(my_directory)
            else:
                filename_gen = self._generate_filenames(self.dump_dir)

            for filename in filename_gen:
                if self._sql_select_filename_exist(filename): # Skip files that have already been loaded into the database. Necessary for dealing with newly uncompressed files
                    continue
            
                self._sql_insert_category_filename(filename, self.notdetermined) #hashes can take a while with large files, need to insert into database before file hashing begins
                filehash = self._hash_file(filename) 
                # Handling duplicate files, those with different file names but the same hash 
                if self._sql_select_filehash_exist(filehash):
                    self._sql_update_category_byname(filename, self.duplicate)
                else:
                    self._sql_update_category_filehash(filehash, filename)

            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._load_filenames.__name__))
                log_file.write('\n')

            return True
        
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._load_filenames.__name__, str(e)))
                log_file.write('\n')
            return False

    def process_directory(self):
        """ 
        Search files by trying to check the file type and use the appropriate method to parse. 
        """
        self._create_dirs()
        self._create_db()
        self._load_values()
        self._sql_update_categorization_status(0) # Explicitly setting, may not be the first run. 
        self._load_filenames()

        processing = self._sql_select_all_category(self.notdetermined)

        while processing:
            files = self._sql_select_all_category(self.notdetermined)
            if files:
                for filehash, filename in files:
                    if filehash == None: # Files are loaded before they are hashed, skip until hash is determined
                        continue

                    # file_state = self._sql_select_state(filehash)
                    # if file_state: # Skip files that other processors have already started
                    #     continue

                    self._sql_insert_state(filehash, self.categorizing) #Take ownership so other processors do not try

                    filetype = self._get_file_magic(filename)

                    if filetype:
                        # Compressed files
                        if "gzip compressed data" in filetype.lower():
                            self._sql_update_category_byhash(filehash, self.gzip)
                            self._sql_update_state(filehash, self.processing) #Take ownership so other processors do not try
                            uncompressed = self._uncompress_gzip(filename, filehash)
                            if uncompressed:
                                self._sql_update_state(filehash, self.processed) 
                                self._load_filenames(uncompressed) # load the new filenames
                            else:
                                self._sql_update_state(filehash, self.error) 

                        # Text Files
                        elif "text" in filetype.lower():
                            self._sql_update_category_byhash(filehash, self.plaintext)
                            self._sql_update_state(filehash, self.categorized) 

                        # Modern Excel Files
                        elif "Microsoft Excel 2007+" in filetype:
                            self._sql_update_category_byhash(filehash, self.excel)
                            self._sql_update_state(filehash, self.categorized) 

                        # Legacy Excel Files
                        elif (".xls" in filename) and ("Composite Document File V2 Document, Little Endian" in filetype or "CDFV2 Microsoft Excel" in filetype):
                            self._sql_update_category_byhash(filehash, self.excellegacy)
                            self._sql_update_state(filehash, self.categorized) 

                        # Modern Word Files
                        elif "Microsoft Word 2007+" in filetype:
                            self._sql_update_category_byhash(filehash, self.word)
                            self._sql_update_state(filehash, self.categorized) 

                        # PDF Files
                        elif "PDF document" in filetype:
                            self._sql_update_category_byhash(filehash, self.pdf)
                            self._sql_update_state(filehash, self.categorized) 

                        # Unsupported files
                        else:
                            self._sql_update_category_byhash(filehash, self.notsupported)
                            self._sql_update_state(filehash, self.categorized) 

                    # Unable to determine file type
                    else:
                        self._sql_update_state(filehash, self.error) 
                
            # If not other containers are still categorizing data, set the status to complete. 
            processing = self._sql_select_all_category(self.notdetermined)
            if not processing:
                self._sql_update_categorization_status(1)
 
def main():
    # Variables & instantiation 
    working_dir = "Data" # Base directory we are working from
    dump_dir = os.path.join(working_dir, "Dump") # Directory containing the files of interest

    dc = DataCategorizer(working_dir, dump_dir)
    dc.process_directory()


if __name__ == "__main__":
    main()





