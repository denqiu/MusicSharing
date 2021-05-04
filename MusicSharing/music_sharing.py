from pySql import *
from pyqt5Custom import *

class Cancel(Button):
    def __init__(self, win):
        super().__init__(ButtonText("Cancel ", "cancel"))
        self.setObjectName("cancel")
        self.addTextToGrid("cancel")
        self.win = win
        
    def mouseLeftReleased(self, QMouseEvent):
        Button.mouseLeftReleased(self, QMouseEvent)
        self.win.close()
        
class Ok(Button):
    def __init__(self, win):
        self.win = win
        super().__init__(ButtonText("Ok ", "ok"))
        self.setObjectName("ok")
        self.addTextToGrid("ok")
        
    def okAction(self):
        self.win.close()
        
    def mouseLeftReleased(self, QMouseEvent):
        Button.mouseLeftReleased(self, QMouseEvent)
        self.okAction()
         
class Message(MessageBox):
    def __init__(self, message, icon = "", iconBackground = None):
        super().__init__(message, icon, iconBackground)
    
    def setupWindow(self):
        MessageBox.setupWindow(self)
        self.setWindowTitle("CSC 450 Music Sharing")
        
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
            search = SearchForm().searchNames("ok")
            ok = p.searchObjects(search).mergeResults().results["ok"]
            self.button = ok
   
