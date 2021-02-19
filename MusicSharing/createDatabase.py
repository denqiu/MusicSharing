from pySql import *
import os

class Execute(ExecuteSql):
    def __init__(self, title, db=None, printText=True, debug=False):
        path = os.getcwd()
        user = os.path.basename(path)
        self.currentUser = user
        if db is None:
            print("Current User: {}".format(user))
        path = "{}\\{}.txt".format(path, user)
        ExecuteSql.__init__(self, title, db, printText, debug, path, AccessSql.SSH_ACCESS)
        
    def accounts(self, index):
        return index
    
    def messages(self, index):
        return index
     
    def songs(self, index):
        return index 
    
    def playlists(self, index):
        return index
    
    def users(self, index):
        return index
    
    def searchAndOrder(self, index):
        return index
   
    def execute(self, i = 1):
        i = self.accounts(i)
        i = self.messages(i)
        i = self.songs(i)
        i = self.playlists(i)
        i = self.users(i)
        return self.searchAndOrder(i)
        
class Creates(CreateSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        CreateSql.__init__(self, db, printText, debug, Execute)
        self.dropCreateDatabase("music_sharing")
        self.start()
      
    def accounts(self, index):
        aid, code = self.begin_table("accounts")
        code.setBinary(True).setColumns("varchar(255)", "username")
        code.setBinary(False).setColumns("varchar(255)", "password")
        code.setKeys("primary", aid)
        code.setKeys("unique", "username")
        code.setKeys("index", "password")
        index = self.createTable("accounts", code, True, False, index)
        admin, code = self.begin_table("admins")
        code.setColumns("int", "user_id")
        code.setKeys("primary", admin)
        code.setForeignIds("accounts").renameForeignKeys("user_id")
        code.setKeys("index", "user_id")
        return self.createTable("admins", code, True, False, index)
    
    def messages(self, index):
        mid, code = self.begin_table("messages")
        code.setBinary(True).setColumns("varchar(255)", "message")
        code.setBinary(False).setColumns("datetime", "timestamp")
        code.setKeys("primary", mid)
        code.setKeys("index", "message", "timestamp")
        index = self.createTable("messages", code, True, False, index)-1
        tables = ("received", "sent")
        accounts_id = ("recipient_id", "sender_id")
        tables = tuple(zip(tables, accounts_id))
        for (table, accounts_id) in tables:
            tid, code = self.begin_table(table)
            code.setColumns("int", accounts_id)
            code.setKeys("primary", tid).renamePrimaryKey("messages_id")
            code.setForeignIds("messages", "accounts").renameForeignKeys(accounts_id)
            code.setKeys("index", accounts_id)
            index = self.createTable(table, code, False, False, index+1)
        return index+1
    
    def songs(self, index):
        tables = ("artists", "genres")
        names = ("artist_name", "genre_name")
        tables = tuple(zip(tables, names))
        for (table, name) in tables:
            tid, code = self.begin_table(table)
            code.setBinary(True).setColumns("varchar(255)", name)
            code.setBinary(False)
            code.setKeys("primary", tid)
            code.setKeys("unique", name)
            index = self.createTable(table, code, True, False, index)
        sid, code = self.begin_table("songs")
        code.setColumns("int", "user_id")
        code.setBinary(True).setColumns("varchar(255)", "song_name")
        code.setBinary(False)
        code.setKeys("primary", sid)
        code.setForeignIds("accounts").renameForeignKeys("user_id")
        code.setKeys("index", "user_id", "song_name")
        index = self.createTable("songs", code, True, False, index)-1
        tables = ("description", "listens", "downloads")
        colType = ("varchar(255)", "int", "int")
        tables = tuple(zip(tables, colType))
        for (name, colType) in tables:
            table = "song_{}".format(name)
            tid, code = self.begin_table(table)
            code.setColumns(colType, name)
            code.setKeys("primary", tid).renamePrimaryKey("songs_id")
            code.setForeignIds("songs")
            code.setKeys("index", name)
            index = self.createTable(table, code, False, False, index+1)
        details, code = self.begin_table("song_details")
        code.setColumns("int", "artists_id", "genres_id")
        code.setKeys("primary", details).renamePrimaryKey("songs_id")
        code.setForeignIds("songs", "artists", "genres")
        code.setKeys("index", "artists_id", "genres_id")
        return self.createTable("song_details", code, False, False, index+1)

    def playlists(self, index):
        pid, code = self.begin_table("playlists")
        code.setColumns("int", "user_id")
        code.setBinary(True).setColumns("varchar(255)", "playlist_name")
        code.setBinary(False)
        code.setKeys("primary", pid)
        code.setForeignIds("accounts").renameForeignKeys("user_id")
        code.setKeys("index", "user_id", "playlist_name")
        index = self.createTable("playlists", code, True, False, index+1)
        _, code = self.begin_table("contained")
        code.pop(0)
        code.setColumns("int", "playlists_id", "songs_id")
        code.setForeignIds("playlists", "songs")
        code.setKeys("index", "playlists_id", "songs_id")
        return self.createTable("contained", code, False, False, index)
    
    def users(self, index):
        tables = ("logged_in", "cur_user")
        for t in tables:
            _, code = self.begin_table(t)
            code.pop(0)
            code.setNull(True).setDefault(0).setColumns("int", "user_id")
            code.setKeys("primary", "user_id")
            index = self.createTable(t, code, False, False, index+1)
            self.db.modify("insert into {} values ()".format(t))
        return index
    
    def __searchOrOrder(self, index, table, *columns):
        columns = list(columns)
        _, code = self.begin_table(table)
        code.pop(0)
        if not "_accounts" in table:
            code.setDefault(0)
        code.setNull(True).setColumns("int", "user_id")
        accounts = table == "search_accounts"
        if accounts:
            c = columns.pop()
        code.setNull(False).setDefault("''").setColumns("varchar(255)", *columns)
        if accounts:
            code.setDefault("'ALL'").setColumns("varchar(255)", c)
        code.setKeys("primary", "user_id")
        index = self.createTable(table, code, False, False, index+1)
        self.db.modify("insert into {} values ()".format(table))
        return index
    
    def searchAndOrder(self, index):
        index = self.__searchOrOrder(index, "search_home_songs", "song", "user", "artist", "genre", "playlist")
        index = self.__searchOrOrder(index, "search_user_songs", "song", "artist", "genre")
        index = self.__searchOrOrder(index, "search_accounts", "user", "admin")
        index = self.__searchOrOrder(index, "order_home_songs", "song", "user", "artist", "genre", "playlist", "download", "play")
        index = self.__searchOrOrder(index, "order_user_songs", "song", "artist", "genre", "download", "play")
        index = self.__searchOrOrder(index, "order_accounts", "user", "password", "admin", "songs", "playlists")
        return index
    
class Checks(CheckSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        CheckSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        i = CheckSql.execute(self, i)
        var = ("low", "up", "num")
        val = ("a-z", "A-Z", "0-9")
        statements = tuple(zip(var, val))
        code = WriteSql()
        for (var, val) in statements:
            code.append("set @{} = cast(pass as binary) regexp binary '[{}]'".format(var, val))
        f = "call set_error('Password must contain upper and lower case letters and numbers.');"
        code.append("if not (@low and @up and @num) then \n\t\t\t{}\n\t\tend if;".format(f))
        self.createProcedure("password_conditions", "in pass varchar(255)", code, i)
        
class Gets(GetSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        GetSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def accounts(self, index):
        return index
        
class Triggers(TriggerSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        TriggerSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def accounts(self, index):
        code = WriteSql()
        columns = ("username", "password")
        for c in columns:
            code.append("call check_empty('{0}', new.{0})".format(c))
        index = self.manageTrigger("accounts", code, index)
        code.clear()
        pas = WriteSql()
        pas.append("call check_empty('{0}', new.{0})".format("password"))
        error = "call set_error('This password is already in use. Please create a new password.');"
        pas.append("if binary old.password = new.password then\n\t\t\t\t{}\n\t\t\tend if".format(error))
        pas.append("call password_conditions(new.password);")
        pas.separator = ";\n\t\t\t"
        user = "call check_empty('{0}', new.{0});".format("username")
        code.append("if old.username = new.username then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(pas, user))
        index = self.createTrigger("before_update_accounts", "before update", "accounts", code, index)
        code.clear()
        code.append("call check_id(new.{0}, '{0}')".format("user_id"))
        return self.manageTrigger("admins", code, index)
    
    def messages(self, index):
        code = "set new.timestamp = now()"
        index = self.manageTrigger("messages", WriteSql(), index, code)
        index = self.createTrigger("before_update_messages_timestamp", "before update", "messages", code+";", index)
        tables = ("received", "sent")
        for t in tables:
            code = "set new.messages_id = manage_messages_id();"
            index = self.createTrigger("before_insert_{}".format(t), "before insert", t, code, index)
        return index
    
    def songs(self, index):
        tables = ("songs", "artists", "genres")
        names = ("song_name", "artist_name", "genre_name")
        tables = tuple(zip(tables, names))
        for (table, name) in tables:
            code = WriteSql()
            code.append("call check_empty('{0}', new.{0})".format(name))
            index = self.manageTrigger(table, code, index)
        return index
    
    def playlists(self, index):
        code = WriteSql()
        code.append("call check_empty('{0}', new.{0})".format("playlist_name"))
        return self.manageTrigger("playlists", code, index)
    
    def execute(self, i=1):
        i = Execute.execute(self, i)
        return self.deleteTrigger(i, "accounts", "admins", "messages", "songs", "artists", "genres", "playlists")
        