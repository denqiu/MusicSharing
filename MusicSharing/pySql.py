from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pyqt5Custom import *
from sshtunnel import SSHTunnelForwarder as ssh
import mysql.connector as con, os, sys, re

class WriteSql:
    def __init__(self):
        self.code = []
        self.separator = ""
        self.setDefault().setNull().setBinary()
        self.column_count = 0
        
    def append(self, sql):
        self.code.append(sql)
        return self
    
    def pop(self, index = None):
        if index is None:
            self.code.pop()
        else:
            self.code.pop(index)
        return self
        
    def setDefault(self, d = None):
        self.__default = "" if d is None else " default {}".format(d)
        return self
        
    def setNull(self, n = True):
        self.__null = "" if n else " not null"
        return self
    
    def setBinary(self, b = False):
        self.__binary = " binary" if b else ""
        return self
         
    def setColumns(self, colType, *colName):
        for i in colName:
            self.append("{} {}{}{}{}".format(i, colType, self.__binary, self.__default, self.__null))
        self.column_count += len(colName)
        return self
            
    def setKeys(self, keyType, *varName):
        if keyType != "index": keyType += " key"
        self.append("{} ({})".format(keyType, ", ".join(varName)))
        return self
        
    def renamePrimaryKey(self, newPrimary):
        for i, c in enumerate(self.code):
            if c[-3:] == "int":
                self.code[i] = "{} int".format(newPrimary)
            elif c[:len("primary")] == "primary":
                self.code[i] = "primary key ({})".format(newPrimary)
        return self
        
    def setForeignKey(self, key, table, tableKey):
        self.append("foreign key ({}) references {} ({})".format(key, table, tableKey))
        return self
        
    def setForeignIds(self, *tables):
        for t in tables:
            i = "{}_id".format(t)
            self.setForeignKey(i, t, i)
        return self
    
    def renameForeignKeys(self, newKey, key = None):
        code = list(reversed(self.code))
        for i, c in enumerate(code):
            r = re.search("foreign key \((.*)\) references (.*)", c)
            if not r is None:
                rep = True if key is None else key == r.group(1)
                if rep:
                    code[i] = "foreign key ({}) references {}".format(newKey, r.group(2))
                    break
        self.code = list(reversed(code))
        return self
    
    def __cascade(self, what):
        code = list(reversed(self.code))
        for i, c in enumerate(code):
            r = re.search("foreign key \(.*\) references .*", c)
            if not r is None:
                code[i] += " on {} cascade".format(what)
        self.code = list(reversed(code))
        return self
    
    def deleteCascade(self):
        return self.__cascade("delete")
    
    def updateCascade(self):
        return self.__cascade("update")
    
    def clear(self):
        self.code.clear()
        self.column_count = 0
        return self
    
    def __str__(self):
        return self.separator.join(self.code)
         
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
                self.connectionType = "py"
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
            if not query is None:
                self.setArgs(*args).query(query)
        except con.Error as e:
            self.results = (self.__checkError(e.msg), None, None)
        return self
        
    def callFunction(self, query, *args):
        try:
            self.__function = True
            if not query is None:
                self.setArgs(*args).query(query)
        except con.Error as e:
            self.results = (self.__checkError(e.msg), None, None)
        return self
    
    def close(self):
        self.db.close()
      
class SshSql(PySql):
    def __init__(self, ssh_host, ssh_user, ssh_password, db_user, db_password, database, debug = False):
        try:
            self.tunnel = ssh((ssh_host), ssh_username = ssh_user, ssh_password = ssh_password, remote_bind_address = ('127.0.0.1', 3306)) 
            self.tunnel.start()
            PySql.__init__(self, '127.0.0.1', db_user, db_password, database, self.tunnel.local_bind_port, debug)
            self.connectionType = "ssh"
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
      
