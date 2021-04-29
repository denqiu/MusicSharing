from pySql import *

class Execute(ExecuteSql):
    def __init__(self, title, db=None, printText=True, debug=False):
        ExecuteSql.__init__(self, title, db, printText, debug, accessType=AccessSql.SSH_ACCESS)
        #self.maintainDatabase(True)

class Create(CreateSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        CreateSql.__init__(self, db, printText, debug, Execute)
        self.dropCreateDatabase("logger")
        self.start()        
        
    def execute(self, i=1):
        i = CreateSql.execute(self, i)
        uid, table, code = self.begin_table("user")
        code.setColumns("varchar(255)", "first_name", "last_name")
        code.setKeys("primary", uid)
        code.setKeys("index", "first_name", "last_name")
        i = self.createTable(table, code, True, False, i)
        did, table, code = self.begin_table("deliverable")
        code.setColumns("varchar(255)", "deliverable")
        code.setColumns("int", "user_id")
        code.setKeys("primary", did)
        code.setForeignIds("user")
        code.setKeys("index", "deliverable", "user_id")
        i = self.createTable(table, code, True, False, i)
        cid, table, code = self.begin_table("current_leader")
        code.setKeys("primary", cid).renamePrimaryKey("user_id")
        code.setForeignIds("user")
        i = self.createAndAddToManageColumns(table, code, False, i)
        tables = ("current_editor", "last_editor")
        for t in tables:
            table, code = self.setTracker(t, "user_id", "int", 0)
            i = self.createAndAddToManageColumns(table, code, False, i+1)
        table, code = self.trackScroll("users_scroll", 0, self.HORIZONTAL_SCROLLBAR)
        i = self.createAndAddToManageColumns(table, code, False, i+1)
        table, code = self.trackWindow("logger_window", False, self.MAXIMIZED_WINDOW_STATE)
        i = self.createAndAddToManageColumns(table, code, False, i+1)
        item_id, table, code = self.begin_table("item")
        code.setColumns("int", "user_id", "leader_id")
        code.setKeys("primary", item_id)
        code.setForeignIds("user", "user").renameForeignKeys("leader_id")
        code.setKeys("index", "user_id", "leader_id")
        i = self.createTable(table, code, True, False, i+1)-1
        tables = ("date", "description", "time")
        cols = ({"start_date": "datetime", "end_date": "date"}, {"description": "varchar(255)"}, {"hours": "int", "minutes": "int"})
        tables = tuple(zip(tables, cols))
        for (table, cols) in tables:
            tid, _, code = self.begin_table(table)
            columns = [table]
            if table == "time":
                columns[0] = "hours"
                columns.append("minutes")
            for c in cols:
                code.setColumns(cols[c], c)
            code.setKeys("primary", tid).renamePrimaryKey("item_id")
            code.setForeignIds("item")
            i = self.createTable(table, code, False, False, i+1)
            self.addTableToManageColumns(table, code.column_count)
        code = "return (select timestamp(date(start_date), curtime()));"
        i = self.createFunction("create_start_date", "start_date varchar(255)", "datetime", code, i+1)
        code = "return (select date_add(start_date, interval concat(hours, ':', minutes) hour_minute));"
        args = "start_date datetime, hours int, minutes int"
        i = self.createFunction("create_end_date", args, "date", code, i)
        return i
   
class Checks(CheckSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        CheckSql.__init__(self, db, printText, debug, Execute)
        self.execute()
   
class Gets(GetSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        GetSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        i = self.getId("user", "fn varchar(255), ln varchar(255)", "first_name = fn and last_name = ln", i)
        for n in ("first_name", "last_name"):
            i = self.get("user", "varchar(255)", n, True, False, i)
        code = "return (select concat(first_name, ' ', last_name) from user where user_id = g);"
        i = self.createFunction("get_user", "g int", "varchar(255)", code, i)
        tables = ("current_leader", "current_editor", "last_editor")
        for t in tables:
            code = "return ifnull((select user_id from {}), 0);".format(t)
            i = self.createFunction("get_{}_id".format(t), "", "int", code, i)
            code = "return (select get_user(get_{}_id()));".format(t)
            i = self.createFunction("get_{}".format(t), "", "varchar(255)", code, i)
        code = "return ifnull((select horizontal from users_scroll), 0);"
        i = self.createFunction("get_users_scroll_horizontal", "", "int", code, i)
        code = "return ifnull((select maximized from logger_window), false);"
        i = self.createFunction("get_logger_window_maximized", "", "boolean", code, i)
        i = self.getId("deliverable", "u int", "user_id = u", i)
        code = "return (select deliverable from deliverable where user_id = u);"
        i = self.createFunction("get_deliverable", "u int", "varchar(255)", code, i)
        table = "item"
        i = self.getId(table, "d datetime", "start_date = d", i, "date")
        i = self.get(table, "int", "user_id", True, False, i)
        i = self.get(table, "int", "leader_id", True, False, i)
        i = self.get(table, "varchar(255)", "user", True, True, i)
        code = "return get_user(get_item_leader_id(g));"
        i = self.createFunction("get_item_leader", "g int", "varchar(255)", code, i)
        i = self.get("date", "datetime", "start_date", True, False, i, whereTable="item")
        i = self.get("date", "date", "end_date", True, False, i, whereTable="item")
        i = self.get("description", "varchar(255)", "description", False, False, i, whereTable="item")
        for t in ("hours", "minutes"):
            i = self.get("time", "int", t, True, False, i, whereTable = "item")
        return i
    
class Triggers(TriggerSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        TriggerSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        code = WriteSql()
        for n in ("first_name", "last_name"):
            code.append(self.codeEmptyCheck(n))
        i = self.manageTrigger("user", code, i)
        code.clear()
        code.append(self.codeEmptyCheck("deliverable"))
        code.append(self.codeIdCheck("user_id"))
        i = self.manageTrigger("deliverable", code, i)
        code.clear()
        for u in ("user_id", "leader_id"):
            code.append(self.codeIdCheck(u))
        i = self.manageTrigger("item", code, i)
        code.clear()
        code.append("if new.user_id = old.user_id then \n\t\t\tset new.user_id = 0;\n\t\tend if;")
        i = self.createTrigger("before_update_current_editor", "before update", "current_editor", code, i)
        return i
        
class PrepareInserts(PreparedInsertStatements, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        PreparedInsertStatements.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        i = PreparedInsertStatements.execute(self, i)
        i = self.addPrimaryId().addArg("string", 2).addMethod(i)
        i = self.addArg("int").addMethod(i)
        i = self.addPrimaryId().addArg("string").addArg("int").addMethod(i)
        i = self.addPrimaryId().addArg("int", 2).addMethod(i)
        i = self.addTableId("item").addArg("datetime").addArg("date").addMethod(i)
        i = self.addTableId("item").addArg("string").addMethod(i)
        i = self.addTableId("item").addArg("int", 2).addMethod(i)
        return i
    
class PrepareUpdates(PreparedUpdateStatements, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        PreparedUpdateStatements.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):  
        i = self.addSetArg("int").addMethod(i)
        i = self.addSetArg("boolean").addMethod(i)
        i = self.addSetArg("datetime").addSetArg("date").addWhereArg().addMethod(i)
        i = self.addSetArg("date").addWhereArg().addMethod(i)
        i = self.addSetArg("string").addWhereArg().addMethod(i)
        i = self.addSetArg("int", 2).addWhereArg().addMethod(i)
        return i
    
class Adds(AddSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        AddSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        code = WriteSql()
        code.append("call insert_id_string2('user', first_name, last_name)")
        code.append("call insert_id_string1_int1('deliverable', deliverable, manage_user_id());")
        args = "in first_name varchar(255), in last_name varchar(255), in deliverable varchar(255)"
        i = self.createProcedure("add_user", args, code, i)
        code.clear()
        code.append("set @user_id = get_user_id(first_name, last_name)")
        code.append("call insert_int1('current_leader', @user_id);")
        args = "in first_name varchar(255), in last_name varchar(255)"
        i = self.createProcedure("add_current_leader", args, code, i)
        code.clear()
        code.append("set @startDate = create_start_date(start_date)")
        code.append("set @endDate = create_end_date(@startDate, hours, minutes)")
        code.append("call insert_id_int2('item', user_id, get_current_leader_id())")
        code.append("call insert_item_id_datetime1_date1('date', @startDate, date(@endDate))")
        code.append("call insert_item_id_string1('description', description)")
        code.append("call insert_item_id_int2('time', hours, minutes);")
        args = "in user_id int, in start_date varchar(255), in description varchar(255), in hours int, in minutes int"
        i = self.createProcedure("add_item", args, code, i)
        return i
    
class Updates(UpdateSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        UpdateSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        code = WriteSql()
        code.append("call update_set_int1('current_leader', 'user_id', user_id);")
        args = "in user_id int"
        i = self.createProcedure("update_current_leader", args, code, i)
        code.clear()
        code.append("call update_set_int1('current_editor', 'user_id', user_id);")
        args = "in user_id int"
        i = self.createProcedure("update_current_editor", args, code, i)
        code.clear()
        code.append("call update_set_int1('last_editor', 'user_id', get_current_editor_id())")
        code.append("call update_set_int1('current_editor', 'user_id', 0);")
        i = self.createProcedure("update_last_editor", "", code, i)
        code.clear()
        code.append("call update_set_int1('users_scroll', 'horizontal', horizontal);")
        args = "in horizontal int"
        i = self.createProcedure("update_users_horizontal_scroll", args, code, i)
        code.clear()
        code.append("call update_set_boolean1('logger_window', 'maximized', isMaximized);")
        args = "in isMaximized boolean"
        i = self.createProcedure("update_logger_window_maximized", args, code, i)
        code.clear()
#         code.append("set @startDate = create_start_date(start_date)")
#         code.append("set @endDate = create_end_date(@startDate, hours, minutes)")
#         args = "in item_id int, start_date varchar(255)"
#         i = self.createProcedure("update_start_date", args, code, i)
        return i
        
class Start(StartSql, Execute):
    def __init__(self, db=None, printText=True, debug=False):
        StartSql.__init__(self, db, printText, debug, Execute)
        self.execute()
        
    def execute(self, i=1):
        if not self.isMaintained:
            firsts = ("Blythe", "Blake", "Dennis", "Gordon", "Aengus")
            lasts = ("Layne", "McCall", "Qiu", "Hendry", "Rafferty")
            deliverables = ("Requirements", "Planning", "Design", "User Guide and Testing Results", "Project Folder (includes program code)")
            users = tuple(zip(firsts, lasts, deliverables))
            for (first_name, last_name, deliverable) in users:
                self.db.callProcedure(None, "add_user", first_name, last_name, deliverable)
                query = "select user.user_id, get_user(user.user_id) as user, deliverable_id, deliverable from user, deliverable where user.user_id = get_user_id(%s, %s) and user.user_id = deliverable.user_id"
                self.db.setArgs(first_name, last_name).query(query)
            self.db.callProcedure(None, "add_current_leader", firsts[0], lasts[0])
            self.db.query("select user_id, get_user(user_id) as user from current_leader")
            tables = ("current_editor", "last_editor")
            for t in tables:
                self.db.modify("insert into {} values ()".format(t))
                self.db.query("select user_id, get_user(user_id) as user from {}".format(t))
            self.db.modify("insert into users_scroll values ()")
            self.db.query("select get_users_scroll_horizontal() as horizontal")
            self.db.modify("insert into logger_window values ()")
            self.db.query("select get_logger_window_maximized() as isMaximized")
           
if __name__ == "__main__":
    db = Create(printText=True, debug=True).db
    Checks(db, printText=True, debug=True)
    Gets(db, printText=True, debug=True)
    Triggers(db, printText=True, debug=True)
    PrepareInserts(db, printText=True, debug=True)
    PrepareUpdates(db, printText=True, debug=True)
    Adds(db, printText=True, debug=True)
    Updates(db, printText=True, debug=True)
    Start(db, printText=True, debug=True)
    db.close()