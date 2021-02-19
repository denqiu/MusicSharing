from pySql import AccessSql
from createDatabase import *

if __name__ == "__main__":
#     db = Creates(printText=True, debug=True).db
#     Checks(db, printText=True, debug=True)
#     Triggers(db, printText=True, debug=True)
    db = AccessSql(True, "dennis.txt", AccessSql.SSH_ACCESS)
    db.source("creates.sql", printText = True)
    db.source("triggers.sql", printText = True)
    db.source("prepared_insert_statements.sql", printText = True)
    db.source("gets.sql", printText = True)
    db.source("adds.sql", printText = True)
    db.source("views.sql", printText = True)
    db.close()