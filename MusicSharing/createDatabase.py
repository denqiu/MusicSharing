from pySql import *
import os

class Execute(ExecuteSql):
    def __init__(self, title, db=None, printText=True, debug=False):
        ExecuteSql.__init__(self, title, db, printText, debug, accessType=AccessSql.SSH_ACCESS)
        
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
        
    def attribute(self, table, attr, colType, index):
        a, name, code = self.begin_table("{}_{}".format(table, attr))
        code.setColumns(colType, attr)
        code.setKeys("primary", a).renamePrimaryKey("{}_{}".format(table, "id"))
        code.setForeignIds(table).deleteCascade().updateCascade()
        code.setKeys("index", attr)
        return self.createAndAddToManageColumns(name, code, False, index)
      
    def date(self, table, index):
        return self.attribute(table, "date", "datetime", index)
   
    def accounts(self, index):
        aid, table, code = self.begin_table("account")
        code.setBinary(True).setColumns("varchar(255)", "username")
        code.setBinary(False).setColumns("varchar(255)", "password")
        code.setKeys("primary", aid)
        code.setKeys("unique", "username")
        code.setKeys("index", "password")
        index = self.createTable(table, code, True, False, index)
        index = self.date(table, index)
        tables = ("admin", "follow")
        for table in tables:
            tid, _, code = self.begin_table(table)
            code.setColumns("int", "user_id")
            code.setKeys("primary", tid)
            code.setForeignIds("account").renameForeignKeys("user_id").deleteCascade().updateCascade()
            code.setKeys("index", "user_id")
            index = self.createTable(table, code, True, False, index)   
        return index
    
    def messages(self, index):
        mid, table, code = self.begin_table("message")
        code.setBinary(True).setColumns("varchar(255)", "message")
        code.setBinary(False).setColumns("datetime", "date")
        code.setKeys("primary", mid)
        code.setKeys("index", "message", "date")
        index = self.createTable(table, code, True, False, index)-1
        tables = ("recipient", "sender")
        for table in tables:
            tid, _, code = self.begin_table(table)
            code.setColumns("int", tid)
            code.setKeys("primary", tid).renamePrimaryKey("message_id")
            code.setForeignIds("message", "account").renameForeignKeys(tid).deleteCascade().updateCascade()
            code.setKeys("index", tid)
            index = self.createAndAddToManageColumns(table, code, False, index+1)
        return index+1
    
    def songs(self, index):
        tables = ("artist", "genre")
        for table in tables:
            tid, _, code = self.begin_table(table)
            name = table + "_name"
            code.setBinary(True).setColumns("varchar(255)", name)
            code.setBinary(False)
            code.setKeys("primary", tid)
            code.setKeys("unique", name)
            index = self.createTable(table, code, True, False, index)
        sid, table, code = self.begin_table("song")
        code.setColumns("int", "user_id")
        code.setBinary(True).setColumns("varchar(255)", "song_name")
        code.setBinary(False)
        code.setKeys("primary", sid)
        code.setForeignIds("account").renameForeignKeys("user_id").deleteCascade().updateCascade()
        code.setKeys("index", "user_id", "song_name")
        index = self.createTable(table, code, True, False, index)
        index = self.date(table, index)+1
        comment, table, code = self.begin_table("comment")
        code.setColumns("varchar(255)", "comment")
        code.setColumns("datetime", "date")
        code.setKeys("primary", comment)
        code.setKeys("index", "comment", "date")
        index = self.createTable(table, code, True, False, index)
        comment, table, code = self.begin_table("song_comment")
        code.setColumns("int", "user_id", "song_id")
        code.setKeys("primary", comment).renamePrimaryKey("comment_id")
        code.setForeignIds("comment", "account", "song").renameForeignKeys("user_id", "account_id")
        code.setKeys("index", "user_id", "song_id")
        index = self.createAndAddToManageColumns(table, code, False, index)
        attributes = ("file", "description", "plays", "downloads")
        colType = tuple(["varchar(255)"]*2+["int"]*2)
        attributes = tuple(zip(attributes, colType))
        for (attr, colType) in attributes:
            index = self.attribute("song", attr, colType, index+1)
        details, table, code = self.begin_table("song_details")
        code.setColumns("int", "artist_id", "genre_id")
        code.setKeys("primary", details).renamePrimaryKey("song_id")
        code.setForeignIds("song", "artist", "genre").deleteCascade().updateCascade()
        code.setKeys("index", "artist_id", "genre_id")
        return self.createTable(table, code, False, False, index+1)

    def playlists(self, index):
        pid, table, code = self.begin_table("playlist")
        code.setColumns("int", "user_id")
        code.setBinary(True).setColumns("varchar(255)", "playlist_name")
        code.setBinary(False)
        code.setKeys("primary", pid)
        code.setForeignIds("account").renameForeignKeys("user_id").deleteCascade().updateCascade()
        code.setKeys("index", "user_id", "playlist_name")
        index = self.createTable(table, code, True, False, index+1)
        pub, table, code = self.begin_table("public")
        code.setColumns("int", "playlist_id")
        code.setKeys("primary", pub)
        code.setForeignIds("playlist")
        code.setKeys("index", "playlist_id")
        index = self.createTable(table, code, True, False, index)
        index = self.date("playlist", index)+1
        item, table, code = self.begin_table("item")
        code.setColumns("int", "playlist_id", "song_id")
        code.setKeys("primary", item)
        code.setForeignIds("playlist", "song").deleteCascade().updateCascade()
        code.setKeys("index", "playlist_id", "song_id")
        return self.createTable(table, code, True, False, index)-1
    
    def users(self, index):
        tables = ("logged_in", "cur_user")
        for t in tables:
            _, _, code = self.begin_table(t)
            code.pop(0)
            code.setNull(True).setDefault(0).setColumns("int", "user_id")
            code.setKeys("primary", "user_id")
            index = self.createTable(t, code, False, False, index+1)
            self.db.modify("insert into {} values ()".format(t))
        return index
