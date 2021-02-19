from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pyqt5Custom import *
from sshtunnel import SSHTunnelForwarder as ssh
import mysql.connector as con, os, sys, re

class PySql:    
    def __init__(self, host, user, password, database, port = 3306, debug = False):
        for _ in range(2):
            e = database == ""
            try:
                self.db = con.connect(host = host, port = port, user = user, password = password, database = database)
                self.db_name = database
                self.cursor = self.db.cursor()
                self.debug = debug
                self.results = None
                self.__vals = None
            except:
                try:
                    self.db = con.connect(host = host, port = port, user = user, password = password)
                    self.db_name = database
                    self.cursor = self.db.cursor()
                    self.cursor.execute("set sql_notes = 0")
                    self.cursor.execute("create database if not exists {}".format(database))
                    self.cursor.execute("use database {}".format(database))
                    self.debug = debug
                    self.results = None
                    self.__vals = None
                except:
                    e = True
        if e: 
            sys.exit("Please enter a valid host, user, password, or database.")
                        
    def printResults(self, index = None, printText = True, debug = True):
        '''Print out data results.
           printText - Allows data results to be printed.
           index - Prints out a number.
           Note: It may be better to set printText = False if the result being printed is large.'''
        if debug:
            print(("" if index is None else "{}. ".format(index)) + (self.results[0] if printText else ""))
            if not self.results[2] is None:
                [print(r) for r in self.results[2]]
            print()
        return self
            
    def writeResults(self, index = None, out = ""):
        '''Write out data results to a file.'''
        if out != "":
            w = open(out, "a+")
            w.write(("" if index is None else "{}. ".format(index)) + self.results[0] + "\n")
            if not self.results[2] is None:
                [w.write(str(r) + "\n") for r in self.results[2]]
            w.write("\n")
            w.close()
        return self
            
    def use(self, database, debug = None):
        '''Method for "use database" statement.'''
        if debug is None: debug = self.debug
        u = "use {}".format(database)
        self.cursor.execute(u)
        if debug: print(u)
        return self
    
    def columns(self):
        '''Returns columns of a table.'''
        return tuple([f[0] for f in self.cursor.description])
        
    def setArgs(self, *vals):
        self.__vals = vals
        return self
        
    def primaries(self, table):
        '''Returns primary keys of the table.'''
        return tuple([d["Column_name"] for d in self.setArgs("PRIMARY").query("show keys from {} where Key_name = %s".format(table)).results[2]])
    
    def __checkError(self, err):
        if "Duplicate" in err:
            r = re.search("entry '.*'.* key '.*\.(.*)'", err)
            err = "An account already exists with this {}".format(r.group(1).replace("_", " "))
        return err
    
    def modify(self, query, *vals):
        '''For inserts, updates, or deletes. Statements that modify the database.'''
        try:
            if len(vals) < 1:
                query = query.replace("!!NEWLINE!!", "\n")
                q = query.split("!!VALS!!")
                vals = [int(v[:-len("!!INT!!")]) if "!!INT!!" in v else v[1:-1] for v in q[1:]]
                self.cursor.execute(q[0], vals)
                query = query.replace("!!VALS!!", "").replace("!!INT!!", "")
            else:
                self.cursor.execute(query, vals)
            self.db.commit()
            for v in vals: query = query.replace("%s", str(v), 1)
            return query
        except con.Error as e:
            return self.__checkError(e.msg)
        
    def query(self, q, index = None, printText = True, debug = None, out = ""):
        '''Statements that don't modify the database and just pull out data, 
           such as select statements.'''
        try:
            if debug is None: debug = self.debug
            if self.__vals is None:
                if q.strip() != "": self.cursor.execute(q)
            else:
                if q.strip() != "":
                    self.cursor.execute(q, self.__vals)
                    for v in self.__vals:
                        q = q.replace('%s', "'{}'".format(v) if isinstance(v, str) else v.__str__(), 1)
                self.__vals = None
            if q.strip() == "":
                self.results = ("Query cannot be empty. Please enter a query.", None, None)
            else:
                cols = self.columns()
                self.results = (q, cols, [dict(zip(cols, row)) for row in self.cursor.fetchall()])
        except con.Error as e:
            self.results = (self.__checkError(e.msg), None, None)
        return self.printResults(index, printText, debug).writeResults(index, out)
    
    def __checkStatements(self, statement, *check):
        if len(check) > 0:
            for c in check:
                if statement[:len(c)].lower() == c:
                    return True
        return False
    
    def source(self, readFile, outFile = "", printText = True, debug = None):
        '''Executes queries and statements in .txt or .sql files.'''
        if debug is None: debug = self.debug
        if outFile != "" and os.path.exists(outFile): os.remove(outFile)
        readFile = os.path.dirname(__file__) + "\\" + readFile
        print("Source " + readFile + "\n")
        r, q, s = ([], open(readFile, encoding = "utf-8"), "")
        for i in q: 
            if ".sql" in readFile:
                b = "#" in i or "--" in i or "delimiter" in i
                if b: continue
                else:
                    if i.strip() == "":
                        if s == "": continue
                    else:
                        i = str(i).replace("$$", "")
                        s += i
                        continue
            elif ".txt" in readFile: 
                if i.strip() == "": continue
                else: s = i
            if self.__checkStatements(s, "set", "use"):
                self.cursor.execute(s)
            else:
                j = len(r)+1
                if self.__checkStatements(s, "insert", "update", "delete"):
                    m = self.modify(s)
                    self.results = (m, None, None)
                    self.printResults(j, printText, debug).writeResults(j, outFile)
                    r.append(m)
                elif self.__checkStatements(s, "create", "drop"):
                    self.cursor.execute(s)
                    self.results = (s, None, None)
                    self.printResults(j, printText, debug).writeResults(j, outFile)
                    r.append(s)
                else: 
                    r.append(self.query(s, index=j, printText=printText, debug=debug, out=outFile).results)
            s = ""
        q.close()
        self.results = (readFile, "", r)
        return self
    
    def backupTable(self, table):
        '''Backs up table.'''
        bd = self.query("show columns from {}".format(table)).results[2]
        c = ", ".join("{} {} {}{}".format(d["Field"], str(d["Type"])[2:-1], "null" if d["Null"] == "YES" else "not null", "" if d["Extra"] == "" else " " + d["Extra"]) for d in bd)
        p = self.primaries(table)
        if len(p) > 0: c += ", primary key ({})".format(", ".join(i for i in p))
        s = self.query("select * from {}".format(table)).results[2]
        for i in s: 
            if i == "date": i["date"] = i["date"].__str__()
        b = open("backup-{}.txt".format(table), "w+", encoding = "utf-8")
        b.write("drop table if exists {}\n".format(table))
        b.write("create table {} ({}) engine = INNODB\n".format(table, c))
        for i, v in enumerate(s): 
            b.write("insert into {} values ({})!!VALS!!{}{}".format(table, ", ".join(["%s"]*len(v)), "!!VALS!!".join(str(k) + "!!INT!!" if "int" in str(bd[j]["Type"]) else "'{}'".format(k.replace("\n", "!!NEWLINE!!")) for j, k in enumerate(v.values())), "\n" if i < len(s)-1 else ""))
        b.close()
        return self
    
    def createTable(self, table, outFile = "", printText = True, debug = None, setForeignKeyChecks = False):  
        if debug is None: debug = self.debug
        if setForeignKeyChecks: self.setForeignKeyChecks(0)
        self.source("backup-{}.txt".format(table), outFile, printText, debug) 
        if setForeignKeyChecks: self.setForeignKeyChecks(1)
        return self
    
    def setForeignKeyChecks(self, c):
        self.cursor.execute("set foreign_key_checks = {}".format(c))
        return self
        
    def truncate(self, table, debug = None):
        '''Truncates, or clears all data from the table.'''
        if debug is None: debug = self.debug
        self.backupTable(table)
        t = "truncate {}".format(table)
        self.cursor.execute(t)
        if debug: print(t)
        return self
    
    def showTables(self):
        self.query("show full tables where table_type <> 'VIEW'")
        return self
    
    def showViews(self):
        self.query("show full tables where table_type = 'VIEW'")
        return self
    
    def showFunctions(self):
        self.query("show function status where db = '{}'".format(self.db_name))
        return self
        
    def showProcedures(self):
        self.query("show procedure status where db = '{}'".format(self.db_name))
        return self
    
    def showProcedureParameters(self, procedure):
        self.setArgs(procedure).query("select * from information_schema.parameters where specific_name = %s")
        return self
    
    def callProcedure(self, query, procName, *args):
        try:
            self.cursor.callproc(procName, args)
            self.db.commit()
            self.setArgs(*args).query(query)
        except con.Error as e:
            self.results = (self.__checkError(e.msg), None, None)
        return self
    
    def callFunction(self, query, *args):
        try:
            self.__function = True
            self.setArgs(*args).query(query)
        except con.Error as e:
            self.results = (self.__checkError(e.msg), None, None)
        return self
    ###################################################################
    def update_user_name(self, new_user, old_user):
        user_id = self.callFunction("select get_user_id(%s) as id", old_user).results[2][0]['id']
        if user_id > 0:
            q = "update accounts set user_name = %s where account_id = %s"
            u = self.modify(q, new_user, user_id)
            if "update" in q and "update" in u:
                q = "select * from accounts where user_name = %s"
                self.setArgs(new_user).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("No account exists with user name {}".format(old_user), None, None)
        return self
    
    def reset_password(self, old_user, new_pass):
        user_id = self.callFunction("select get_user_id(%s) as id", old_user).results[2][0]['id']
        q = "update accounts set password = %s where account_id = %s"
        r = self.modify(q, new_pass, user_id)
        if "update" in q and "update" in r:
            q = "select * from accounts where account_id = %s"
            self.setArgs(user_id).query(q)
        else:
            self.results = (r, None, None)
        return self
    
    def set_user_logged_in(self, user_name = ""):
        user_id = self.callFunction("select get_user_id(%s) as id", user_name).results[2][0]['id']
        q = "update logged_in set user_id = %s"
        u = self.modify(q, user_id)
        if "update" in q and "update" in u:
            self.callProcedure("select user_id from logged_in", 'set_search')
            self.query("select if(get_user_id_logged_in() > 0, 'YES', 'NO') as is_logged_in")
        else:
            self.results = (u, None, None)
        return self
          
    def set_current_user(self, user_name = ""):
        user_id = self.callFunction("select get_user_id(%s) as id", user_name).results[2][0]['id']
        q = "update cur_user set user_id = %s"
        u = self.modify(q, user_id)
        if "update" in q and "update" in u:
            self.setArgs(user_id).query("select user_name from accounts where account_id = %s")
        else:
            self.results = (u, None, None)
        return self
            
    def update_artist_name(self, old_artist, new_artist):
        artist_id = self.callFunction("select get_artist_id(%s) as id", old_artist).results[2][0]['id']
        if artist_id > 0:
            q = "update artists set artist_name = %s where artist_id = %s"
            u = self.modify(q, new_artist, artist_id)
            if "update" in q and "update" in u:
                q = "select * from artists where artist_name = %s"
                self.setArgs(new_artist).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("No artist exists with artist name {}".format(old_artist), None, None)
        return self
               
    def update_genre(self, old_genre, new_genre):
        genre_id = self.callFunction("select get_genre_id(%s) as id", old_genre).results[2][0]['id']
        if genre_id > 0:
            q = "update genres set genre = %s where genre_id = %s"
            u = self.modify(q, new_genre, genre_id)
            if "update" in q and "update" in u:
                q = "select * from genres where genre = %s"
                self.setArgs(new_genre).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("No genre exists with genre {}".format(old_genre), None, None)
        return self
               
    def edit_message(self, msg_date, new_msg):
        msg_id = self.callFunction("select get_message_id(%s) as id", msg_date).results[2][0]['id']
        if msg_id > 0:
            q = "update messages set message = %s where message_id = %s"
            u = self.modify(q, new_msg, msg_id)
            if "update" in q and "update" in u:
                q = "select * from messages where message_id = %s"
                self.setArgs(msg_id).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("No message exists with time stamp {}".format(msg_date), None, None)
        return self
            
    def update_playlist(self, playlist_id, new_playlist):
        if playlist_id > 0:
            q = "update playlists set playlist_name = %s where playlist_id = %s"
            u = self.modify(q, new_playlist, playlist_id)
            if "update" in q and "update" in u:
                q = "select * from playlists where playlist_id = %s"
                self.setArgs(playlist_id).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("This playlist doesn't exist.", None, None)
        return self
    
    def update_song_name(self, song_id, new_song):
        if song_id > 0:
            if new_song.strip() == "":
                self.results = ("Song name cannot be empty. Please create a new song name.", None, None)
            else:
                q = "update songs set song_name = %s where song_id = %s"
                u = self.modify(q, new_song, song_id)
                if "update" in q and "update" in u:
                    q = "select * from songs where song_id = %s"
                    self.setArgs(song_id).query(q)
                else:
                    self.results = (u, None, None)
        else:
            self.results = ("This song doesn't exist.", None, None)
        return self
        
    def update_song_artist(self, song_id, new_artist):
        if song_id > 0:
            if new_artist.strip() == "": new_artist = "N/A"
            artist_id = self.callFunction("select get_artist_id(%s) as id", new_artist).results[2][0]['id']
            if artist_id < 1:
                self.callProcedure("select * from artists where artist_name = %s", 'add_artist', new_artist)
                artist_id = self.callFunction("select get_artist_id(%s) as id", new_artist).results[2][0]['id']
            q = "update song_details set artist_id = %s where song_id = %s"
            u = self.modify(q, artist_id, song_id)
            if "update" in q and "update" in u:
                q = "select * from song_details where song_id = %s"
                self.setArgs(song_id).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("This song doesn't exist", None, None)
        return self
        
    def update_song_genre(self, song_id, new_genre):
        if song_id > 0:
            if new_genre.strip() == "": new_genre = "N/A"
            genre_id = self.callFunction("select get_genre_id(%s) as id", new_genre).results[2][0]['id']
            if genre_id < 1:
                self.callProcedure("select * from genres where genre = %s", 'add_genre', new_genre)
                genre_id = self.callFunction("select get_genre_id(%s) as id", new_genre).results[2][0]['id']
            q = "update song_details set genre_id = %s where song_id = %s"
            u = self.modify(q, genre_id, song_id)
            if "update" in q and "update" in u:
                q = "select * from song_details where song_id = %s"
                self.setArgs(song_id).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("This song doesn't exist.", None, None)
        return self
    
    def update_song_description(self, song_id, descr):
        if song_id > 0:
            q = "update song_descriptions set description = %s where song_id = %s"
            u = self.modify(q, descr, song_id)
            if "update" in q and "update" in u:
                q = "select * from song_descriptions where song_id = %s"
                self.setArgs(song_id).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("This song doesn't exist", None, None)
        return self
    
    def increment_song_downloads(self, song_id):
        if song_id > 0:
            down = self.callFunction("select get_song_downloads(%s) as down", song_id).results[2][0]['down']
            q = "update song_downloads set downloads = %s where song_id = %s"
            u = self.modify(q, (down+1), song_id)
            if "update" in q and "update" in u:
                q = "select * from song_downloads where song_id = %s"
                self.setArgs(song_id).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("This song doesn't exist.", None, None)
        return self   
    
    def increment_song_listens(self, song_id):
        if song_id > 0:
            lis = self.callFunction("select get_song_listens(%s) as lis", song_id).results[2][0]['lis']
            q = "update song_listens set listens = %s where song_id = %s"
            u = self.modify(q, (lis+1), song_id)
            if "update" in q and "update" in u:
                q = "select * from song_listens where song_id = %s"
                self.setArgs(song_id).query(q)
            else:
                self.results = (u, None, None)
        else:
            self.results = ("This song doesn't exist.", None, None)
        return self   
    
    def set_order(self, order):
        if order == "desc":
            order = "asc"
        else:
            order = "desc"
        return order
       
    def set_search_home(self, song, user, artist, genre, playlist):
        user_id = self.query("select get_user_id_logged_in() as user_id").results[2][0]['user_id']
        q = "update search_home_songs set song = %s, user = %s, artist = %s, genre = %s, playlist = %s where user_id = %s"
        s = self.modify(q, song, user, artist, genre, playlist, user_id)
        if "update" in q and "update" in s:
            q = "update order_home_songs set song = %s, user = %s, artist = %s, genre = %s, playlist = %s, download = %s, play = %s where user_id = %s"
            self.modify("", "", "", "", "", "", "", user_id)
            q = "select * from search_home_songs where user_id = %s"
            self.setArgs(user_id).query(q)
        else:
            self.results = (s, None, None)
        return self
    
    def set_order_home(self, order):
        user_id = self.query("select get_user_id_logged_in() as user_id").results[2][0]['user_id']
        q = "select {} from order_home_songs where user_id = %s".format(order)
        new_order = self.set_order(self.setArgs(user_id).query(q).results[2][0][order])
        q = "update order_home_songs set {} = %s where user_id = %s".format(order)
        s = self.modify(q, new_order, user_id)
        if "update" in q and "update" in s:
            q = "select {} from order_home_songs where user_id = %s".format(order)
            self.setArgs(user_id).query(q)
        else:
            self.results = (s, None, None)
        return self
    
    def set_search_user(self, song, artist, genre):
        user_id = self.query("select get_user_id_logged_in() as user_id").results[2][0]['user_id']
        q = "update search_user_songs set song = %s, artist = %s, genre = %s where user_id = %s"
        s = self.modify(q, song, artist, genre, user_id)
        if "update" in q and "update" in s:
            q = "update order_user_songs set song = %s, artist = %s, genre = %s, download = %s, play = %s where user_id = %s"
            self.modify("", "", "", "", "", user_id)
            q = "select * from search_user_songs where user_id = %s"
            self.setArgs(user_id).query(q)
        else:
            self.results = (s, None, None)
        return self
    
    def set_order_user(self, order):
        user_id = self.query("select get_user_id_logged_in() as user_id").results[2][0]['user_id']
        q = "select {} from order_user_songs where user_id = %s".format(order)
        new_order = self.set_order(self.setArgs(user_id).query(q).results[2][0][order])
        q = "update order_user_songs set {} = %s where user_id = %s".format(order)
        s = self.modify(q, new_order, user_id)
        if "update" in q and "update" in s:
            q = "select {} from order_user_songs where user_id = %s".format(order)
            self.setArgs(user_id).query(q)
        else:
            self.results = (s, None, None)
        return self
    
    def set_search_accounts(self, user, admin):
        user_id = self.query("select get_user_id_logged_in() as user_id").results[2][0]['user_id']
        q = "update search_accounts set user = %s, admin = %s where user_id = %s"
        s = self.modify(q, user, admin, user_id)
        if "update" in q and "update" in s:
            q = "update order_accounts set id = %s, user = %s, password = %s, admin = %s, songs = %s, playlists = %s where user_id = %s"
            self.modify("", "", "", "", "", "", user_id)
            q = "select * from search_accounts where user_id = %s"
            self.setArgs(user_id).query(q)
        else:
            self.results = (s, None, None)
        return self
    
    def set_order_accounts(self, order):
        user_id = self.query("select get_user_id_logged_in() as user_id").results[2][0]['user_id']
        q = "select {} from order_accounts where user_id = %s".format(order)
        new_order = self.set_order(self.setArgs(user_id).query(q).results[2][0][order])
        q = "update order_accounts set {} = %s where user_id = %s".format(order)
        s = self.modify(q, new_order, user_id)
        if "update" in q and "update" in s:
            q = "select {} from order_accounts where user_id = %s".format(order)
            self.setArgs(user_id).query(q)
        else:
            self.results = (s, None, None)
        return self
    
    def delete_user(self, user_name):
        user_id = self.callFunction("select get_user_id(%s) as id", user_name).results[2][0]['id']
        log_user_id = self.query("select get_user_id_logged_in() as id").results[2][0]['id']
        if user_id == log_user_id:
            self.results = ("Cannot delete user. User is already logged in.", None, None)
        else:
