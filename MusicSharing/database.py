from pySql import *
import os, time

class Execute(ExecuteSql):
    def __init__(self, title, db=None, printText=True, debug=False):
        ExecuteSql.__init__(self, title, db, printText, debug, accessType=AccessSql.PY_ACCESS)
        
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
    
    def execute(self, i = 1):
        i = self.accounts(i)
        i = self.messages(i)
        i = self.songs(i)
        i = self.playlists(i)
        return self.users(i)
        
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
        return self.createAndAddToManageColumns(table, code, False, index+1)

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
        code.setForeignIds("playlist").deleteCascade().updateCascade()
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
        i = self.createProcedure("check_audio_format", "in format varchar(255)", code, i)
        code.clear()
        code.append("set @detail = detail")
        code.append("if is_empty(@detail) then \n\t\t\tset @detail = 'N/A';\n\t\tend if")
        code.append("return @detail;")
        self.createFunction("check_song_detail", "detail varchar(255)", "varchar(255)", code, i)
         
class Gets(GetSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        GetSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def attribute(self, table, attr, returnType, index):
        return self.get("{}_{}".format(table, attr), returnType, attr, False, False, index, whereTable=table)
        
    def date(self, table, index):
        return self.attribute(table, "date", "datetime", index)
        
    def accounts(self, index):
        index = self.getId("account", "user varchar(255)", "username = user", index)
        cols = ("username", "password")
        for c in cols:
            index = self.get("account", "varchar(255)", c, True, False, index)
        index = self.date("account", index)
        tables = ("admin", "follow")
        for t in tables:
            index = self.getId(t, "uid int", "user_id = uid", index)
            index = self.getId("user", "aid int", "admin_id = aid", index, t, True)
            index = self.get(t, "varchar(255)", "user", True, True, index, functionName="account_username")
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
            index = self.get(t, "varchar(255)", "", False, True, index, functionName="account_username")
        return index
    
    def songs(self, index):
        tables = ("artist", "genre")
        for t in tables:
            col = t+"_name"
            index = self.getId(t, "name varchar(255)", col+ " = name", index)
            index = self.get(t, "varchar(255)", col, False, False, index)
        index = self.getId("song", "uid int, song varchar(255)", "user_id = uid and song_name = song", index)
        cols = ("user_id", "song_name")
        colTypes = ("int", "varchar(255)")
        cols = tuple(zip(cols, colTypes))
        for i, (c, colType) in enumerate(cols):
            index = self.get("song", colType, c, i < 1, False, index)
        index = self.get("song", "varchar(255)", "user", True, True, index, functionName="account_username")
        index = self.date("song", index)
        index = self.getId("comment", "d datetime", "date = d", index)
        cols = ("comment", "date")
        colTypes = ("varchar(255)", "datetime")
        cols = tuple(zip(cols, colTypes))
        for i, (c, colType) in enumerate(cols):
            index = self.get("comment", colType, c, i > 0, False, index)
        cols = ("user", "song")
        functionNames = ("account_username", "song")
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
        index = self.get("playlist", "varchar(255)", "user", True, True, index, functionName="account_username")
        index = self.date("playlist", index)
        index = self.getId("public", "pid int", "playlist_id = pid", index)
        index = self.getId("playlist", "pid int", "public_id = pid", index, "public", True)
        index = self.get("public", "varchar(255)", "playlist", True, True, index)
        index = self.getId("item", "pid int, sid int", "playlist_id = pid and song_id = sid", index)
        cols = ("playlist", "song")
        functionNames = ("playlist", "song")
        cols = tuple(zip(cols, functionNames))
        for (c, name) in cols:
            index = self.getId(c, "i int", "item_id = i", index, "item", table_in_name=True)
            index = self.get("item", "varchar(255)", c, True, True, index, functionName=name)
        return index
    
    def users(self, index):
        tables = ("logged_in", "cur_user")
        for t in tables:
            code = "return (select user_id from {});".format(t)
            index = self.createFunction("get_{}_user_id".format(t).replace("user_user", "user"), "", "int", code, index)
            code = "return get_account_username(get_{}_user_id());".format(t).replace("user_user", "user")
            index = self.createFunction("get_{}_user".format(t).replace("user_user", "user"), "", "varchar(255)", code, index)
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
        code.append("call password_conditions(new.password)")
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
            code = "call check_empty('{0}', new.{0});".format(name)
            index = self.createTrigger("before_update_{}".format(table), "before update", table, code, index)
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
        return self.addTableId("comment").addArg("int", 2).addMethod(i)
    
class PrepareUpdates(PreparedUpdateStatements, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        PreparedUpdateStatements.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):  
        i = self.addSetArg("date").addWhereArg().addMethod(i)
        i = self.addSetArg("string").addWhereArg().addMethod(i)
        i = self.addSetArg("int").addWhereArg().addMethod(i)
        return self.addSetArg("int").addMethod(i)
    
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
        tables = ("admin", "follow")
        err = ("admin", "follower")
        tables = tuple(zip(tables, err))
        for (t, e) in tables:
            code.clear()
            code.append("set @user_id = get_account_id(username)")
            insert = "call insert_id_int1('{}', @user_id);".format(t)
            error = "call set_error(concat('No {} exists with user name ', username));".format(e)
            code.append("if get_{}_id(@user_id) < 1 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(t, insert, error))
            args = "in username varchar(255)"
            index = self.createProcedure("add_{}".format(e), args, code, index)
        return index
    
    def messages(self, index):
        code = WriteSql()
        code.append("set @sender_id = get_account_id(sender)")
        code.append("set @recipient_id = get_account_id(recipient)")
        s = "call set_error(concat('No account exists with user name ', sender));"
        r = "call set_error(concat('No account exists with user name ', recipient));"
        go = WriteSql()
        go.append("call insert_id_string1('message', message)")
        go.append("call insert_message_id_int1('sender', @sender_id)")
        go.append("call insert_message_id_int1('recipient', @recipient_id);")
        go.separator = ";\n\t\t\t"
        code.append("if @sender_id < 1 then \n\t\t\t{}\n\t\telseif @recipient_id < 1 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(s, r, go))
        args = "in message varchar(255), in sender varchar(255), in recipient varchar(255)"
        return self.createProcedure("add_message", args, code, index)
    
    def songs(self, index):
        tables = ("artist", "genre")
        names = ("artist_name", "genre_name")
        tables = tuple(zip(tables, names))
        for (t, name) in tables:
            code = "call insert_id_string1('{}', {});".format(t, name)
            args = "in {} varchar(255)".format(name)
            index = self.createProcedure("add_{}".format(t), args, code, index)
        code = WriteSql()
        code.append("set @user_id = get_account_id(username)")
        c = WriteSql()
        c.append("call insert_id_int1_string1('song', @user_id, song_name)")
        for (t, name) in tables:
            c.append("set @{} = check_song_detail({})".format(t, name))
            i = t+"_id"
            c.append("set @{0} = get_{0}(@{1})".format(i, t))
            a = WriteSql()
            a.append("call add_{0}(@{0})".format(t))
            a.append("set @{0} = get_{0}(@{1});".format(i, t))
            a.separator = ";\n\t\t\t\t"
            c.append("if @{} < 1 then \n\t\t\t\t{}\n\t\t\tend if".format(i, a))
        c.append("call insert_song_id_int2('song_details', @artist_id, @genre_id)")
        tables = ("downloads", "plays")
        for t in tables:
            c.append("call insert_song_id_int1('song_{}', 0)".format(t))
        c.append("call insert_song_id_string1('song_file', file)")
        c.append("call insert_song_id_string1('song_description', description)")
        c.append("call insert_song_id_datetime1('song_date', now());")
        c.separator = ";\n\t\t\t"
        e = "call set_error(concat('No account exists with user name ', username));"
        code.append("if @user_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(c, e))
        args = "in username varchar(255), in song_name varchar(255), in artist_name varchar(255), in genre_name varchar(255), in description varchar(255), in file varchar(255)"
        index = self.createProcedure("add_song", args, code, index)
        code.clear()
        code.append("call insert_id_string1('comment', comment)")
        code.append("set @user_id = get_account_id(username)")
        code.append("set @song_id = get_song_id(@user_id, song_name)")
        code.append("call insert_comment_id_int2('song_comment', @user_id, @song_id);")
        args = "in comment varchar(255), in username varchar(255), in song_name varchar(255)"
        index = self.createProcedure("add_song_comment", args, code, index)
        return index
    
    def playlists(self, index):
        code = WriteSql()
        code.append("call insert_id_int1('public', manage_playlist_id())")
        code.append("call insert_playlist_id_datetime1('playlist_date', now());")
        index = self.createProcedure("set_playlist_public", "", code, index)
        code = WriteSql()
        code.append("set @user_id = get_account_id(username)")
        ins = WriteSql()
        ins.append("call insert_id_int1_string1('playlist', @user_id, playlist_name)")
        ins.append("call set_playlist_public();")
        ins.separator = ";\n\t\t\t"
        err = "call set_error(concat('No account exists with user name ', username));"
        code.append("if @user_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(ins, err))
        args = "in playlist_name varchar(255), in username varchar(255)"
        index = self.createProcedure("add_playlist", args, code, index)
        code.clear()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @playlist_id = get_playlist_id(@user_id, playlist_name)")
        code.append("set @song_id = get_song_id(@user_id, song_name)")
        code.append("call insert_id_int2('item', @playlist_id, @song_id);")
        args = "in username varchar(255), in playlist_name varchar(255), in song_name varchar(255)"
        index = self.createProcedure("add_song_item", args, code, index)
        return index

class Updates(UpdateSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        UpdateSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def accounts(self, index):
        var1 = ("new_user", "new_pass")
        var2 = ("old_user", "username")
        col = ("username", "password")
        vargs = tuple(zip(var1, var2, col))
        for (var1, var2, col) in vargs:
            code = WriteSql()
            code.append("set @user_id = get_account_id({})".format(var2))
            up = "call update_set_string1_where_int1('account', '{}', {}, 'account_id', @user_id);".format(col, var1)
            err = "call set_error(concat('No account exists with user name ', {}));".format(var2)
            code.append("if @user_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
            args = "in {} varchar(255), in {} varchar(255)".format(var1, var2)
            index = self.createProcedure("update_account_{}".format(col), args, code, index)
        return index
    
    def messages(self, index):
        code = WriteSql()
        code.append("set @message_id = get_message_id(msg_date)")
        up = "call update_set_string1_where_int1('message', 'message', new_msg, 'message_id', @message_id);"
        err = "call set_error(concat('No message exists with time stamp ', msg_date));"
        code.append("if @message_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
        args = "in new_msg varchar(255), in msg_date datetime"
        return self.createProcedure("update_message", args, code, index)
    
    def songs(self, index):
        tables = ("artist", "genre")
        for t in tables:
            i = t+"_id"
            code = WriteSql()
            code.append("set @{0} = get_{0}(old_{1})".format(i, t))
            up = "call update_set_string1_where_int1('{0}', '{0}_name', new_{0}, '{1}', @{1});".format(t, i)
            err = "call set_error(concat('No {0} exists with {0} name ', old_{0}));".format(t)
            code.append("if @{} > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(i, up, err))
            args = "in new_{0} varchar(255), in old_{0} varchar(255)".format(t)
            index = self.createProcedure("update_{}".format(t), args, code, index)
        code.clear()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @song_id = get_song_id(@user_id, old_song)")
        up = "call update_set_string1_where_int1('song', 'song_name', new_song, 'song_id', @song_id);"
        err = "call set_error(concat('No song exists with song name ', old_song));"
        code.append("if @song_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
        args = "in new_song varchar(255), in old_song varchar(255), in username varchar(255)"
        index = self.createProcedure("update_song_name", args, code, index)
        for t in tables:
            i = t+"_id"
            code.clear()
            code.append("set @{0} = get_{0}(new_{1})".format(i, t))
            a = WriteSql()
            a.append("set @{0} = check_song_detail(new_{0})".format(t))
            a.append("call add_{0}(@{0})".format(t))
            a.append("set @{0} = get_{0}(@{1});".format(i, t))
            a.separator = ";\n\t\t\t"
            code.append("if @{} < 1 then \n\t\t\t{}\n\t\tend if".format(i, a))
            code.append("set @user_id = get_account_id(username)")
            code.append("set @song_id = get_song_id(@user_id, old_song)")            
            up = "call update_set_int1_where_int1('song_details', '{0}', @{0}, 'song_id', @song_id);".format(i)
            err = "call set_error(concat('No song exists with song name ', old_song));"
            code.append("if @song_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
            args = "in new_{0} varchar(255), in old_song varchar(255), in username varchar(255)".format(t)
            index = self.createProcedure("update_song_{}".format(t), args, code, index)
        tables = ("file", "description")
        for t in tables:
            code.clear()
            code.append("set @user_id = get_account_id(username)")
            code.append("set @song_id = get_song_id(@user_id, old_song)")
            up = "call update_set_string1_where_int1('song_{0}', '{0}', new_{0}, 'song_id', @song_id);".format(t)
            err = "call set_error(concat('No song exists with song name ', old_song));"
            code.append("if @song_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
            args = "in new_{} varchar(255), in old_song varchar(255), in username varchar(255)".format(t)
            index = self.createProcedure("update_song_{}".format(t), args, code, index)
        tables = ("plays", "downloads")
        for t in tables:
            code.clear()
            code.append("set @user_id = get_account_id(username)")
            code.append("set @song_id = get_song_id(@user_id, old_song)")
            code.append("set @increment_{0} = get_song_{0}(@song_id) + 1".format(t))
            up = "call update_set_int1_where_int1('song_{0}', '{0}', @increment_{0}, 'song_id', @song_id);".format(t)
            err = "call set_error(concat('No song exists with song name ', old_song));"
            code.append("if @song_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
            args = "in old_song varchar(255), in username varchar(255)".format(t)
            index = self.createProcedure("update_song_{}".format(t), args, code, index)
        code.clear()
        code.append("set @comment_id = get_comment_id(cmt_date)")
        up = "call update_set_string1_where_int1('comment', 'comment', new_cmt, 'comment_id', @comment_id);"
        err = "call set_error(concat('No comment exists with time stamp ', cmt_date));"
        code.append("if @comment_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
        args = "in new_cmt varchar(255), in cmt_date datetime"
        return self.createProcedure("update_comment", args, code, index)
    
    def playlists(self, index):
        code = WriteSql()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @playlist_id = get_playlist_id(@user_id, old_playlist)")
        up = "call update_set_string1_where_int1('playlist', 'playlist_name', new_playlist, 'playlist_id', @playlist_id);"
        err = "call set_error(concat('No playlist exists with playlist name ', old_playlist));"
        code.append("if @playlist_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(up, err))
        args = "in new_playlist varchar(255), in old_playlist varchar(255), in username varchar(255)"
        index = self.createProcedure("update_playlist_name", args, code, index)
        code.clear()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @playlist_id = get_playlist_id(@user_id, old_playlist)")
        code.append("call update_set_date1_where_int1('playlist_date', 'date', now(), 'playlist_id', @playlist_id);")
        args = "in old_playlist varchar(255), in username varchar(255)"
        return self.createProcedure("update_playlist_date", args, code, index)
    
    def users(self, index):
        tables = ("logged_in", "cur_user")
        for t in tables:
            code = WriteSql()
            code.append("set @user_id = get_account_id(username)")
            code.append("call update_set_int1('{}', 'user_id', @user_id);".format(t))
            args = "in username varchar(255)"
            index = self.createProcedure("update_{}".format(t), args, code, index)
        return index
    
class Deletes(DeleteSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        DeleteSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def accounts(self, index):
        code = WriteSql()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @logged_id = get_logged_in_user_id()")
        err = "call set_error('Cannot delete user. User is already logged in.');"
        d = "call delete_table_id('account', @user_id);"
        code.append("if @user_id = @logged_id then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(err, d))
        args = "in username varchar(255)"
        index = self.createProcedure("delete_account", args, code, index)
        tables = ("admin", "follow")
        err = ("admin", "follower")
        ids = ("admin_id", "follow_id")
        tables = tuple(zip(tables, err, ids))
        for (t, e, i) in tables:
            code.clear()
            code.append("set @user_id = get_account_id(username)")
            code.append("set @{0} = get_{0}(@user_id)".format(i))
            d = "call delete_table_id('{}', @{});".format(t, i)
            error = "call set_error(concat('No {} exists with user name ', username));".format(e)
            code.append("if @{} > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(i, d, error))
            args = "in username varchar(255)"
            index = self.createProcedure("delete_{}".format(e), args, code, index)
        return index
    
    def messages(self, index):
        code = WriteSql()
        code.append("set @message_id = get_message_id(date)")
        d = "call delete_table_id('message', @message_id);"
        err = "call set_error(concat('No message exists with time stamp ', date));"
        code.append("if @message_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(d, err))
        args = "in date datetime"
        return self.createProcedure("delete_message", args, code, index)
    
    def songs(self, index):
        code = WriteSql()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @song_id = get_song_id(@user_id, song_name)")
        d = "call delete_table_id('song', @song_id);"
        err = "call set_error(concat('No song exists with song name ', song_name));"
        code.append("if @song_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(d, err))
        args = "in song_name varchar(255), in username varchar(255)"
        index = self.createProcedure("delete_song", args, code, index)
        code.clear()
        code.append("set @comment_id = get_comment_id(date)")
        d = "call delete_table_id('comment', @comment_id);"
        err = "call set_error(concat('No comment exists with time stamp ', date));"
        code.append("if @comment_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(d, err))
        args = "in date datetime"
        return self.createProcedure("delete_comment", args, code, index)
    
    def playlists(self, index):
        code = WriteSql()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @playlist_id = get_playlist_id(@user_id, playlist_name)")
        d = "call delete_table_id('playlist', @playlist_id);"
        error = "call set_error(concat('No playlist exists with playlist name ', playlist_name));"
        code.append("if @playlist_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(d, error))
        args = "in playlist_name varchar(255), in username varchar(255)"
        index = self.createProcedure("delete_playlist", args, code, index)
        code.clear()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @playlist_id = get_playlist_id(@user_id, playlist_name)")
        code.append("set @public_id = get_public_id(@playlist_id)")
        d = "call delete_table_id('public', @public_id);"
        error = "call set_error(concat('No public playlist exists with playlist name ', playlist_name));"
        code.append("if @public_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(d, error))
        args = "in playlist_name varchar(255), in username varchar(255)"
        index = self.createProcedure("set_playlist_private", args, code, index)
        code.clear()
        code.append("set @user_id = get_account_id(username)")
        code.append("set @playlist_id = get_playlist_id(@user_id, playlist_name)")
        code.append("set @song_id = get_song_id(@user_id, song_name)")
        code.append("set @item_id = get_item_id(@playlist_id, @song_id)")
        d = "call delete_table_id('item', @item_id);"
        error = "call set_error('Song or playlist does not exist.');"
        code.append("if @item_id > 0 then \n\t\t\t{}\n\t\telse\n\t\t\t{}\n\t\tend if;".format(d, error))
        args = "in playlist_name varchar(255), in song_name varchar(255), in username varchar(255)"
        return self.createProcedure("delete_song_item", args, code, index)
         
class Start(StartSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        StartSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def addAccount(self, user):
        self.db.callProcedure(None, "add_account", user, user+"1")
        query = "select account_id, username from account where username = %s"
        self.db.setArgs(user).query(query)
        time.sleep(1)
        
    def addAdmin(self, user):
        self.db.callProcedure(None, "add_admin", user)
        query = "select admin_id, get_account_username(user_id) as user from admin where user_id = get_account_id(%s)"
        self.db.setArgs(user).query(query)
        
    def execute(self, i=1):
        if not self.isMaintained:
            users = ("Blythe", "Blake", "Dennis", "Gordon", "Aengus")
            for u in users:
                self.addAccount(u)
                self.addAdmin(u)
            self.addAccount("User")
           
if __name__ == "__main__":
    db = Creates(printText=True, debug=True).db
    Checks(db, printText=True, debug=True)
    Gets(db, printText=True, debug=True)
    Triggers(db, printText=True, debug=True)
    PrepareInserts(db, printText=True, debug=True)
    PrepareUpdates(db, printText=True, debug=True)
    PrepareDeletes(db, printText=True, debug=True)
    Adds(db, printText=True, debug=True)
    Updates(db, printText=True, debug=True)
    Deletes(db, printText=True, debug=True)
    Start(db, printText=True, debug=True)
    db.close()