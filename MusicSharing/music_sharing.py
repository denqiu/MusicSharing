from pySql import *
from pyqt5Custom import *
from pygame import mixer
import shutil

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
            fields = win.fields()
            query = "select * from account where username = %s and password = %s"
            create_account = win.is_create_account()
            music = self.music
            if create_account:
                results = music.db.callProcedure(query, "add_account", *fields[:-1]).results
            else:
                results = music.db.setArgs(*fields).query(query).results
            if results[2] is None:
                win.setMessage(results[0], Message.WARNING_ICON)
            elif len(results[2]) == 0:
                win.setMessage("This account doesn't exist.", Message.WARNING_ICON)
            else:
                win.close()
                if not create_account:
                    for u in (music.updateLoggedIn, music.updateCurUser):
                        u(results[2][0]["username"])

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
        
    def searchObjects(self, searchForm = None):
        return self.childForm.searchObjects(searchForm)
 
    def fields(self):
        search = SearchForm().searchNames("username", "password")
        return tuple(self.searchObjects(search).mergeResults().resultValues().results.values())

    def setMessage(self, text, icon = "", iconBackground = None):
        self.setChildWindows(Message(text, icon, iconBackground))
        
    def eventFilter(self, QObject, QEvent):
        if not self.childForm is None:
            fields, isOk = (self.fields(), True)
            for f in fields:
                if f == "":
                    isOk = False
                    break
            if self.button.objectName() == "create-account":
                if isOk:
                    isOk = fields[-2] == fields[-1]
            self.ok.setEnabled(isOk)
        return Window.eventFilter(self, QObject, QEvent)
         
    def closeEvent(self, QEvent):
        self.music.setEnabled(True)
        self.button.leaveEvent(QEvent)
        Window.closeEvent(self, QEvent)
        