#             sizes = {"songs": 0, "playlists": 0, "admins": 0}
#             for t, _ in sizes:  
#                 q = "select * from {} where user_id = %s".format(t)
#                 sizes[t] = len(self.setArgs(user_id).query(q).results[2])
            q = "delete from accounts where account_id = %s"
            d = self.modify(q, user_id)
            if "delete" in q and "delete" in d:
                q = "update manage_songs"
                self.query("select * from accounts")
            else:
                self.results = (d, None, None)
        return self
    
    def remove_admin(self, user_name):
        admin_id = self.callFunction("select get_admin_id(get_user_id(%s)) as id", user_name).results[2][0]['id']
        if admin_id > 0:
            q = "delete from admins where admin_id = %s"
            d = self.modify(q, admin_id)
            if "delete" in q and "delete" in d:
                self.query("select * from admins")
            else:
                self.results = (d, None, None)
        else:
            self.results = ("No admin exists with user name {}".format(user_name))
        return self
    
    def remove_message(self, msg_date):
        msg_id = self.callFunction("select get_message_id(%s) as id", msg_date).results[2][0]['id']
        if msg_id > 0:
            q = "delete from messages where message_id = %s"
            d = self.modify(q, msg_id)
            if "delete" in q and "delete" in d:
                self.query("select * from messages")
            else:
                self.results = (d, None, None)
        else:
            self.results = ("No message exists with time stamp {}".format(msg_date), None, None)
        return self
    
    def delete_playlist(self, playlist_id):
        if playlist_id > 0:
            q = "delete from playlists where playlist_id = %s"
            d = self.modify(q, playlist_id)
            if "delete" in q and "delete" in d:
                self.query("select * from playlists")
            else:
                self.results = (d, None, None)
        else:
            self.results = ("This playlist doesn't exist.", None, None)
        return self
    
    def delete_song(self, song_id):
        if song_id > 0:
            q = "delete from songs where song_id = %s"
            d = self.modify(q, song_id)
            if "delete" in q and "delete" in d:
                self.query("select * from songs")
            else:
                self.results = (d, None, None)
        else:
            self.results = ("This song doesn't exist.", None, None)
        return self
    
    def remove_song_from_playlist(self, playlist_id, song_id):
        q = "delete from contained where playlist_id = %s and song_id = %s"
        d = self.modify(q, playlist_id, song_id)
        if "delete" in q and "delete" in d:
            self.setArgs(playlist_id).query("select * from contained where playlist_id = %s")
        else:
            self.results = (d, None, None)
        return self
    ###########################################################################################
    def close(self):
        self.db.close()
      
