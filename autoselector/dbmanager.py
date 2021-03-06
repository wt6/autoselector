import sqlite3
from flask import Flask, g

class DBManager(object):
    '''Class for abstracting use of sqlite3 with flask app'''

    def __init__(self, app, db_location):
        self.app = app
        self.db_location = db_location;
        self.app.teardown_appcontext(self.close_connection)
        
    # check if database connection is already open, then either return existing
    # connection or open new one.
    def get_db(self):
        self.db = getattr(g, '_database', None)
        
        if self.db is None:
            self.db = g._database = sqlite3.connect(self.db_location)
        
        # Specify dict format for db's row factory
        def make_dicts(cursor, row):
            return dict((cursor.description[idx][0], value)
            for idx, value in enumerate(row))
        self.db.row_factory = make_dicts
        return self.db
        
    def close_connection(self, exception):
        self.db = getattr(g, '_database', None)
        if self.db is not None:
            self.db.close()
            
    def execute(self, statement, **kwargs):
        # Find which type of SQL statement was used
        statement_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        statement_type = None
        for type in statement_types:
            if statement[:len(type)].upper() == type:
                statement_type = type
                break
        
        # Refactor statement to use '?' to represent position of argument instead of argument key
        # name preceded by ':' and generate ordered args list from args dict.
        # '?' and arg list are required to interact with sqlite3.
        new_statement = ""
        arg_keys = []
        statement_length = len(statement)
        i = 0
        while i < statement_length:
        
            # ':' represents beginning of argument key to be replaced
            if statement[i] == ':':
                new_statement += '?'
                
                # ',', ')', ' ' or '' can represent the end of the arg key,
                # use whichever comes first
                end = len(statement)
                for char in (',', ')', ' '):
                    pos = statement.find(char, i)
                    if pos < end and pos != -1:
                        end = pos
                
                # add argument to keys list and continue loop from end 
                arg_keys.append(statement[i+1:end])
                i = end
            else:
                new_statement += statement[i]
                i += 1
        
        # check arguments in kwargs match keys and create ordered argument list
        arg_list = []
        for key in arg_keys:
            try:
                arg_list.append(kwargs[key])
            except KeyError:
                print("Error: Missing argument for sql statement, arg_list:", arg_list)
                return None
        
        # get cursor, fetch data from db, close connection and return rows
        cur = self.get_db().cursor()
        cur.execute(new_statement, arg_list)
        rv = cur.fetchall()
        
        # If insert statement was executed, commit change and return id for inserted record
        if statement_type == "INSERT" or statement_type == "UPDATE" or statement_type == "DELETE":
            self.db.commit()
            return cur.lastrowid
        else:
            return rv