class AccountWindow(Window):
    class _Ok(Ok):
        def __init__(self, win, music):
            self.music = music
            Ok.__init__(self, win)
            
        def okAction(self):
            win = self.win
            texts = win.texts()
            query = "select * from account where username = %s and password = %s"
            if win.is_create_account():
                results = self.music.db.callProcedure(query, "add_account", *texts[:-1]).results
            else:
                results = self.music.db.setArgs(*texts).query(query).results
            if results[2] is None:
                win.setMessage(results[0], Message.CRITICAL_ICON)
            else:
                win.close()
                
    def __init__(self, music, button):
        self.music = music
        self.button = button
        self.childForm = None
        super().__init__(flags=Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        
    def is_create_account(self):
        return self.button.objectName() == "create-account"
        
    def setupWindow(self):
        Window.setupWindow(self)
        self.setWindowTitle(self.button.text)
        self.music.setEnabled(False)
        f = Form(self)
        f.setFont(self.getFont())
        f.addLineBox(message="Username:", msgIn=False).addRow()
        f.addPassword().addRow()
        if self.is_create_account():
            f.addPassword(message="Re-enter").addRow()
        self.ok = self._Ok(self, self.music)
        for b in (Cancel(self), self.ok):
            f.addButton(b)
        f.addRow(Qt.AlignCenter)
        self.childForm = f
        self.childForm.layout()
 
    def texts(self):
        search = SearchForm().searchNames("username", "password")
        return tuple(self.childForm.searchObjects(search).mergeResults().resultValues().results.values())

    def setMessage(self, text, icon = "", iconBackground = None):
        self.setChildWindows(Message(text, icon, iconBackground))
        
    def eventFilter(self, QObject, QEvent):
        if not self.childForm is None:
            texts, isOk = (self.texts(), True)
            for t in texts:
                if t == "":
                    isOk = False
                    break
            if self.button.objectName() == "create-account":
                if isOk:
                    isOk = texts[-2] == texts[-1]
            self.ok.setEnabled(isOk)
        return Window.eventFilter(self, QObject, QEvent)
         
    def closeEvent(self, QEvent):
        self.music.setEnabled(True)
        self.button.leaveEvent(QEvent)
        Window.closeEvent(self, QEvent)
       
class MenuButton(Button):
    def __init__(self, music, menu, doCurrentClicked, name):
        self.music = music
        self.menu = menu
        self.doCurrentClicked = doCurrentClicked
        text = " ".join([n.capitalize() for n in name.split(" ")])+" "
        self.text = text
        attr = name.replace(" ", "-")
        Button.__init__(self, ButtonText(text, attr))
        self.setObjectName(attr)
        self.addTextToGrid(attr)
        self.backCol = self.backgroundColor
        
    def mouseLeftReleased(self, QMouseEvent):
        Button.mouseLeftReleased(self, QMouseEvent)
        if self.doCurrentClicked:
            curButton = self.menu.currentButton
            if not curButton is None:
                curButton.backgroundColor = self.backCol
                curButton.doCurrentClicked = False
                curButton.mouseLeftReleased(QMouseEvent)
                curButton.leave(QMouseEvent)
                curButton.doCurrentClicked = True
            self.backgroundColor = self.clickColor
            self.menu.currentButton = self
            
class Home(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "home")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
                   
class LogIn(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "log in")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
        self.music.setChildWindows(AccountWindow(self.music, self))
                   
class CreateAccount(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "create account")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
        self.music.setChildWindows(AccountWindow(self.music, self))
                
class Upload(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "upload")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
                
class Profile(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "profile")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
                
class Messages(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "messages")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
             
class Accounts(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "accounts")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
          
class LogOut(MenuButton):
    def __init__(self, music, menu, doCurrentClicked):
        MenuButton.__init__(self, music, menu, doCurrentClicked, "log out")
       
    def mouseLeftReleased(self, QMouseEvent):
        MenuButton.mouseLeftReleased(self, QMouseEvent)
   
class Menu(Form):
    def __init__(self, music):
        self.currentButton = None
        Form.__init__(self, music)
        self.tablelize(True)
        buttons = [Home]
        curClicked = [True]
        level, _ = music.get_user_level()
        if level == "guest":
            buttons += [LogIn, CreateAccount]
            curClicked += [False]*2
        elif level == "user" or level == "admin":
            buttons += [Upload, Profile, Messages, LogOut]
            curClicked += [False, True] + [False]*2
            if level == "admin":
                buttons = buttons[:-1] + [Accounts] + buttons[-1]
                curClicked = curClicked[:-1] + [True] + curClicked[-1]
        buttonNames = {}
        buttons = list(zip(buttons, curClicked))
        for i, (b, curClick) in enumerate(buttons):
            b = b(music, self, curClick)
            b.setFixedHeight(40)
            b.setFont(self.getFont(12))
            buttonNames[b.objectName()] = b
            buttons[i] = b
        buts = (buttons[:1], buttons[1:])
        aligns = (Qt.AlignLeft, Qt.AlignRight)
        box = tuple(zip(buts, aligns))
        for (b, align) in box:
            boxLayout = BoxLayout(Qt.Horizontal, *b)
            boxLayout.setAlignment(align)
            self.addBoxLayout(boxLayout)
        self.addRow()
        self.buttonNames = buttonNames
        
class View(Form):
    def __init__(self, music):
        Form.__init__(self, music)
        self.tablelize(True)
        
        
class MusicSharing(ParentWindow):    
    def __init__(self):
        app = QApplication(sys.argv)
        try:
            self.db = AccessSql(True, accessType=AccessSql.PY_ACCESS)
            self.__start = True
        except SystemExit as e:
            self.db = str(e)
            self.__start = False
        super().__init__()
        sys.exit(app.exec_())  
        
    def checkDb(self):
        return not type(self.db) is str
    
    def setupWindow(self):
        ParentWindow.setupWindow(self)
        self.setWindowTitle("CSC 450 Music Sharing")
        if self.checkDb():
            vbox = QVBoxLayout(self)
            self.menu = Menu(self)
            vbox.addLayout(self.menu.layout())
            self.view = View(self)
            self.center()
        else:
            error = MessageBox(self.db, MessageBox.CRITICAL_ICON)
            error.setWindowTitle("Connection Error")
            error.center()
            self.addChildWindows(error)
        self.showMaximized()
        self.installEventFilter(self)
         
    def changeEvent(self, QEvent):
        ParentWindow.changeEvent(self, QEvent)
        if self.isVisible():
            if self.__start:
                if self.checkDb():
                    home = self.menu.buttonNames["home"]
                    home.enter(QMouseEvent)
                    home.mouseLeftReleased(QMouseEvent)
                    home.leave(QMouseEvent)
                self.__start = False
                 
    def loadChunks(self, scroll):
        chunks = 0
        size = scroll.getWidgetOrLayoutRowCount()
        if size < 20:
            chunks = int((20 - size) / scroll.getWidgetOrLayoutRowsPerChunk())
        if chunks > 0:
            for _ in range(chunks):
                scroll.widgetOrLayoutLoadChunk()
#                  
#     def eventFilter(self, QObject, QEvent):
#         if self.isVisible():
#             if self.__autoSize:
#                 self.__autoSize = False
#                 scrolls = self.__users.getItemsScroll()
#                 for s in scrolls:
#                     if s.isVisible():
#                         rows = s.getItems().getRows()
#                         if len(rows) > 0:
#                             for r in rows:
#                                 cells = r.getCells()
#                                 for c in cells:
#                                     c.autoSize()
#                         self.loadChunks(s)
#         return ParentWindow.eventFilter(self, QObject, QEvent)
#        
    def get_logged_in(self):
        return self.db.query("select get_logged_in_user_id() as logged_in").results[2][0]['logged_in']
    
    def get_logged_in_user(self):
        return self.db.query("select get_logged_in_user() as logged_in").results[2][0]['logged_in']

    def get_admin(self, logged_in):
        return self.callFunction("select get_admin_id(%s) as admin_id", logged_in).results[2][0]['admin_id']
    
    def get_user_level(self):
        logged_in = self.get_logged_in()
        if logged_in > 0:
            admin_id = self.get_admin(logged_in)
            if admin_id > 0:
                return ("admin", admin_id)
            return ("user", logged_in)
        else:
            return ("guest", logged_in)

if __name__ == "__main__":
    MusicSharing()