class SshSql(PySql):
    def __init__(self, ssh_host, ssh_user, ssh_password, db_user, db_password, database, debug = False):
        try:
            self.tunnel = ssh((ssh_host), ssh_username = ssh_user, ssh_password = ssh_password, remote_bind_address = ('127.0.0.1', 3306)) 
            self.tunnel.start()
            PySql.__init__(self, '127.0.0.1', db_user, db_password, database, self.tunnel.local_bind_port, debug)
        except:
            sys.exit("Remote connection failed.")

    def close(self):
        try:
            PySql.close(self)
            self.tunnel.close() 
        except:
            pass
        
class AccessSql(SshSql, PySql):
    PY_ACCESS = "py"
    SSH_ACCESS = "ssh"
    
    def __init__(self, debug = False, path = "access.txt", accessType = PY_ACCESS, decode = None):
        access = {}
        with open(path, encoding = "utf-8") as f:
            for line in f:
                (key, val) = [s.strip() for s in line.split(":")]
                if not decode is None:
                    if "password" in key.lower():
                        val = decode(val).text()
                access[key] = val
        access["debug"] = debug
        self.__access = {self.PY_ACCESS: PySql, self.SSH_ACCESS: SshSql}[accessType]
        try:
            self.__access.__init__(self, **access)
        except:
            sys.exit("Accessing connection failed.")
      
    def close(self):
        try:
            self.__access.close(self)
        except:
            pass
            
