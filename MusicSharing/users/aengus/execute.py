from pySql import AccessSql

if __name__ == "__main__":
    db = AccessSql(True, "aengus.txt", AccessSql.SSH_ACCESS)
    db.showTables()
    db.close()