import os
import re
import sqlite3
from sys import getfilesystemencoding
import re
from datetime import datetime
from random import randint
from time import sleep

#Third Party
from tqdm import tqdm
import docx

class DatabaseManager:
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.output_dir = os.path.join(self.working_dir, "Output")
        self.db = os.path.join(self.working_dir, "ExcavationPack.db")
        self.log_file = os.path.join(self.output_dir, "log_excel.txt")
        self.system_encoding = getfilesystemencoding()

    def check_database(self):
        """
        Checks multiple times to see if the database exists or not
        Exits the script if it does not exist
        Currently does a file check, will need some other method
        if a remote database is used
        """
        attempts = 0
        while attempts < 3:
            try:
                if os.path.isfile(self.db):
                    with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                        log_file.write("[{} Success]Database exists.".format(self.check_database.__name__))
                        log_file.write('\n')
                    return self.db
                else:
                    attempts += 1
                    with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                        log_file.write("[{} Failed]Database does not exist".format(self.check_database.__name__))
                        log_file.write('\n')
                    sleep(10)

            except Exception as e:
                with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                    log_file.write("[{} Failed]{}".format(self.check_database.__name__, str(e)))
                    log_file.write('\n')
                    return False
                    
        return False

class SearcherWord:

    def __init__(self, working_dir, database):
        self.working_dir = working_dir
        self.output_dir = os.path.join(self.working_dir, "Output")
        self.results_dir = os.path.join(self.output_dir, "Results") # Directory to place results
        self.log_file = os.path.join(self.output_dir, "log_word.txt")
        self.system_encoding = getfilesystemencoding()
        self.db = database
        self.keywords_file = os.path.join(self.working_dir, "keywords.txt") # File containing the keywords which will be searched for
        self.keywords = set()
        with open(self.keywords_file) as file:
            for line in file:
                self.keywords.add(line.strip())

        # States
        self.categorizing = self._sql_select_state_category("Categorizing")
        self.categorized = self._sql_select_state_category("Categorized")
        self.processing = self._sql_select_state_category("Processing")
        self.processed = self._sql_select_state_category("Processed")
        self.error = self._sql_select_state_category("Error")

        # Data Category
        self.word = self._sql_select_data_category("Word")
        self.notdetermined = self._sql_select_data_category("NotDetermined")

    def _sql_select_ready(self, DataCategoryID, StateID):
        """
        Selects and returns the FileName and FileHash from the database for all file with a certain state. 
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""
            SELECT categorization.FileHash, categorization.FileName
            FROM categorization
            INNER JOIN state
            ON categorization.FileHash = state.FileHash
            where DataCategoryID = {DataCategoryID}
            AND StateID = {StateID}
            ORDER BY RANDOM()
            ;
            """
            cursor.execute(sql)
            files = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_ready.__name__))
                log_file.write('\n')
            return files
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_select_ready.__name__, str(e)))
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
                log_file.write("[{} Failed]{}".format(self._sql_select_data_category.__name__, str(e)))
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
                log_file.write("[{} Failed]{}".format(self._sql_select_state_category.__name__, str(e)))
                log_file.write('\n')
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

    def _sql_select_processing_status(self):
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""SELECT * FROM state WHERE StateId = {self.processing};"""
            cursor.execute(sql)
            state = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_processing_status.__name__))
                log_file.write('\n')
            if state:
                state = state[0][0]
            return state
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_select_processing_status.__name__, str(e)))
                log_file.write('\n')
            return False

    def _sql_select_load_status(self):
        """
        Used to check the state of completion for the data categorizer
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            # Data to Select
            sql = f"""SELECT AllLoaded FROM load_status WHERE AllLoaded = 0;"""
            cursor.execute(sql)
            state = cursor.fetchall()
            conn.close()
            # Returning Filename and FileHash
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_select_load_status.__name__))
                log_file.write('\n')
            if state:
                state = state[0][0]
            return state
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_select_load_status.__name__, str(e)))
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
            WHERE DataCategoryID = {DataCategoryID}
            ORDER BY RANDOM();"""
            ## Random order helps processors avoid starting on the same file
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

    def _sql_update_state(self, FileHash, StateID):
        """
        Updates text files in the database as needed using the unique FileHash.
        """
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

    def _sql_insert_statistics(self, FileHash, ProcessingStartTime, ProcessingEndTime, ElapsedTime):
        """
        Updates text files in the database as needed using the unique FileHash.
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            #Data to Update
            sql = f"""
            INSERT OR IGNORE INTO statistics 
            VALUES (
                "{FileHash}", 
                "{ProcessingStartTime}",
                "{ProcessingEndTime}",
                "{ElapsedTime}"
            );
            """
            cursor.execute(sql)
            # Commit and Close
            conn.commit()
            conn.close()
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]".format(self._sql_insert_statistics.__name__))
                log_file.write('\n')
            return True

        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failed]{}".format(self._sql_insert_statistics.__name__, str(e)))
                log_file.write('\n')
            return False

    def _search_word(self, filename):
        """
        Searches a provided word document using the keywords list included in the class. 
        Writes findings to a file, using the keyword as the filename. 
        """
        try:
            # open connection to Word Document
            doc = docx.Document(filename)
        
            # read in each paragraph in file
            for paragraph in doc.paragraphs:
                for keyword in self.keywords:
                    if re.search(keyword, paragraph.text, re.IGNORECASE):
                        keyword_result_file = os.path.join(self.results_dir, keyword + ".txt")
                        with open(keyword_result_file, 'a') as krs:
                            # file_basename = os.path.split(filename)[1] #Only the filename
                            result = filename + "---" + paragraph.text
                            krs.write(result)
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Success]{}".format(self._search_word.__name__,filename))
                log_file.write('\n')
            return True
        except Exception as e:
            with open(self.log_file, 'a', encoding=self.system_encoding) as log_file:
                log_file.write("[{} Failure]{} --- {}".format(self._search_word.__name__,filename, str(e)))
                log_file.write('\n')
            return False

    def process_word(self):
        # Allowing some time for the DB to be set up, need a better way to handle this
        sleep(60)

        allloaded = self._sql_select_load_status()
        categorizing = self._sql_select_all_category(self.notdetermined)
        processing = self._sql_select_processing_status()

        while allloaded == 0 or categorizing or processing:
            files = self._sql_select_ready(self.word, self.categorized)
            if files:
                for filehash, filename in tqdm(files, desc="Progress"):
                    ProcessingStartTime = datetime.now()
                    if self._search_word(filename):
                        ProcessingEndTime = datetime.now()
                        ElapsedTime = ProcessingEndTime - ProcessingStartTime
                        self._sql_update_state(filehash, self.processed)
                        self._sql_insert_statistics(filehash, ProcessingStartTime, ProcessingEndTime, ElapsedTime)
                    else:
                        self._sql_update_state(filehash, self.error)

            allloaded = self._sql_select_load_status()
            categorizing = self._sql_select_all_category(self.notdetermined)
            sleep(30)
                    
def main():
    working_dir = "Data"
    
    dbm = DatabaseManager(working_dir)
    db = dbm.check_database()
    if db is False:
        exit()
    
    searcher = SearcherWord(working_dir, db)
    searcher.process_word()

if __name__ == "__main__":
    main()