class QtWorkbenchSql(ParentWindow):
    class _Form(Form):
        class Add(ScrollChildButton):
            def __init__(self, mainForm, *text):
                super().__init__(mainForm.index, *text)
                self.mainForm = mainForm
                                 
            def mouseLeftReleased(self):
                ScrollChildButton.mouseLeftReleased(self)
                self.mainForm.newConnection()
                             
        class Manage(ScrollChildButton):
            def __init__(self, mainForm, *text):
                super().__init__(mainForm.index, *text)
                self.mainForm = mainForm
                                 
        class Connect(ScrollChildButton):
            def __init__(self, mainForm, *text):
                super().__init__(mainForm.index, *text)
                self.setFixedSize(300, 125)
                self.mainForm = mainForm
                                 
        class SetupConnection(Window):
            class Combo(ComboBox):
                def __init__(self, setupConn):
                    super().__init__()
                    self.start = False
                    items = ("Standard (TCP/IP)", "Standard (TCP/IP) over SSH")
                    group = (setupConn.standard, setupConn.standardSSH)
                    height = (230, 300)
                    self.items = dict(zip(items, tuple(zip(group, self.__access(), height))))
                    self.setupConn = setupConn
                    self.addItems(self.items.keys())
                    
                def __access(self):
                    b = (True, False)
                    p = (AccessSql.PY_ACCESS, PySql)
                    s = (AccessSql.SSH_ACCESS, SshSql)
                    return tuple([dict(zip(b, a)) for a in [p, s]])
                   
                def textChanged(self):
                    ComboBox.textChanged(self)
                    if not self.start:
                        self.start = True
                    else:
                        for s in self.items:
                            group, _, height = self.items[s]
                            b = s == self.currentText()
                            group.setVisible(b)
                            if b:
                                self.setupConn.setFixedHeight(height+30)
                
            class TestConnection(Button):
                class ErrorMessage(MessageBox):
                    def __init__(self):
                        super().__init__("Please enter a name for the connection", MessageBox.CRITICAL_ICON)
                    
                    def setupWindow(self):
                        MessageBox.setupWindow(self)
                        self.setWindowTitle("Qt Workbench")
                        
                    def hideEvent(self, QEvent):
                        if self.checkParentWindow():
                            p = self.getParentWindow()
                            p.setEnabled(True)
                            self.ok.leaveEvent(QEvent)
                            p.setFocus()
                            self.removeWindow()
                            
                    def changeEvent(self, QEvent):
                        MessageBox.changeEvent(self, QEvent)
                        if self.checkParentWindow():
                            p = self.getParentWindow()
                            p.setEnabled(False)
                            search = SearchForm().searchNames("ok")
                            ok = p.searchObjects(search).mergeResults().results["ok"]
                            self.ok = ok
                    
                def __init__(self, comboBox, *text):
                    super().__init__(*text)
                    self.comboBox = comboBox
                  
                def testConnection(self, isAccess = False):
                    comboBox = self.comboBox
                    group, access, _ = comboBox.items[comboBox.currentText()]                    
                    results = group.searchObjects(SearchForm().searchClasses(TextBox)).mergeResults().resultValues().results
                    keys = tuple(results.keys())
                    for r in keys:
                        if "schema" in r:
                            n = "database"
                        else:
                            n = r.replace("name", "").replace("MySql", "db").replace(":", "").strip().replace(" ", "_").lower()
                        results[n] = results.pop(r)
                    try:
                        if isAccess:
                            setupConn = comboBox.setupConn
                            search = SearchForm().searchNames("connection name", "Debug")
                            results = setupConn.searchObjects(search).mergeResults().resultValues().results
                            name, debug = tuple(results.values())
                            if name == "":
                                setupConn.setChildWindows(self.ErrorMessage())
                                return None
                            path = self.createConnection(name, results)
                            c = AccessSql(debug, path, access[isAccess], Decode)
                        else:
                            c = access[isAccess](**results)
                        return c
                    except SystemExit as e:
                        print(e)
                        return None
                    
                def createConnection(self, name, results):
                    results = str(results)[1:-1].replace(", ", "\n").replace("'", "")
                    conns = "{}//connections".format(os.getcwd())
                    if not os.path.exists(conns):
                        os.mkdir(conns)
                    create = "{}//{}.txt".format(conns, name)
                    c = open(create, "w")    
                    c.write(results)
                    c.close()
                    return create
                    
                def mouseLeftReleased(self):
                    Button.mouseLeftReleased(self)
                    self.testConnection()
                    
            class Cancel(Button):
                def __init__(self, setupConn, *text):
                    super().__init__(*text)
                    self.setupConn = setupConn
                    
                def mouseLeftReleased(self):
                    Button.mouseLeftReleased(self)
                    self.setupConn.close()
                    
            class Ok(Button):
                def __init__(self, setupConn, *text):
                    super().__init__(*text)
                    self.setupConn = setupConn
                    
                def mouseLeftReleased(self):
                    Button.mouseLeftReleased(self)
                    search = SearchForm().searchNames("test")
                    test = self.setupConn.searchObjects(search).mergeResults().results["test"]
                    test.testConnection(True)
                
            def __init__(self, mainForm):
                self.mainForm = mainForm
                self.font = mainForm.getFont()
                self.add = tuple(mainForm.searchObjects(SearchForm().searchNames("new")).mergeResults().results.values())[0]
                self.scrollArea = self.add.getScrollArea()
                super().__init__(flags=Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
                 
            def setupWindow(self):
                Window.setupWindow(self)
                self.setWindowTitle("Setup New Connection")
                self.scrollArea.setEnabled(False)
                g = Form()
                g.setFont(self.font)
                g.addTextBox("127.0.0.1", "Host name:", False).addRow()
                g.addTextBox("root", "Username:", False).addRow()
                g.addPassword().addRow()
                g.addTextBox(message="Enter default schema name (Optional)").addRow() 
                self.standard = g.group() 
                g = Form()
                g.setFont(self.font)
                g.addTextBox("127.0.0.1", "SSH Host name:", False).addRow()
                g.addTextBox("user", "SSH Username:", False).addRow()
                g.addPassword(message="SSH").addRow()
                g.addTextBox("root", "MySql Username:", False).addRow()
                g.addPassword(message="MySql").addRow()
                g.addTextBox(message="Enter MySql default schema name (Optional)").addRow()
                self.standardSSH = g.group()
                f = Form(self)
                f.setFont(self.font)
                f.addTextBox(message="Enter a connection name").addRow()
                f.addLabel("Connection method:")
                c = self.Combo(self)
                f.addComboBox(c).addRow()
                self.standardSSH.setVisible(False)
                for g in (self.standard, self.standardSSH):
                    f.addGroup(g).addRow()
                names = ("Test Connection", "Cancel", "Ok")
                attributes = ("test", "cancel", "ok")
                actionClasses = (self.TestConnection, self.Cancel, self.Ok)
                params = ([c], [self], [self])
                width = (125, 60, 32)
                buttons = tuple(zip(names, attributes, actionClasses, params, width))
                for (name, attribute, actionClass, params, width) in buttons:
                    params.append(ButtonText(name, attribute))
                    b = actionClass(*params)
                    b.setObjectName(attribute)
                    b.setFixedSize(width, 25)
                    b.addTextToGrid(attribute)
                    f.addButton(b)
                f.addCheckBox("Debug").addRow(Qt.AlignCenter)
                self.setFixedHeight(260)
                self.childForm = f
                self.childForm.layout()
                
            def searchObjects(self, searchForm):
                return self.childForm.searchObjects(searchForm)
                
            def closeEvent(self, QEvent):
                self.scrollArea.setEnabled(True)
                self.add.leaveEvent(QEvent)
                Window.closeEvent(self, QEvent)
               
        def __init__(self, parent = None):
            super().__init__(parent)
            self.index = 1
            title = QLabel("Qt Connections")
            title.setFont(self.getFont(16))
            title.setFixedWidth(190)
            self.addLabel(label=title)
            buttons = (self.Add, self.Manage)
            names = ("New connection", "Manage connections")
            width = (125, 160)
            b = tuple(zip(buttons, names, width))
            for i in b:
                self.addButton(self.titleButton(*i))
            self.addRow().isAddingItems(True).setRowSize(6)
                
        def getFont(self, size = 10):
            if self.getParent() is None:
                font = QFont()
                font.setFamily("Times New Roman")
                font.setPointSize(size)
                font.setBold(True)
                font.setWeight(75)
                return font
            return self.getParent().getFont(size)
        
        def connection(self, name):
            width = 300
            name = ButtonText(name, "name") 
            name.setFixedSize(width, 25)
            name.setFont(self.getFont(14))
            user = ButtonText("User: user", "user") 
            user.setFont(self.getFont())
            user.setAlignment(Qt.AlignTop)
            host = ButtonText("Host: host", "host")  
            host.setFont(self.getFont())
            host.setAlignment(Qt.AlignTop)
            c = self.Connect(self, name, user, host)
            self.index += 1
            c.addTextToGrid("name", Qt.AlignTop)
            c.addBoxLayoutToGrid(BoxLayout(BoxLayout.ALIGN_VERTICAL, "user", "host"), Qt.AlignBottom)  
            return c
                    
        def titleButton(self, actionClass, name, width):
            height = 25
            bname = ButtonText(name, "name") 
            bname.setFixedSize(width, height)
            bname.setFont(self.getFont())
            t = actionClass(self, bname)
            t.setObjectName(name)
            t.setFixedSize(width, height)
            self.index += 1
            t.addTextToGrid("name")
            return t
         
        def newConnection(self):
            self.getParent().setChildWindows(self.SetupConnection(self))
            #self.addButton(self.connection("d"))
               
    def __init__(self):
        app = QApplication(sys.argv)
        super().__init__()
        sys.exit(app.exec_())  
        
    def setupWindow(self):
        ParentWindow.setupWindow(self)
        self.showMaximized()
        self.setWindowTitle("Qt Workbench")
        group = self._Form(self).group()
        group.setObjectName("box")
        sc = ScrollArea(group)
        sc.setObjectName("scroll")
        s = Style()
        s.setWidget("QWidget#scroll")
        s.setAttribute("background-color", "white")
        s.setAttribute("border", "0")
        s.setWidget("QWidget#box")
        s.setAttribute("border", "0")
        sc.setStyleSheet(s.css())
        sc.setParent(self)
        QVBoxLayout(self).addWidget(sc)