class ExecuteSql:
    def __init__(self, title, db = None, printText = True, debug = False, path = "access.txt", accessType = AccessSql.PY_ACCESS):
        if db is None:
            try:
                self.db = AccessSql(debug, path, accessType)
            except SystemExit as e:
                print(e)
                quit()
        else:
            self.db = db
        title = title.upper()
        t = "=" * len(title) * 2
        s = " " * ((len(t) // 4))
        self.title = "\n".join((t, s+title, t))
        self.printText = printText
        self.debug = debug
        self.maintainDatabase(False)
        print(self.title)
           
    def printResults(self, q, index = None):
        if self.debug: 
            print("{}{}\n".format("" if index is None else "{}. ".format(index), q if self.printText else ""))
          
    def execute(self, i = 1):
        return i
        
    def begin_method(self, q, code):
        q.append("begin")
        q.append("\t{}".format(code))
        q.append("end")
        q.separator = "\n\t"
        return q.__str__()
        
    def createProcedure(self, name, args, code, index):
        self.db.cursor.execute("drop procedure if exists {}".format(name))
        q = WriteSql()
        q.append("create procedure {}({})".format(name, args))
        if isinstance(code, WriteSql):
            code.separator = ";\n\t\t"
        q = self.begin_method(q, code)
        self.printResults(q, index)
        self.db.cursor.execute(q)
        return index + 1
         
    def createFunction(self, name, args, returnType, code, index):
        self.db.cursor.execute("drop function if exists {}".format(name))
        q = WriteSql()
        q.append("create function {}({}) returns {}".format(name, args, returnType))
        if isinstance(code, WriteSql):
            code.separator = ";\n\t\t"
        q.append("not deterministic")
        q.append("reads sql data")
        q = self.begin_method(q, code)
        self.printResults(q, index)
        self.db.cursor.execute(q)
        return index + 1
    
    def checkString(self, check, find, isEqual = True, isEnd = False):
        check = check[-len(find):] if isEnd else check[:len(find)]
        return check == find if isEqual else check != find
    
    def createPreparedStatement(self, name, args, prepStatement, setStatements, index):
        prep = WriteSql()
        prep.append("set @prep = {}".format(prepStatement))
        for s in setStatements:
            prep.append("set @{} = {}".format(s, setStatements[s]))
        prep.append("prepare stmt from @prep")
        executeArgs = ["@"+e for e in setStatements]
        prep.append("execute stmt using {}".format(", ".join(executeArgs)))
        prep.append("deallocate prepare stmt;")
        args = {**{"table_name": "varchar(255)"}, **args}
        args = list(args.items())
        args = [list(a) for a in args]
        for a in args:
            a[0] = "in " + a[0]
        args = ", ".join([" ".join(a) for a in args])
        return self.createProcedure(name, args, prep, index)
    
    def maintainDatabase(self, maintain):
        self.isMaintained = maintain
    
class CreateSql(ExecuteSql):
    VERTICAL_SCROLLBAR = "vertical"
    HORIZONTAL_SCROLLBAR = "horizontal"
    
    MINIMIZED_WINDOW_STATE = "minimized_state"
    MAXIMIZED_WINDOW_STATE = "maximized_state"
    CLOSED_WINDOW_STATE = "closed_state"
    RESTORED_WINDOW_STATE = "restored_state"
    
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "creates", db, printText, debug)
        
    def dropCreateDatabase(self, database = None):
        if not database is None:
            if self.isMaintained:
                self.db.showTables()
                tables = self.db.results[2]
                tables = [table["Tables_in_{}".format(self.db.db_name)] for table in tables]
                tableRows = []
                for t in tables:
                    self.db.query("select * from {}".format(t))
                    tableRows.append(self.db.results[2])
                self.__backup = dict(zip(tables, tableRows))
            self.db.cursor.execute("drop database if exists {}".format(database))
            self.db.cursor.execute("create database {}".format(database))
            self.db.use(database, debug = False)
            
    def __maintainTable(self, table):
        rows = self.__backup[table]
        if len(rows) > 0:
            for r in rows:
                values = tuple(r.values())
                questions = ", ".join(["%s"]*len(values))
                query = "insert into {} values ({})".format(table, questions)
                self.db.modify(query, *values)
        self.db.query("select * from {}".format(table))
          
    def start(self):
        table = "manage_columns"
        q = "drop table if exists {}".format(table)
        self.db.cursor.execute(q)
        q = WriteSql().setNull(False)
        q.setColumns("varchar(255)", "table_name", "column_questions")
        q.setKeys("index", "table_name", "column_questions")
        q.separator = ",\n\t"
        q = "create table {} (\n\t{}\n) engine = INNODB".format(table, q)
        self.printResults(q, 1)
        self.db.cursor.execute(q)
        if self.isMaintained:
            self.__maintainTable(table)
        self.execute(2)
        
    def createAndAddToManageColumns(self, table, code, foreign_checks, index):
        index = self.createTable(table, code, False, foreign_checks, index)
        self.addTableToManageColumns(table, code.column_count)
        return index
        
    def addTableToManageColumns(self, table, column_count):
        if not self.isMaintained:
            self.db.modify("insert into manage_columns values ('{}', '{}')".format(table, ",".join(["?"] * column_count)))
        return self
        
    def manageTable(self, table, column_count, index):
        manage = "manage_{}".format(table)
        q = "drop table if exists {}".format(manage)
        self.db.cursor.execute(q)
        q = WriteSql().setDefault(0).setNull(False)
        q.setColumns("int", "new_id", "size")
        q.setKeys("index", "new_id", "size")
        q.separator = ",\n\t"
        q = "create table {} (\n\t{}\n) engine = INNODB".format(manage, q)
        self.printResults(q, index)
        self.db.cursor.execute(q)
        if self.isMaintained:
            self.__maintainTable(manage)
        else:
            self.db.modify("insert into {} values ()".format(manage))
            self.addTableToManageColumns(table, column_count)
        return index + 1
    
    def createTable(self, table, code, manage, foreign_checks, index):
        q = "drop table if exists {}".format(table)
        self.db.cursor.execute(q)
        if foreign_checks: self.db.setForeignKeyChecks(0)
        code.separator = ",\n\t"
        q = "create table {} (\n\t{}\n) engine = INNODB".format(table, code)
        self.printResults(q, index)
        self.db.cursor.execute(q)
        if self.isMaintained:
            self.__maintainTable(table)
        if foreign_checks: self.db.setForeignKeyChecks(1)
        if manage: index = self.manageTable(table, code.column_count, index+1)
        return index
    
    def begin_table(self, table):
        table_id = "{}_id".format(table)
        code = WriteSql()
        code.setColumns("int", table_id)
        code.setNull(False)
        return (table_id, table, code)
    
    def setTracker(self, table, trackerColumn, columnType, defaultValue):
        code = WriteSql()
        code.setDefault(defaultValue).setNull(False)
        code.setColumns(columnType, trackerColumn)
        code.setKeys("index", trackerColumn)
        return (table, code)
    
    def __getTrackers(self, what):
        tk = vars(CreateSql)
        trackers = {}
        for t in list(tk.keys()).copy():
            if what in t:
                trackers[tk[t]] = t[:t.find('_')].lower()
        return trackers
        
    def trackScroll(self, table, defaultValue, scrollBar = None):
        code = WriteSql()
        if isinstance(defaultValue, str):
            defaultValue = int(defaultValue)
        if not isinstance(defaultValue, int):
            print("Default value must be a number.")
            return (table, code)
        code.setDefault(defaultValue).setNull(False)
        trackScrolls = self.__getTrackers("SCROLLBAR")
        if not scrollBar is None:
            if scrollBar in trackScrolls:
                trackScrolls = {scrollBar: trackScrolls[scrollBar]}
        columns = tuple(trackScrolls.values())
        code.setColumns("int", *columns)
        code.setKeys("index", *columns)
        return (table, code)
    
    def trackWindow(self, table, defaultValue, *windowStates):
        code = WriteSql()
        for c in (int, str):
            if isinstance(defaultValue, c):
                defaultValue = bool(defaultValue)
                break
        if not isinstance(defaultValue, bool):
            print("Default value must be a boolean variable.")
            return (table, code)
        code.setDefault(defaultValue).setNull(False)
        trackStates = self.__getTrackers("WINDOW")
        if len(windowStates) > 0:
            t = {}
            for s in windowStates:
                if s in trackStates:
                    t[s] = trackStates[s]
            trackStates = t
        columns = tuple(trackStates.values())
        code.setColumns("boolean", *columns)
        code.setKeys("index", *columns)
        return (table, code)
    
class CheckSql(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "checks", db, printText, debug)
        
    def execute(self, i = 1):
        i = self.createProcedure("set_error", "in msg varchar(255)", "signal sqlstate '45000' set message_text = msg;", i)
        i = self.createFunction("is_empty", "str varchar(255)", "boolean", "return trim(str) = '' or str is null;", i)
        i = self.createFunction("remove_underscore", "str varchar(255)", "varchar(255)", "return replace(str, '_', ' ');", i)
        i = self.createFunction("capitalize", "str varchar(255)", "varchar(255)", "return concat(ucase(left(str, 1)), substring(str, 2));", i)
        code = WriteSql()
        code.append("set @name = remove_underscore(field_name)")
        code.append("set @cap = capitalize(@name)")
        code.append("call set_error(concat(@cap, ' cannot be empty. Please enter ', @name, '.'));")
        code.separator = ";\n\t\t\t"
        code = "if is_empty(field_value) then\n\t\t\t{}\n\t\tend if;".format(code)
        i = self.createProcedure("check_empty", "in field_name varchar(255), in field_value varchar(255)", code, i)
        code = "call set_error(concat(capitalize(remove_underscore(what)), ' does not exist.'));"
        code = "if c_id < 1 then \n\t\t\t{}\n\t\tend if;".format(code)
        return self.createProcedure("check_id", "in c_id int, in what varchar(255)", code, i)

class GetSql(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "gets", db, printText, debug)
        
    def getId(self, table, args, where, index, fromTable = None, table_in_name = False):
        if fromTable is None:
            fromTable = table
        c = "{}_id".format(table)
        code = "return ifnull((select {} from {} where {}), 0);".format(c, fromTable, where)
        if table_in_name:
            c = "{}_{}".format(fromTable, c)
        return self.createFunction("get_{}".format(c), args, "int", code, index)
     
    def get(self, table, returnType, column, column_in_name, get_from_id, index, whereTable = None, functionName = None):
        if whereTable is None:
            whereTable = table
        g = "get_{}".format(table)    
        name = "{}_{}".format(g, column) if column_in_name else g  
        if get_from_id:
            code = "return get_{}({}_id(g));".format(column if functionName is None else functionName, name if column_in_name else g)
        else:
            code = "return (select {} from {} where {}_id = g);".format(column, table, whereTable)
        return self.createFunction(name, "g int", returnType, code, index)
    
class TriggerSql(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "triggers", db, printText, debug)
        
    def codeEmptyCheck(self, check):
        return "call check_empty('{0}', new.{0})".format(check)
    
    def codeIdCheck(self, check):
        return "call check_id(new.{0}, '{0}')".format(check)
        
    def manageId(self, table, index):
        m = "manage_{}".format(table)
        code = "return (select new_id from {});".format(m)
        return self.createFunction("{}_id".format(m), "", "int", code, index)
         
    def manageSize(self, table, index):
        m = "manage_{}".format(table)
        code = "return (select size from {});".format(m)
        return self.createFunction("{}_size".format(m), "", "int", code, index)
     
    def createTrigger(self, name, action, table, code, index):
        self.db.cursor.execute("drop trigger if exists {}".format(name))
        q = WriteSql()
        q.append("create trigger {} {} on {} for each row".format(name, action, table))
        q = self.begin_method(q, code)
        self.printResults(q, index)
        self.db.cursor.execute(q)
        return index + 1
         
    def manageTrigger(self, table, code, index, *codeAfter):
        for m in (self.manageId, self.manageSize):
            index = m(table, index)
        m = "manage_{}".format(table)
        code.append("update {0} set new_id = {0}_id() + 1, size = {0}_size() + 1".format(m))
        code.append("set new.{}_id = {}_id()".format(table, m))
        if len(codeAfter) > 0:
            for a in codeAfter:
                code.append(a)
        code.code[-1] = code.code[-1] + ";"
        code.separator = ";\n\t\t"
        action = "before insert"
        name = "{}_{}".format(action.replace(" ", "_"), table)          
        return self.createTrigger(name, action, table, code, index)
    
    def deleteTrigger(self, index, *tables):
        if len(tables) > 0:
            for t in tables:
                code = "update {0} set {1} = {0}_{1}() - 1;".format("manage_{}".format(t), "size")
                index = self.createTrigger("delete_{}".format(t), "before delete", t, code, index)
        return index
    
class PreparedInsertStatements(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        self.clearArgs()
        self.__setDataTypes()
        execute.__init__(self, "prepared insert statements", db, printText, debug)
        
    def __setDataTypes(self):
        d = {"string": "varchar(255)"}
        repeats = ["int", "datetime", "date", "boolean"]
        for r in repeats:
            d[r] = r
        self.__dataTypes = d
        
    def clearArgs(self):
        self.__args = {}
        return self
        
    def __createArgs(self, value, args):
        f = value.rfind('_')
        if f > -1:
            f = value[f+1:]
            if f in self.__dataTypes:
                args[value] = self.__dataTypes[f]
        return args
        
    def addMethod(self, index):
        a = self.__args
        keys = tuple(a.keys())
        values, args, setStatements = ([], {}, {})
        if "id" in keys:
            setStatements["id"] = "0"
        for i in list(a.values()):
            values += i
        for v in values:
            if self.checkString(v, "manage"):
                setStatements["id"] = v
            else:
                if not v in setStatements:
                    args = self.__createArgs(v, args)
                    setStatements[v] = v
        name = "_".join(keys).replace("id_id", "id")
        prepStatement = "concat('insert into ', table_name, ' values (', get_table_column_questions(table_name), ')')"
        self.clearArgs()
        return self.createPreparedStatement("insert_"+name, args, prepStatement, setStatements, index)
        
    def addTableId(self, table):
        self.db.setArgs(table).query("select table_name from manage_columns where table_name = %s", printText=self.printText, debug = self.debug)
        results = self.db.results[2][0]
        if len(results) > 0:
            table = "{}_id".format(results["table_name"])
            self.__args[table] = ["manage_{}()".format(table)]
            self.addPrimaryId()
        else:
            print("Table {} doesn't exist.".format(table))
        return self
    
    def addPrimaryId(self):
        self.__args["id"] = ["id"]
        return self
    
    def addArg(self, arg, count = 1):
        args = []
        for c in range(count):
            args.append("arg{}_{}".format(c+1, arg))
        self.__args["{}{}".format(arg, count)] = args
        return self
        
    def removeArgs(self, *args):
        for a in args:
            if a in self.__args:
                self.__args.pop(a)
        return self
    
    def getArgs(self):
        return self.__args
    
    def execute(self, i=1):
        code = "return (select column_questions from manage_columns where table_name = t_name);"
        return self.createFunction("get_table_column_questions", "t_name varchar(255)", "varchar(255)", code, i)
        
class PreparedUpdateStatements(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        self.clearArgs()
        self.__whereExists = False
        self.__setWhatCount = 0
        self.__setDataTypes()
        execute.__init__(self, "prepared update statements", db, printText, debug)
     
    def __setDataTypes(self):
        d = {"what": "varchar(255)", "string": "varchar(255)"}
        repeats = ["int", "datetime", "date", "boolean"]
        for r in repeats:
            d[r] = r
        self.__dataTypes = d
        
    def clearArgs(self):
        self.__args = {}
        return self
    
    def addMethod(self, index):
        a = self.__args
        keys = list(a.keys())
        values, args, setStatements = ([], {}, {})
        for i in list(a.values()):
            values += i
        for v in values:
            args = self.__createArgs(v, args)
            if self.checkString(v, "what", False, True):
                setStatements[v] = v
        if self.__whereExists:
            name = "_".join(keys).replace("set", "set_").replace("where", "where_")
        else:
            name = keys[0].replace("set", "set_")
        getSets = ["{}, '=?".format(s)+"'" for s in args if self.checkString(s, "set") and self.checkString(s, "what", isEnd=True)]
        isWhere = ", ' where ', where1_what, '=?'" if self.__whereExists else ""
        prepStatement = "concat('update ', table_name, ' set ', {}{})".format(", ".join(getSets), isWhere)
        self.clearArgs()
        self.__whereExists = False
        self.__setWhatCount = 0
        return self.createPreparedStatement("update_"+name, args, prepStatement, setStatements, index)
    
    def __addArg(self, action, arg, whatCount, count = 1):
        args = []
        for c in range(count):
            c += 1
            args.append("{}{}_what".format(action, whatCount))
            args.append("{}{}_{}".format(action, c, arg))
        self.__args["{}{}{}".format(action, arg, count)] = args
        return self
        
    def addSetArg(self, arg, count = 1):
        self.__setWhatCount += 1
        return self.__addArg("set", arg, self.__setWhatCount, count)
    
    def __createArgs(self, value, args):
        f = value.rfind('_')
        if f > -1:
            f = value[f+1:]
            if f in self.__dataTypes:
                args[value] = self.__dataTypes[f]
        return args
        
    def addWhereArg(self, arg = "int"):
        if not self.__whereExists:
            self.__whereExists = True
        return self.__addArg("where", arg, 1, 1)
          
    def removeArgs(self, *args):
        for a in args:
            if a in self.__args:
                self.__args.pop(a)
        return self
    
    def getArgs(self):
        return self.__args
    
class PreparedDeleteStatements(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "prepared delete statements", db, printText, debug)
    
    def execute(self, i=1):
        prepStatement = "concat('delete from ', table_name, ' where ', table_name, '_id=?')"
        args = {"table_id":"int"}
        setStatements = {"table_id":"table_id"}
        return self.createPreparedStatement("delete_table_id", args, prepStatement, setStatements, i)
    
class AddSql(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "adds", db, printText, debug)

class UpdateSql(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "updates", db, printText, debug)

class DeleteSql(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "deletes", db, printText, debug)

class StartSql(ExecuteSql):
    def __init__(self, db = None, printText = True, debug = False, execute = ExecuteSql):
        execute.__init__(self, "start", db, printText, debug)
                    
class QtWorkbenchSql(ParentWindow):
    class _Add(Button):   
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
                
            class Message(MessageBox):
                def __init__(self, message, icon = "", iconBackground = None):
                    super().__init__(message, icon, iconBackground)
                
                def setupWindow(self):
                    MessageBox.setupWindow(self)
                    self.setWindowTitle("Qt Workbench")
                    
                def hideEvent(self, QEvent):
                    if self.checkParentWindow():
                        p = self.getParentWindow()
                        p.setEnabled(True)
                        self.button.leaveEvent(QEvent)
                        p.setFocus()
                        self.removeWindow()
                        
                def changeEvent(self, QEvent):
                    MessageBox.changeEvent(self, QEvent)
                    if self.checkParentWindow():
                        p = self.getParentWindow()
                        p.setEnabled(False)
                        search = SearchForm().searchNames("test", "ok")
                        buttons = tuple(p.searchObjects(search).mergeResults().results.values())
                        for b in buttons:
                            if b.entered:
                                self.button = b
                                break
                    
            class TestConnection(Button):
                def __init__(self, comboBox, connectionNames, *text):
                    super().__init__(*text)
                    self.comboBox = comboBox
                    self.setupConn = comboBox.setupConn
                    self.connectionNames = connectionNames
                  
                def testConnection(self, isAccess = False):
                    comboBox = self.comboBox
                    group, access, _ = comboBox.items[comboBox.currentText()]                    
                    results = group.searchObjects(SearchForm().searchClasses(LineBox)).mergeResults().resultValues().results
                    keys = tuple(results.keys())
                    for r in keys:
                        if "schema" in r:
                            n = "database"
                        else:
                            n = r.replace("name", "").replace("MySql", "db").replace(":", "").strip().replace(" ", "_").lower()
                        results[n] = results.pop(r)
                    try:
                        if isAccess:
                            search = SearchForm().searchNames("connection name", "Debug")
                            res = self.setupConn.searchObjects(search).mergeResults().resultValues().results
                            name, debug = tuple(res.values())
                            if name == "":
                                return "Please enter a name for the connection"
                            elif len(self.connectionNames) > 0:
                                if name in self.connectionNames:
                                    return "This connection name already exists.\nPlease create a unique connection name."
                            path = self.createConnection(name, results)
                            connect = (debug, path, access[isAccess], Decode)
                            c = AccessSql(*connect)
                            results["name"] = name
                            results["connect"] = connect
                        else:
                            c = access[isAccess](**results)
                        if c.connectionType == AccessSql.SSH_ACCESS:
                            results["user"] = results["db_user"]
                            results["host"] = "{}@{}".format(results["ssh_user"], results["ssh_host"])
                        c.close()
                        return results
                    except SystemExit as e:
                        return e.__str__()
                    
                def createConnection(self, name, results):
                    results = str(results)[1:-1].replace(", ", "\n").replace("'", "")
                    conns = "{}\\connections".format(os.getcwd())
                    if not os.path.exists(conns):
                        os.mkdir(conns)
                    create = "{}\\{}.txt".format(conns, name)
                    c = open(create, "w")    
                    c.write(results)
                    c.close()
                    return create
                    
                def mouseLeftReleased(self, QMouseEvent):
                    Button.mouseLeftReleased(self, QMouseEvent)
                    test = self.testConnection()
                    message = self.setupConn.setMessage
                    if type(test) is dict:
                        success = ButtonText("Successfully made the MySQL connection", "success")
                        success.setStyleSheet("color: blue")
                        success.setFont(self.setupConn.getFont(14))
                        info = [success]
                        info.append("Information related to this connection:")
                        info.append("")
                        for i in ("host", "user"):
                            info.append("{}: {}".format(i.capitalize(), test[i]))
                        message(info, self.setupConn.Message.INFORMATION_ICON, Qt.blue)
                    else:
                        message(test, self.setupConn.Message.CRITICAL_ICON)
                    
            class Cancel(Button):
                def __init__(self, setupConn, *text):
                    super().__init__(*text)
                    self.setupConn = setupConn
                    
                def mouseLeftReleased(self, QMouseEvent):
                    Button.mouseLeftReleased(self, QMouseEvent)
                    self.setupConn.close()
                    
            class Ok(Button):
                def __init__(self, setupConn, scrollForm, *text):
                    super().__init__(*text)
                    self.setupConn = setupConn
                    self.scrollForm = scrollForm
                    
                def mouseLeftReleased(self, QMouseEvent):
                    Button.mouseLeftReleased(self, QMouseEvent)
                    search = SearchForm().searchNames("test")
                    test = self.setupConn.searchObjects(search).mergeResults().results["test"]
                    results = test.testConnection(True)
                    if type(results) is dict:
                        self.scrollForm.addConnection(results)
                        self.setupConn.close()
                    else:
                        self.setupConn.setMessage(results, self.setupConn.Message.CRITICAL_ICON)
                
            def __init__(self, add):
                self.add = add
                self.mainWindow = add.mainWindow
                self.scrollForm = add.scrollForm
                super().__init__(flags=Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
                 
            def setupWindow(self):
                Window.setupWindow(self)
                self.setWindowTitle("Setup New Connection")
                self.mainWindow.setEnabled(False)
                g = Form()
                g.setFont(self.getFont())
                g.addLineBox("127.0.0.1", "Host name:", False).addRow()
                g.addLineBox("root", "Username:", False).addRow()
                g.addPassword().addRow()
                g.addLineBox(message="Enter default schema name (Optional)").addRow() 
                self.standard = g.group() 
                g = Form()
                g.setFont(self.getFont())
                g.addLineBox("127.0.0.1", "SSH Host name:", False).addRow()
                g.addLineBox("user", "SSH Username:", False).addRow()
                g.addPassword(message="SSH").addRow()
                g.addLineBox("root", "MySql Username:", False).addRow()
                g.addPassword(message="MySql").addRow()
                g.addLineBox(message="Enter MySql default schema name (Optional)").addRow()
                self.standardSSH = g.group()
                f = Form(self)
                f.setFont(self.getFont())
                f.addLineBox(message="Enter a connection name").addRow()
                f.addLabel("Connection method:")
                c = self.Combo(self)
                f.addComboBox(c).addRow()
                self.standardSSH.setVisible(False)
                for g in (self.standard, self.standardSSH):
                    g.setStyleSheet("")
                    f.addGroup(g).addRow()
                names = ("Test Connection", "Cancel", "Ok")
                attributes = ("test", "cancel", "ok")
                actionClasses = (self.TestConnection, self.Cancel, self.Ok)
                params = ([c, self.scrollForm.connectionNames], [self], [self, self.scrollForm])
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
                
            def searchObjects(self, searchForm  = None):
                return self.childForm.searchObjects(searchForm)
            
            def setMessage(self, text, icon = "", iconBackground = None):
                self.setChildWindows(self.Message(text, icon, iconBackground))
                
            def closeEvent(self, QEvent):
                self.mainWindow.setEnabled(True)
                self.add.leaveEvent(QEvent)
                Window.closeEvent(self, QEvent)
               
        def __init__(self, *text):
            self.setMainScroll()
            super().__init__(*text)
            
        def setMainScroll(self, mainWindow = None, scrollForm = None):
            self.mainWindow = mainWindow
            self.scrollForm = scrollForm
                             
        def mouseLeftReleased(self, QMouseEvent):
            Button.mouseLeftReleased(self, QMouseEvent)
            if not self.mainWindow is None:
                self.mainWindow.setChildWindows(self.SetupConnection(self))
#                 results = {"name": "connect name", "user": "some user", "host": "a host", "connect": "connect"}
#                 self.scrollForm.addConnection(results)
            
    class _Manage(Button):
        def __init__(self, *text):
            super().__init__(*text)
                  
    class _ScrollForm(Form):           
        class Connect(ScrollButton):
            def __init__(self, index, *text):
                self.isMoved = False
                super().__init__(index, *text)
                self.setFixedSize(300, 125)
                self.setConnection(None)
                
            def setConnection(self, connect):
                self.connect = connect
                    
            def checkScrollArea(self):
                return not self.getScrollArea() is None
                
            def mouseMove(self, QMouseEvent):
                if self.checkScrollArea():
                    self.getScrollArea().mouseMoveEvent(QMouseEvent)
                
            def mouseLeftPressed(self, QMouseEvent):
                ScrollButton.mouseLeftPressed(self, QMouseEvent)
                if self.checkScrollArea():
                    self.getScrollArea().mouseLeftPressed(QMouseEvent)
                 
            def mouseLeftReleased(self, QMouseEvent):
                s = self.startPosition
                ScrollButton.mouseLeftReleased(self, QMouseEvent)
                if s == QMouseEvent.pos():
                    print(self.connect)
                if self.checkScrollArea():
                    self.getScrollArea().mouseLeftReleased(QMouseEvent)
                    
        def __init__(self):
            self.index = 1
            super().__init__()
            self.connectionNames = []
            self.setAddingItems(True).setColumnSize(6)
                        
        def addConnection(self, results):
            self.addButton(self.connection(results))
                
        def connection(self, results):
            self.connectionNames.append(results["name"])
            width = 300
            name = ButtonText(" "+results["name"], "name") 
            name.setFixedSize(width, 25)
            name.setFont(self.getFont(14))
            user = ButtonText("  User: {}".format(results["user"]), "user") 
            user.setFont(self.getFont())
            user.setFixedSize(width, 25)
            host = ButtonText("  Host: {}".format(results["host"]), "host")  
            host.setFont(self.getFont())
            host.setFixedSize(width, 25)
            c = self.Connect(self.index, name, user, host, ButtonText(attribute="space"))
            self.index += 1
            c.addBoxLayoutToGrid(BoxLayout(Qt.Vertical, "name", "space", "user", "host"), Qt.AlignCenter)  
            c.setConnection(results["connect"])
            return c
                 
    def __init__(self):
        app = QApplication(sys.argv)
        self.__titleForm = None
        self.__start = True
        super().__init__()
        sys.exit(app.exec_())  
        
    def setupWindow(self):
        ParentWindow.setupWindow(self)
        self.showMaximized()
        self.setWindowTitle("Qt Workbench")
        self.__titleForm = Form(self)   
        space = ButtonText(attribute="space")
        space.setFixedWidth(2)
        self.__titleForm.addButtonText(buttonText=space)
        title = QLabel("Qt Connections")
        title.setFont(self.getFont(16))
        title.setFixedWidth(190)
        self.__titleForm.addLabel(label=title)
        buttons = (self._Add, self._Manage)
        names = ("New connection", "Manage connections")
        width = (125, 160)
        b = tuple(zip(buttons, names, width))
        for i in b:
            self.__titleForm.addButton(self.__titleButton(*i))
        self.__titleForm.addRow()
        vbox = QVBoxLayout(self)
        vbox.addLayout(self.__titleForm.layout())
        self.__scrollForm = self._ScrollForm()
        scroll = ScrollArea(self.__scrollForm.group())
        scroll.setDraggable(True)
        #scroll.setScrollBarVisibility(False)
        vbox.addWidget(scroll)
         
    def changeEvent(self, QEvent):
        ParentWindow.changeEvent(self, QEvent)
        if self.isVisible():
            if self.__start:
                if not self.__titleForm is None:
                    search = SearchForm().searchClasses(self._Add)
                    add = self.__titleForm.searchObjects(search).mergeResults().results
                    add = tuple(add.values())[0]
                    add.setMainScroll(self, self.__scrollForm)
                    self.__start = False
    
    def __titleButton(self, actionClass, name, width):
        height = 25
        bname = ButtonText(name, "name") 
        bname.setFixedSize(width, height)
        bname.setFont(self.getFont())
        t = actionClass(self, bname)
        t.setObjectName(name)
        t.setFixedSize(width, height)
        t.addTextToGrid("name")
        return t