class UploadWindow(Window):
    class _Ok(Ok):
        def __init__(self, win, music):
            self.music = music
            Ok.__init__(self, win)
            
        def okAction(self):
            win = self.win
            _, vals = win.fields()
            username = self.music.get_logged_in_user()
            vals = [username] + vals + [win.filePath]
            results = self.music.db.callProcedure(None, "add_song", *vals).results
            if results[2] is None:
                win.setMessage(results[0], Message.WARNING_ICON)
            else:
                query = "select * from song where user_id = get_account_id(%s) and song_name = %s"
                results = self.music.db.setArgs(*vals[:2]).query(query).results
                if results[2] is None:
                    win.setMessage(results[0], Message.WARNING_ICON)
                else:
                    win.close()
                    music = self.music
                    music.addSongFile(results[2][0]["song_id"], vals[-1])
                    music.menu.executeButton()
            
    class Browse(Button):
        def __init__(self, win):
            text = ButtonText("Browse song", "browse")
            text.setAlignment(Qt.AlignCenter) 
            super().__init__(text)
            self.setObjectName("browse")
            self.addTextToGrid("browse")
            self.win = win
            
        def mouseLeftReleased(self, QMouseEvent):
            Button.mouseLeftReleased(self, QMouseEvent)
            path, _ = QFileDialog.getOpenFileName(self,"Browse song", "","Audio Files (*.ogg *.mp3 *.wav)", options=QFileDialog.Options())
            if path != "":
                win = self.win
                win.filePath = path
                name = os.path.basename(path)[:-4]
                objs, _ = win.fields()
                objs[0].setText(name)
             
    def __init__(self, music, button):
        self.music = music
        self.button = button
        self.childForm = None
        self.filePath = ""
        super().__init__(flags=Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        
    def setupWindow(self):
        Window.setupWindow(self)
        self.setWindowTitle(self.button.text)
        self.music.setEnabled(False)
        f = Form(self)
        f.setFont(self.getFont())
        fields = ("Name", "Artist", "Genre")
        for fi in fields:
            f.addLineBox(message=fi+":", msgIn=False).addRow()
        f.addTextBox(message="Description:", msgIn=False).addRow()
        f.addButton(self.Browse(self)).addRow()
        self.ok = self._Ok(self, self.music)
        for b in (Cancel(self), self.ok):
            f.addButton(b)
        f.addRow(Qt.AlignCenter)
        self.childForm = f
        self.childForm.layout()
        
    def searchObjects(self, searchForm = None):
        return self.childForm.searchObjects(searchForm)
 
    def fields(self):
        search = SearchForm().searchNames("name", "artist", "genre", "description")
        search = self.searchObjects(search)
        objs = tuple(search.mergeResults().results.values())
        vals = list(search.resultValues().results.values())
        return (objs, vals)

    def setMessage(self, text, icon = "", iconBackground = None):
        self.setChildWindows(Message(text, icon, iconBackground))
        
    def eventFilter(self, QObject, QEvent):
        if not self.childForm is None:
            self.ok.setEnabled(not self.filePath.strip() == "")
        return Window.eventFilter(self, QObject, QEvent)
         
    def closeEvent(self, QEvent):
        self.music.setEnabled(True)
        self.button.leaveEvent(QEvent)
        Window.closeEvent(self, QEvent)
       
class Action(Button):
    def __init__(self, music, menu, view, doCurrentClicked, name):
        self.music = music
        self.menu = menu
        self.view = view
        self.doReset = False
        self.doCurrentClicked = doCurrentClicked
        text = " ".join([n.capitalize() for n in name.split(" ")])+" "
        self.text = text
        attr = name.replace(" ", "-")
        Button.__init__(self, ButtonText(text, attr))
        self.setObjectName(attr)
        self.addTextToGrid(attr)
        self.backCol = self.backgroundColor
        
    def checkPlayButtons(self):
        plays = ("play", "shuffle", "repeat")
        return not self.objectName() in plays
        
    def mouseLeftReleased(self, QMouseEvent):
        Button.mouseLeftReleased(self, QMouseEvent)
        if self.doCurrentClicked:
            curButton = self.menu.currentButton
            if not curButton is None:
                if self.checkPlayButtons():
                    curButton.reset()
            self.backgroundColor = self.clickColor
            if self.checkPlayButtons():
                self.menu.currentButton = self
        if self.doReset:
            self.doReset = False
        else:
            self.doAction(QMouseEvent)
            
    def doAction(self, QMouseEvent):
        pass
            
    def reset(self):
        self.doReset = True
        self.backgroundColor = self.backCol
        self.doCurrentClicked = False
        self.mouseLeftReleased(QMouseEvent)
        self.leave(QMouseEvent)
        self.doCurrentClicked = True
            
class Home(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "home")
        
    def createQuery(self, table):
        return "select {0}_name as Name, get_account_username(user_id) as Username, '{0}' as What, get_{0}_date({0}_id) as date from {0}".format(table)
        
    def doAction(self, QMouseEvent):
        songs = self.createQuery("song")
        playlists = self.createQuery("playlist")
        playlists = "{} where get_public_id(playlist_id) > 0".format(playlists)
        query = "{} union {} order by date desc".format(songs, playlists)
        results = self.music.db.query(query).results[2]
        self.view.createView(results)
       
class Profile(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "profile")
      
    def doAction(self, QMouseEvent):
        pass
       
class LogIn(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "log in")
       
    def doAction(self, QMouseEvent):
        self.music.setChildWindows(AccountWindow(self.music, self))
                   
class CreateAccount(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "create account")
       
    def doAction(self, QMouseEvent):
        self.music.setChildWindows(AccountWindow(self.music, self))
                
class Upload(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "upload")
       
    def doAction(self, QMouseEvent):
        self.music.setChildWindows(UploadWindow(self.music, self))
                   
class Messages(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "messages")
       
    def doAction(self, QMouseEvent):
        pass
       
class Accounts(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "accounts")
     
    def doAction(self, QMouseEvent):
        pass
       
class LogOut(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "log out")
       
    def doAction(self, QMouseEvent):
        self.music.updateLoggedIn("")
       
class Play(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        self.isOn = False
        self.curSong = ""
        self.doSwitchOn = True
        Action.__init__(self, music, menu, view, doCurrentClicked, "play")
       
    def doAction(self, QMouseEvent):
        path = self.view.songName
        if path == "":
            self.reset()
        else:
            if self.doSwitchOn:
                self.isOn = not self.isOn
            else:
                self.doSwitchOn = True
            if self.isOn:
                if self.curSong == path:
                    mixer.music.unpause()
                else:
                    mixer.init()
                    mixer.music.load("{}\\songs\\{}".format(os.getcwd(), path))
                    mixer.music.set_volume(0.7)
                    mixer.music.play()
                    self.curSong = path
                pass
            else:
                self.reset()
                mixer.music.pause()
       
    def executePlay(self):
        self.enter(QMouseEvent)
        self.mouseLeftReleased(QMouseEvent)
        self.leave(QMouseEvent)
        
class Next(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "next")
       
    def doAction(self, QMouseEvent):
        pass
               
class Previous(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        Action.__init__(self, music, menu, view, doCurrentClicked, "previous")
       
    def doAction(self, QMouseEvent):
        pass
            
class Repeat(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        self.isOn = False
        Action.__init__(self, music, menu, view, doCurrentClicked, "repeat")
       
    def doAction(self, QMouseEvent):
        self.isOn = not self.isOn
        if self.isOn:
            pass
        else:
            self.reset()
       
class Shuffle(Action):
    def __init__(self, music, menu, view, doCurrentClicked):
        self.isOn = False
        Action.__init__(self, music, menu, view, doCurrentClicked, "shuffle")
       
    def doAction(self, QMouseEvent):
        self.isOn = not self.isOn
        if self.isOn:
            pass
        else:
            self.reset()
       
class Header(ButtonText):
    def __init__(self, text):
        text = " {} ".format(text)
        attribute = text.lower()
        ButtonText.__init__(self, text, attribute, None if text.strip() == "" else "1px solid black")
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(40)
        self.textClickColor = None
        self.textHoverColor = None
        if text.strip() != "":
            s = Style()
            s.setWidget("QLabel")
            s.setAttribute("background-color", "gray")
            s.setAttribute("color", "white")
            s.setAttribute("border", "1px solid black")
            self.setStyleSheet(s.css())
    
class Menu(Form):
    def __init__(self, music, view):
        self.currentButton = None
        self.view = view
        Form.__init__(self, music)
        self.tablelize(True)     
        buttons = [Home, Profile, Upload, Messages, Accounts, LogOut, LogIn, CreateAccount]
        curClicked = [True]*2 + [False]*6
        self.buttonNames = {}
        buttons = list(zip(buttons, curClicked))
        for i, (b, curClick) in enumerate(buttons):
            b = b(music, self, view, curClick)
            b.setFixedHeight(40)
            b.setFont(self.getFont(14))
            self.buttonNames[b.objectName()] = b
            buttons[i] = b
        boxLayout = BoxLayout(Qt.Horizontal, *buttons)
        boxLayout.setAlignment(Qt.AlignCenter)
        self.addBoxLayout(boxLayout).addRow()
        self.addLabel("").addRow()
        headers = ["", "Name", "Username", "What"]
        for h in headers:
            h = Header(h)
            h.setFont(self.getFont(12))
            self.addButtonText(buttonText=h)
        self.addRow()
        
    def executeButton(self, name = None):
        b = self.currentButton if name is None else self.buttonNames[name]
        if not b is None:
            b.enter(QMouseEvent)
            b.mouseLeftReleased(QMouseEvent)
            b.leave(QMouseEvent)
        
    def changeAccess(self):
        self.executeButton("home")
        self.buttonsVisible = self.getButtonsVisible()
        for _ in range(2):
            for name in self.buttonNames:
                self.buttonNames[name].setVisible(name in self.buttonsVisible)
        
    def getButtonsVisible(self):
        access, _ = self.getParent().getAccess()
        self.access = access
        names = ["home"]
        if access == "guest":
            names += ["log-in", "create-account"]
        elif access == "user" or access == "admin":
            names += ["upload", "profile", "messages", "log-out"]
            if access == "admin":
                names = names[:-1] + ["accounts"] + names[-1:]
        return names
    
class ViewCell(ChildButton):
    def __init__(self, text, index, music, menu, view):
        self.index = index
        self.music = music
        self.menu = menu
        self.view = view
        self.setCells(None)
        self.setRow(None)
        buttonText = ButtonText(text, "text")
        ChildButton.__init__(self, buttonText)
        self.addTextToGrid("text", Qt.AlignCenter)
        self.setObjectName(text)
        self.setFixedHeight(40)
        self.backCol = self.backgroundColor
        
    def setCells(self, cells):
        self.cells = cells
        
    def setRow(self, row):
        self.row = row
       
    def mousePressEvent(self, QMouseEvent):
        ChildButton.mousePressEvent(self, QMouseEvent)
        view = self.view
        keys = list(self.cells.keys())
        if self.objectName() == "Play":
            if keys[-1] == "Song":
                query = "select song_id, get_song_file(song_id) as file from song where user_id = get_account_id(%s) and song_name = %s"
                results = self.music.db.setArgs(keys[2], keys[1]).query(query).results[2][0]
                view.songName = "{}.{}".format(results["song_id"], results["file"][-3:])
                self.row.backgroundColor = self.clickColor
                curRow = view.curRow
                playMusic = self.music.playMusic
                play = playMusic.buttonNames["play"]
                if not curRow is None:
                    if curRow.objectName() != self.row.objectName():
                        curRow.backgroundColor = self.backCol
                        curRow.leave(QMouseEvent)
                        play.doSwitchOn = play.isOn != True
                self.view.curRow = self.row
                query = "select get_song_details_artist(%s) as artist"
                artist = self.music.db.setArgs(results["song_id"]).query(query).results[2][0]["artist"]
                details = keys[1:3] + [artist]
                names = ["name", "user", "artist"]
                details = list(zip(details, names))
                for (d, n) in details:
                    playMusic.details[n].setText("{}: {}".format(n.capitalize(), d))
                play.executePlay()
                
class ViewRow(ScrollButton):
    def __init__(self, index, row, music, menu, view):
        self.row = row
        self.music = music
        self.menu = menu
        self.view = view
        ScrollButton.__init__(self, index)
        self.setObjectName("row{}".format(index))
        cellNames = ["Play", row["Name"]]
        if "Username" in row:
            cellNames += [row["Username"]]
        cellNames += [row["What"].capitalize()]
        cells = {}
        for c in cellNames:
            cells[c] = self.createCell(c)
        self.cells = cells
        for c in cells:
            c = cells[c]
            c.setCells(self.cells)
            c.setRow(self)
            self.addChildren(c)
        boxLayout = BoxLayout(Qt.Horizontal, *cellNames)
        self.addBoxLayoutToGrid(boxLayout)
        self.clickColor = None
        self.hoverColor = Qt.gray
       
    def createCell(self, text):
        return ViewCell(text, self.index, self.music, self.menu, self.view)
    
    def getViewScroll(self):
        return self.view.getParent()
        
    def mouseMove(self, QMouseEvent):
        self.getViewScroll().mouseMove(QMouseEvent)
            
    def mouseLeftPressed(self, QMouseEvent):
        ScrollButton.mouseLeftPressed(self, QMouseEvent)
        self.getViewScroll().mouseLeftPressed(QMouseEvent)
                
    def mouseLeftReleased(self, QMouseEvent):
        h = self.hoverColor
        self.hoverColor = None
        ScrollButton.mouseLeftReleased(self, QMouseEvent)
        self.hoverColor = h
        self.getViewScroll().mouseLeftReleased(QMouseEvent)
        
class View(Form):
    def __init__(self, music):
        self.music = music
        self.songName = ""
        self.curRow = None
        self.index = 1
        Form.__init__(self)
        self.tablelize(True)
        self.setColumnSize(1).setRowsPerChunk(4)
        self.setAddingItems(True)
        
    def createViewRow(self, row):
        return ViewRow(self.index, row, self.music, self.music.menu, self)
    
    def createView(self, rows):
        self.clearForm()
        self.index = 1
        for r in rows:
            self.addButton(self.createViewRow(r), self.getFont())
            self.index += 1
        self.music.loadChunks(self.getParent())
        
class ViewScroll(ScrollArea):
    def __init__(self, view, music):
        self.music = music
        ScrollArea.__init__(self, view.group())
        self.setDraggable(True)
        self.setScrollBarVisibility(False)
        
class PlayMusic(Form):
    def __init__(self, music, menu, view):
        self.menu = menu
        self.view = view
        Form.__init__(self, music)
        self.tablelize(True)
        buttons = [Previous, Play, Next, Shuffle, Repeat]
        curClick = [False, True, False] + [True]*2
        buttons = list(zip(buttons, curClick))
        self.buttonNames = {}
        for i, (b, curClick) in enumerate(buttons):
            b = b(music, menu, view, curClick)
            b.setFont(self.getFont(14))
            b.setFixedHeight(40)
            self.buttonNames[b.objectName()] = b
            buttons[i] = b
        boxLayout = BoxLayout(Qt.Horizontal, *buttons)
        boxLayout.setAlignment(Qt.AlignLeft)
        self.addBoxLayout(boxLayout)
        self.details = {}
        for d in ("name", "user", "artist"):
            self.details[d] = ButtonText(d.capitalize()+":", d, "1px solid black")
            self.addButtonText(font=self.getFont(14), buttonText=self.details[d])
        self.addRow()
        
class MusicSharing(ParentWindow):    
    def __init__(self):
        self.changeAccess = False
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
            self.view = View(self)
            self.menu = Menu(self, self.view)
            vbox.addLayout(self.menu.layout())
            self.viewScroll = ViewScroll(self.view, self)
            vbox.addWidget(self.viewScroll)
            self.playMusic = PlayMusic(self, self.menu, self.view)
            vbox.addWidget(self.playMusic.group(), alignment=Qt.AlignBottom)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(0)
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
                    self.menu.changeAccess()
                self.__start = False
                 
    def loadChunks(self, scroll):
        chunks = 0
        size = scroll.getWidgetOrLayoutRowCount()
        if size < 20:
            chunks = int((20 - size) / scroll.getWidgetOrLayoutRowsPerChunk())
        if chunks > 0:
            for _ in range(chunks):
                scroll.widgetOrLayoutLoadChunk()
                
    def eventFilter(self, QObject, QEvent):
        if self.changeAccess:
            play = self.playMusic.buttonNames["play"]
            if play.isOn:
                play.executePlay()
            play.curSong = ""
            self.view.curRow = None
            self.view.songName = ""
            self.changeAccess = False
            self.menu.changeAccess()
        return ParentWindow.eventFilter(self, QObject, QEvent)
               
    def get_logged_in(self):
        return self.db.query("select get_logged_in_user_id() as logged_in").results[2][0]['logged_in']
    
    def get_logged_in_user(self):
        return self.db.query("select get_logged_in_user() as logged_in").results[2][0]['logged_in']

    def get_admin(self, logged_in):
        return self.db.callFunction("select get_admin_id(%s) as admin_id", logged_in).results[2][0]['admin_id']
    
    def updateLoggedIn(self, username):
        self.db.callProcedure(None, "update_logged_in", username)
        self.changeAccess = True
        
    def updateCurUser(self, username):
        self.db.callProcedure(None, "update_cur_user", username)
        
    def addSongFile(self, song_id, filePath):
        songDir = "{}\\songs".format(os.getcwd())
        if not os.path.exists(songDir):
            os.mkdir(songDir)
        newPath = "{}\\{}.{}".format(songDir, song_id, filePath[-3:])
        shutil.copyfile(filePath, newPath)
    
    def getAccess(self):
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