#     
#     def __searchOrOrder(self, index, table, *columns):
#         columns = list(columns)
#         _, code = self.begin_table(table)
#         code.pop(0)
#         if not "_accounts" in table:
#             code.setDefault(0)
#         code.setNull(True).setColumns("int", "user_id")
#         accounts = table == "search_accounts"
#         if accounts:
#             c = columns.pop()
#         code.setNull(False).setDefault("''").setColumns("varchar(255)", *columns)
#         if accounts:
#             code.setDefault("'ALL'").setColumns("varchar(255)", c)
#         code.setKeys("primary", "user_id")
#         index = self.createTable(table, code, False, False, index+1)
#         self.db.modify("insert into {} values ()".format(table))
#         return index
#     
#     def searchAndOrder(self, index):
#         index = self.__searchOrOrder(index, "search_home_songs", "song", "user", "artist", "genre", "playlist")
#         index = self.__searchOrOrder(index, "search_user_songs", "song", "artist", "genre")
#         index = self.__searchOrOrder(index, "search_accounts", "user", "admin")
#         index = self.__searchOrOrder(index, "order_home_songs", "song", "user", "artist", "genre", "playlist", "download", "play")
#         index = self.__searchOrOrder(index, "order_user_songs", "song", "artist", "genre", "download", "play")
#         index = self.__searchOrOrder(index, "order_accounts", "user", "password", "admin", "songs", "playlists")
#         return index
#     
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
        i = self.createProcedure("password_conditions", "in pass varchar(255)", code, i)
        code.clear()
        var = ("ogg", "wav", "mp3")
        code = WriteSql()
        for v in var:
            code.append("set @{0} = format like '%.{0}'".format(v))
        f = "call set_error('Please select an audio file of the following formats: ogg, wav, or mp3.');"
        code.append("if not (@ogg or @wav or @mp3) then \n\t\t\t{}\n\t\tend if;".format(f))
        self.createProcedure("check_audio_format", "in format varchar(255)", code, i)
         
class Gets(GetSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        GetSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def attribute(self, table, attr, returnType, index):
        return self.get("{}_{}".format(table, attr), returnType, attr, False, False, index, whereTable=table)
        
    def date(self, table, index):
        return self.attribute(table, "date", "datetime", index)
        
    def accounts(self, index):
        index = self.getId("account", "user varchar(255)", "user_name = user", index)
        cols = ("user_name", "password")
        for c in cols:
            index = self.get("account", "varchar(255)", c, True, False, index)
        index = self.date("account", index)
        tables = ("admin", "follow")
        for t in tables:
            index = self.getId(t, "uid int", "user_id = uid", index)
            index = self.get(t, "int", "user_id", True, False, index)
            index = self.get(t, "varchar(255)", "user", True, True, index, functionName="account_user_name")
        return index
    
    def messages(self, index):
        index = self.getId("message", "d datetime", "date = d", index)
        cols = ("message", "date")
        colTypes = ("varchar(255)", "datetime")
        cols = tuple(zip(cols, colTypes))
        for i, (c, colType) in enumerate(cols):
            index = self.get("message", colType, c, i > 0, False, index)
        tables = ("recipient", "sender")
        for t in tables:
            index = self.getId(t, "mid int", "message_id = mid", index)
            index = self.get(t, "varchar(255)", "", False, True, index, functionName="account_user_name")
        return index
    
    def songs(self, index):
        tables = ("artist", "genre")
        for t in tables:
            col = t+"_name"
            index = self.getId(t, "name varchar(255)", col, index)
            index = self.get(t, "varchar(255)", col, False, False, index)
        index = self.getId("song", "uid int, song varchar(255)", "user_id = uid and song_name = song", index)
        cols = ("user_id", "song_name")
        colTypes = ("int", "varchar(255)")
        cols = tuple(zip(cols, colTypes))
        for i, (c, colType) in enumerate(cols):
            index = self.get("song", colType, c, i < 1, False, index)
        index = self.get("song", "varchar(255)", "user", True, True, index, functionName="account_user_name")
        index = self.date("song", index)
        index = self.getId("comment", "d datetime", "date = d", index)
        cols = ("comment", "date")
        colTypes = ("varchar(255)", "datetime")
        cols = tuple(zip(cols, colTypes))
        for i, (c, colType) in enumerate(cols):
            index = self.get("comment", colType, c, i > 0, False, index)
        cols = ("user", "song")
        functionNames = ("account_user_name", "song")
        cols = tuple(zip(cols, functionNames))
        for (c, name) in cols:
            index = self.getId(c, "cid int", "comment_id = cid", index, "song_comment", table_in_name=True)
            index = self.get("song_comment", "varchar(255)", c, True, True, index, functionName=name)
        attributes = ("file", "description", "plays", "downloads")
        returnType = tuple(["varchar(255)"]*2+["int"]*2)
        attributes = tuple(zip(attributes, returnType))
        for (attr, returnType) in attributes:
            index = self.attribute("song", attr, returnType, index)
        tables = ("artist", "genre")
        for t in tables:
            index = self.getId(t, "sid int", "song_id = sid", index, "song_details", table_in_name=True)
            index = self.get("song_details", "varchar(255)", t, True, True, index, functionName=t)
        return index
    
    def playlists(self, index):
        index = self.getId("playlist", "uid int, playlist varchar(255)", "user_id = uid and playlist_name = playlist", index)
        cols = ("user_id", "playlist_name")
        colTypes = ("int", "varchar(255)")
        cols = tuple(zip(cols, colTypes))
        for i, (c, colType) in enumerate(cols):
            index = self.get("playlist", colType, c, i < 1, False, index)
        index = self.get("playlist", "varchar(255)", "user", True, True, index, functionName="account_user_name")
        index = self.date("playlist", index)
        index = self.getId("public", "pid int", "playlist_id = pid", index)
        index = self.get("public", "varchar(255)", "playlist", True, True, index)
        index = self.getId("item", "pid int, sid int", "playlist_id = pid and song_id = sid", index)
        cols = ("playlist", "song")
        functionNames = ("playlist", "song")
        cols = tuple(zip(cols, functionNames))
        for (c, name) in cols:
            index = self.getId(c, "i int", "item_id = i", index, "item", table_in_name=True)
            index = self.get("item", "varchar(255)", c, True, True, index, functionName=name)
        return index

class Triggers(TriggerSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        TriggerSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def table(self, t, code, index):
        actions = ("insert", "update")
        for a in actions:
            index = self.createTrigger("before_{}_{}".format(a, t), "before {}".format(a), t, code, index)
        return index
    
    def date(self, table, index):
        return self.table(table+"_date", "set new.date = now();", index)

    def accounts(self, index):
        code = WriteSql()
        for c in ("username", "password"):
            code.append(self.codeEmptyCheck(c))
        index = self.manageTrigger("account", code, index)
        code.clear()
        pas = WriteSql()
        pas.append("call check_empty('{0}', new.{0})".format("password"))
        error = "call set_error('This password is already in use. Please create a new password.');"
        pas.append("if binary old.password = new.password then\n\t\t\t\t{}\n\t\t\tend if".format(error))
        pas.append("call password_conditions(new.password);")
        pas.separator = ";\n\t\t\t"
        user = "call check_empty('{0}', new.{0});".format("username")
        code.append("if old.username = new.username then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(pas, user))
        index = self.createTrigger("before_update_account", "before update", "account", code, index)
        tables = ("admin", "follow")
        for t in tables:
            code.clear()
            code.append("call check_id(new.{0}, '{0}')".format("user_id"))
            index = self.manageTrigger(t, code, index)
        return index
    
    def messages(self, index):
        code = "set new.date = now()"
        index = self.manageTrigger("message", WriteSql(), index, code)
        return self.createTrigger("before_update_message", "before update", "message", code+";", index)
    
    def songs(self, index):
        tables = ("song", "artist", "genre")
        for table in tables:
            name = table+"_name"
            code = WriteSql()
            code.append("call check_empty('{0}', new.{0})".format(name))
            index = self.manageTrigger(table, code, index)
        code = "set new.date = now()"
        index = self.manageTrigger("comment", WriteSql(), index, code)
        index = self.createTrigger("before_update_comment_date", "before update", "comment", code+";", index)
        code = WriteSql()
        code.append("call check_empty('{0}', new.{0})".format("file"))
        code.append("call check_audio_format(new.file);")
        code.separator = ";\n\t\t"
        return self.table("song_file", code, index)
     
    def playlists(self, index):
        code = WriteSql()
        code.append("call check_empty('{0}', new.{0})".format("playlist_name"))
        index = self.manageTrigger("playlist", code, index)
        return index

    def execute(self, i=1):
        i = Execute.execute(self, i)
        return self.deleteTrigger(i, "account", "admin", "message", "song", "artist", "genre", "playlist")
            
class PrepareInserts(PreparedInsertStatements, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        PreparedInsertStatements.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        i = PreparedInsertStatements.execute(self, i)
        i = self.addArg("int").addMethod(i)
        i = self.addPrimaryId().addArg("int").addArg("string").addMethod(i)
        nums = (1, 2)
        for n in nums:
            i = self.addPrimaryId().addArg("string", n).addMethod(i)
            i = self.addPrimaryId().addArg("int", n).addMethod(i)
        tables = ("account", "song", "playlist")
        for t in tables:
            i = self.addTableId(t).addArg("datetime").addMethod(i)
        i = self.addTableId("message").addArg("int").addMethod(i)
        for n in nums:
            i = self.addTableId("song").addArg("int", n).addMethod(i)
        i = self.addTableId("song").addArg("string").addMethod(i)
        i = self.addTableId("comment").addArg("int", 2).addMethod(i)
        return i
    
class PrepareUpdates(PreparedUpdateStatements, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        PreparedUpdateStatements.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):  
        i = self.addSetArg("date").addWhereArg().addMethod(i)
        i = self.addSetArg("string").addWhereArg().addMethod(i)
        return i
    
class PrepareDeletes(PreparedDeleteStatements, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        PreparedDeleteStatements.__init__(self, db, printText, debug, Execute)
        self.execute()
        
class Adds(AddSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        AddSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def accounts(self, index):
        code = WriteSql()
        code.append("call insert_id_string2('account', username, password)")
        code.append("call insert_account_id_datetime1('account_date', now());")
        args = "in username varchar(255), in password varchar(255)"
        index = self.createProcedure("add_account", args, code, index)
        code.clear()
        code.append("set @user_id = get_account_id(username)")
        insert = "call insert_id_int1('admin', @user_id);"
        error = "call set_error(concat('No admin exists with user name ', username));"
        code.append("if get_admin_id(@user_id) < 1 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(insert, error))
        args = "in username varchar(255)"
        index = self.createProcedure("add_admin", args, code, index)
        return index
    
if __name__ == "__main__":
    db = Creates(printText=True, debug=True).db
    Checks(db, printText=True, debug=True)
    Gets(db, printText=True, debug=True)
    Triggers(db, printText=True, debug=True)
    PrepareInserts(db, printText=True, debug=True)
    PrepareUpdates(db, printText=True, debug=True)
    PrepareDeletes(db, printText=True, debug=True)
    Adds(db, printText=True, debug=True)
#     Updates(db, printText=True, debug=True)
#     Start(db, printText=True, debug=True)
    db.close()