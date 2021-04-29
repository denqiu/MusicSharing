from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import re, sys, math, time

class Style:
    def __init__(self, style = ""):
        self.__widget = ""
        if style.strip() == "":
            self.clear()
        else:
            self.importStyle(style)
        
    def setWidget(self, name):
        self.__widget = name
        if not name in self.__style:
            self.__style[name] = {}
            
    def getWidget(self):
        return self.__widget
        
    def setAttribute(self, attribute, value):
        self.__style[self.__widget][attribute] = value
        
    def removeWidget(self, widget):
        if widget in self.__style:
            if self.__widget == widget:
                self.__widget = None
            return self.__style.pop(widget)
        return None
                
    def removeAttribute(self, widget, attribute):
        if widget in self.__style:
            if attribute in self.__style[widget]:
                return self.__style[widget].pop(attribute)
        return None
    
    def renameWidget(self, oldWidget, newWidget):
        r = self.removeWidget(oldWidget)
        if not r is None:
            self.__style[newWidget] = r
        
    def renameAttribute(self, widget, oldAttribute, newAttribute):
        r = self.removeAttribute(widget, oldAttribute)
        if not r is None:
            self.__style[widget][newAttribute] = r
        
    def getAttribute(self, widget, attribute):
        if widget in self.__style:
            if attribute in self.__style[widget]:
                return self.__style[widget][attribute]
        return None
        
    def clear(self):
        self.__style = {}
        
    def importStyle(self, style):
        self.clear()
        try:
            widgets = re.findall("(.*){", style)
            for w in widgets:
                a = re.search(w+"{(.*?)}", style, re.DOTALL)
                attributes = re.findall("\n\t(.*):\s(.*);", a.group(1))
                w = w.strip()
                self.__widget = w
                self.__style[w] = dict(attributes)
        except:
            print("Unable to import style")
        
    def css(self):
        return self.__str__()
        
    def __str__(self):
        return "\n\n".join(["{} {{\n\t{}\n}}".format(w, "\n\t".join(["{}: {};".format(a, self.__style[w][a]) for a in self.__style[w]])) for w in self.__style])
    
class SearchForm:
    def __init__(self):
        self.searchVisible(True)
        self.searchRows()
        self.searchNames()
        self.searchClasses()
        self.setMatchCases()
        self.clearResults()
     
    # if visible, all rows that have been loaded onto the layout are searchable. 
    # Otherwise, all rows, regardless of whether they have been loaded or not, are searchable.
    def searchVisible(self, isVisible):
        self.__isVisible = isVisible
        return self
    
    def isVisible(self):
        return self.__isVisible
     
    def searchRows(self, *rows):
        self.rows = rows
        return self
        
    def searchAllRows(self):
        return len(self.rows) == 0
        
    def searchNames(self, *names):
        self.names = names
        return self
        
    def searchClasses(self, *classes):
        self.classes = classes
        return self
        
    def setMatchCases(self, *matchCases):
        self.matchCases = matchCases
        return self
        
    def clearResults(self):
        self.results = {}
        return self
        
    def search(self, num, row):
        names = [(n, n in self.matchCases) for n in self.names]
        foundNames, foundClasses = ([], [] if len(self.classes) > 0 else None)
        row = list(row.items())
        for (name, obj) in row:
            for (n, match) in names:
                b = name == n if match else n.lower() in name.lower()
                if b:
                    foundNames.append((name, obj))
            if not foundClasses is None:
                for c in self.classes:
                    if isinstance(obj, c):
                        foundClasses.append((name, obj))
        if foundClasses is None:
            result = foundNames
        else:
            if len(foundNames) == 0:
                result = foundClasses
            else:
                n = [n for n in foundNames if n in foundClasses]
                c = [c for c in foundClasses if c in foundNames and not c in n]
                result = n+c
        if len(result) > 0:
            self.results[num] = dict(result)
        return self

class ParentWindow(QWidget): #siblings in progress for both ParentWindow and Window
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupWindow()
        self.show()
        
    def getFont(self, size = 10):
        font = QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(size)
        font.setBold(True)
        font.setWeight(75)
        return font
    
    def __siblingIndexes(self, numWindows):
        windows = [s for s in range(numWindows)]
        sibs = []
        for i in windows:
            for j in range(i+1, numWindows):
                sibs.append((i, j))
        return sibs
    
    def __isChild(self, windows):
        windows = list(windows)
        for w in windows:
            if isinstance(w, ChildWindow) or isinstance(w, Window):
                w.setParentWindow(self)
            else:
                print("Child windows must be of type ChildWindow or Window.")
                quit()
        siblings = self.__siblingIndexes(len(windows))
        for (a, b) in siblings:
            windows[a].addSiblings(windows[b])
        return windows
  
    def setChildWindows(self, *childWindows):
        self.__childWindows = self.__isChild(childWindows)
        
    def addChildWindows(self, *childWindows):
        self.__childWindows += self.__isChild(childWindows)
        
    def getChildWindows(self):
        return self.__childWindows
    
    def checkChildWindows(self, child = None):
        c = len(self.__childWindows) > 0
        if not child is None:
            c = c and child in self.__childWindows
        return c
    
    def closeChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.close()
        
    def minimizeChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.minimizeWindow()
    
    def maximizeChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.maximizeWindow()
        
    def restoreChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.restoreWindow()
        
    def setupWindow(self):
        self.setChildWindows()
        self.setObjectName("parentWindow")
        s = Style()
        s.setWidget("QWidget#parentWindow")
        s.setAttribute("background-color", "white")
        self.setStyleSheet(s.css()) 
        self.setFocusPolicy(Qt.StrongFocus)
        self.installEventFilter(self)
    
    def closeEvent(self, QEvent):
        self.closeChildren()
        
    def minimizeEvent(self, QEvent):
        self.minimizeChildren()
        
    def maximizeEvent(self, QEvent):
        pass
    
    def restoreEvent(self, QEvent):
        pass
        
    def changeEvent(self, QEvent):
        if QEvent.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.minimizeEvent(QEvent)
            elif self.isMaximized():
                self.maximizeEvent(QEvent)
            elif self.windowState() == Qt.WindowNoState:
                self.restoreEvent(QEvent)
        elif self.isVisible():
            self.mousePressEvent(QEvent)
                    
    def mousePressEvent(self, QMouseEvent):
        self.restoreChildren()
            
    def focusInEvent(self, QEvent):
        self.mousePressEvent(QEvent)
        
    def eventFilter(self, QObject, QEvent):
        if QEvent.type() == QEvent.NonClientAreaMouseButtonPress:
            if not self.windowState() & Qt.WindowMinimized:
                self.mousePressEvent(QEvent)
        return super().eventFilter(QObject, QEvent)

    def center(self):
        center = QDesktopWidget().availableGeometry().center()
        center.setX(center.x()-self.width())
        center.setY(center.y()-(self.height()//2))
        self.move(center)
    
class ChildWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupWindow()
        self.show()
    
    def getFont(self, size = 10):
        font = QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(size)
        font.setBold(True)
        font.setWeight(75)
        return font
    
    def setParentWindow(self, parentWindow):
        self.__parentWindow = parentWindow
        
    def getParentWindow(self):
        return self.__parentWindow
    
    def checkParentWindow(self):
        return not self.__parentWindow is None
    
    def setSiblings(self, *siblings):
        self.__siblings = list(siblings)
        
    def addSiblings(self, *siblings):
        self.__siblings += list(siblings)
        
    def removeSiblings(self, *siblings):
        for s in siblings:
            if s in self.__siblings:
                self.__siblings.remove(s)
        
    def getSiblings(self):
        return self.__siblings
        
    def __setWindowStates(self):
        w = {}
        w[QWindow.Windowed] = "window" 
        w[QWindow.Minimized] = "minimized" 
        w[QWindow.Maximized] = "maximized" 
        w[QWindow.AutomaticVisibility] = "autoVisibility" 
        w[QWindow.Hidden] = "hidden"
        self.__windowStates = w
        
    def getWindowStates(self):
        return self.__windowStates
    
    def setupWindow(self):
        self.setParentWindow(None)
        self.setSiblings()
        self.__setWindowStates()
        self.setObjectName("childWindow")
        s = Style()
        s.setWidget("QWidget#childWindow")
        s.setAttribute("background-color", "white")
        self.setStyleSheet(s.css()) 
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.installEventFilter(self)

    def getWindowState(self, window):
        return self.__windowStates[int(window.windowState())]
      
    def showEvent(self, QEvent):
        if self.checkParentWindow():
            p = self.__parentWindow
            state = self.getWindowState(p)
            if state == "autoVisibility":
                p.setWindowState(Qt.WindowNoState)
            elif state == "minimized":
                p.showMaximized()
                
    def removeWindow(self):
        if self.checkParentWindow():
            children = self.__parentWindow.getChildWindows()
            if self in children:
                children.remove(self)
            self.__parentWindow.setChildWindows(*children)
    
    def closeEvent(self, QEvent):
        if self.checkParentWindow():
            QWidget.closeEvent(self, QEvent)
            self.removeWindow()
    
    def __change(self):
        p, wins = (self.__parentWindow, [self]+self.__siblings)
        while True:
            wins.append(p)
            if isinstance(p, ParentWindow):
                break
            p = p.getParentWindow()
            if p is None:
                break
        for w in wins[::-1]:
            w.raise_()
            
    def minimizeEvent(self, QEvent):
        pass
            
    def maximizeEvent(self, QEvent):
        pass
    
    def restoreEvent(self, QEvent):
        pass
            
    def changeEvent(self, QEvent):
        if self.checkParentWindow():
            if QEvent.type() == QEvent.WindowStateChange:
                if self.isMinimized():
                    self.minimizeEvent(QEvent)
                elif self.isMaximized():
                    self.maximizeEvent(QEvent)
                elif self.windowState() == Qt.WindowNoState:
                    self.restoreEvent(QEvent)
            elif self.isVisible(): #when opening from taskbar
                self.__change()
            
    def mouseReleaseEvent(self, QMouseEvent):
        self.setFocus()
            
    def eventFilter(self, QObject, QEvent):
        if QEvent.type() == QEvent.NonClientAreaMouseButtonPress:
            self.setFocus()
        return super().eventFilter(QObject, QEvent)
    
    def minimizeWindow(self):
        self.showMinimized()
        
    def maximizeWindow(self):
        self.showMaximized()
    
    '''
        Note: 
            By default, minimizing a child window (of type ChildWindow or Window) will not minimize window. 
            The window will be automatically restored.
            
            Using getWindowState method to check if not auto visible will disable this function.
            However, this will prevent parent windows from restoring their child windows. 
            The child windows have to be restored manually from the taskbar.
    '''
    def restoreWindow(self):
        self.setWindowState(Qt.WindowNoState)
        self.raise_()
        
    def center(self):
        center = QDesktopWidget().availableGeometry().center()
        center.setX(center.x()-self.width())
        center.setY(center.y()-(self.height()//2))
        self.move(center)
    
class Window(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupWindow()
        self.show()
        
    def getFont(self, size = 10):
        font = QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(size)
        font.setBold(True)
        font.setWeight(75)
        return font
    
    def setParentWindow(self, parentWindow):
        self.__parentWindow = parentWindow
        
    def getParentWindow(self):
        return self.__parentWindow
    
    def checkParentWindow(self):
        return not self.__parentWindow is None
    
    def setSiblings(self, *siblings):
        self.__siblings = list(siblings)
        
    def addSiblings(self, *siblings):
        self.__siblings += list(siblings)
        
    def removeSiblings(self, *siblings):
        for s in siblings:
            if s in self.__siblings:
                self.__siblings.remove(s)
        
    def getSiblings(self):
        return self.__siblings
        
    def __siblingIndexes(self, numWindows):
        windows = [s for s in range(numWindows)]
        sibs = []
        for i in windows:
            for j in range(i+1, numWindows):
                sibs.append((i, j))
        return sibs
    
    def __isChild(self, windows):
        windows = list(windows)
        for w in windows:
            if isinstance(w, ChildWindow) or isinstance(w, Window):
                w.setParentWindow(self)
            else:
                print("Child windows must be of type ChildWindow or Window.")
                quit()
        siblings = self.__siblingIndexes(len(windows))
        for (a, b) in siblings:
            windows[a].addSiblings(windows[b])
        return windows
    
    def setChildWindows(self, *childWindows):
        self.__childWindows = self.__isChild(childWindows)
        
    def addChildWindows(self, *childWindows):
        self.__childWindows += self.__isChild(childWindows)
        
    def getChildWindows(self):
        return self.__childWindows
    
    def checkChildWindows(self, child = None):
        c = len(self.__childWindows) > 0
        if not child is None:
            c = c and child in self.__childWindows
        return c
    
    def closeChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.close()
      
    def minimizeChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.minimizeWindow()
        
    def maximizeChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.maximizeWindow()
        
    def restoreChildren(self):
        if self.checkChildWindows():
            for c in self.__childWindows:
                c.restoreWindow()
        
    def __setWindowStates(self):
        w = {}
        w[QWindow.Windowed] = "window" 
        w[QWindow.Minimized] = "minimized" 
        w[QWindow.Maximized] = "maximized" 
        w[QWindow.AutomaticVisibility] = "autoVisibility" 
        w[QWindow.Hidden] = "hidden"
        self.__windowStates = w
        
    def getWindowStates(self):
        return self.__windowStates
    
    def setupWindow(self):
        self.setParentWindow(None)
        self.setSiblings()
        self.setChildWindows()
        self.__setWindowStates()
        self.setObjectName("window")
        s = Style()
        s.setWidget("QWidget#window")
        s.setAttribute("background-color", "white")
        self.setStyleSheet(s.css()) 
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.installEventFilter(self)
        
    def getWindowState(self, window):
        return self.__windowStates[int(window.windowState())]
      
    def showEvent(self, QEvent):
        if self.checkParentWindow():
            p = self.__parentWindow
            state = self.getWindowState(p)
            if state == "autoVisibility":
                p.setWindowState(Qt.WindowNoState)
            elif state == "minimized":
                p.showMaximized()
    
    def closeEvent(self, QEvent):
        self.closeChildren()
        if self.checkParentWindow():
            QWidget.closeEvent(self, QEvent)
            children = self.__parentWindow.getChildWindows()
            if self in children:
                children.remove(self)
            self.__parentWindow.setChildWindows(*children)
            
    def __change(self):
        p, wins = (self.__parentWindow, [self]+self.__siblings)
        while True:
            wins.append(p)
            if isinstance(p, ParentWindow):
                break
            p = p.getParentWindow()
            if p is None:
                break
        for w in wins[::-1]:
            w.raise_()
            
    def minimizeEvent(self, QEvent):
        self.minimizeChildren()
        
    def maximizeEvent(self, QEvent):
        pass
    
    def restoreEvent(self, QEvent):
        pass
            
    def changeEvent(self, QEvent):
        if QEvent.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.minimizeEvent(QEvent)
            elif self.isMaximized():
                self.maximizeEvent(QEvent)
            elif self.windowState() == Qt.WindowNoState:
                self.restoreEvent(QEvent)
        else:
            if self.checkParentWindow():
                if self.isVisible(): #when opening from taskbar
                    self.__change()
            if self.isVisible():
                self.mousePressEvent(QEvent)
            
    def mousePressEvent(self, QMouseEvent):
        self.restoreChildren()
            
    def focusInEvent(self, QEvent):
        self.mousePressEvent(QEvent)
        
    def mouseReleaseEvent(self, QMouseEvent):
        self.setFocus()
            
    def eventFilter(self, QObject, QEvent):
        if QEvent.type() == QEvent.NonClientAreaMouseButtonPress:
            if not self.windowState() & Qt.WindowMinimized:
                self.mousePressEvent(QEvent)
            self.setFocus()
        return super().eventFilter(QObject, QEvent)
        
    def minimizeWindow(self):
        self.showMinimized()
        self.minimizeChildren()
        
    def maximizeWindow(self):
        self.showMaximized()
    
    '''
        Note: 
            By default, minimizing a child window (of type ChildWindow or Window) will not minimize window. 
            The window will be automatically restored.
            
            Using getWindowState method to check if not auto visible will disable this function.
            However, this will prevent parent windows from restoring their child windows. 
            The child windows have to be restored manually from the taskbar.
    '''
    def restoreWindow(self): 
        self.setWindowState(Qt.WindowNoState)
        self.raise_()
        self.restoreChildren()
        
    def center(self):
        center = QDesktopWidget().availableGeometry().center()
        center.setX(center.x()-self.width())
        center.setY(center.y()-(self.height()//2))
        self.move(center)
    
class ButtonText(QLabel):
    def __init__(self, text = "", attribute = "", border = None):
        super().__init__()
        self.startPosition = None
        self.textBackgroundColor = Qt.black
        self.textClickColor = None
        self.textHoverColor = Qt.white
        self.entered = False
        self.setObjectName("text")
        if text != "":
            self.setToolTip(text)
        if attribute != "": 
            self.setObjectName(attribute)
        if border is None: 
            text = " " + text
        if text != "":
            self.setText(text)
        s = Style()
        s.setWidget("QLabel")
        s.setAttribute("background-color", "transparent")
        if not border is None: 
            s.setAttribute("border", border)
            if attribute.strip() == "":
                self.setObjectName("border")
        self.setStyleSheet(s.css())
        self.setButton(None)
                
    def getText(self):
        return self.toolTip()
    
    def checkButton(self):
        return self.__button is None
  
    def setButton(self, button):
        self.__button = button
        
    def getButton(self):
        return self.__button
        
    def enterText(self, QMouseEvent):
        self.entered = True
            
    def enterEvent(self, QMouseEvent):
        if self.checkButton():
            self.enterText(QMouseEvent)
        else:
            self.__button.enterEvent(QMouseEvent)
            
    def leaveText(self, QMouseEvent):
        self.entered = False
          
    def leaveEvent(self, QMouseEvent):
        if self.checkButton():
            self.leaveText(QMouseEvent)
        else:
            self.__button.leaveEvent(QMouseEvent)
            
    def mouseMove(self, QMouseEvent):
        pass
    
    def mouseMoveEvent(self, QMouseEvent):
        if self.checkButton():
            self.mouseMove(QMouseEvent)
        else:
            self.__button.mouseMoveEvent(QMouseEvent)
            
    def mouseLeftPressed(self, QMouseEvent):
        self.startPosition = QMouseEvent.pos()
    
    def mouseMiddlePressed(self, QMouseEvent):
        pass
    
    def mouseRightPressed(self, QMouseEvent):
        pass
            
    def mousePressText(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddlePressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed(QMouseEvent)
        
    def mousePressEvent(self, QMouseEvent):
        if self.checkButton():
            self.mousePressText(QMouseEvent)
        else:
            self.__button.mousePressEvent(QMouseEvent)

    def mouseLeftReleased(self, QMouseEvent):
        self.startPosition = None
    
    def mouseMiddleReleased(self, QMouseEvent):
        pass
    
    def mouseRightReleased(self, QMouseEvent):
        pass
            
    def mouseReleaseText(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddleReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased(QMouseEvent)
        
    def mouseReleaseEvent(self, QMouseEvent):
        if self.checkButton():
            self.mouseReleaseText(QMouseEvent)
        else:
            self.__button.mouseReleaseEvent(QMouseEvent)

class BoxLayout:
    def __init__(self, alignment, *items):
        self.setLayout(alignment)
        self.setItems(*items)
        self.setAttribute()
        self.setFont(None)
        self.setVisible(False)
        
    def setVisible(self, isVisible):
        self.__visible = isVisible
        
    def isVisible(self):
        return self.__visible
        
    def setFont(self, font):
        self.__font = font
        
    def setAttribute(self, attribute = ""):
        align = {QVBoxLayout: Qt.Vertical, QHBoxLayout: Qt.Horizontal}[type(self.__layout)]
        align = {Qt.Vertical: "v", Qt.Horizontal: "h"}[align]
        if attribute.strip() != "":
            attribute = "-" + attribute.strip()
        self.__attribute = "{}layout{}".format(align, attribute)
        self.__layout.setObjectName(self.__attribute)
        
    def getAttribute(self):
        return self.__attribute
        
    def setLayout(self, alignment):
        self.__layout = {Qt.Vertical: QVBoxLayout, Qt.Horizontal: QHBoxLayout}[alignment]()
        
    def setItems(self, *items):
        self.__items = list(items)
        
    def __method(self, items):
        method = {True: self.__layout.addWidget, False: self.__layout.addLayout}
        widgets = (QLabel, QGroupBox, QScrollArea)
        for i in items:
            b = i
            if not self.__font is None:
                if b.font() == QLabel().font():
                    b.setFont(self.__font)
            m = False
            for w in widgets:
                w = isinstance(i, w)
                if w:
                    m = w
                    break
            if not m:
                b = b.layout()
            method[m](b)
    
    def addItems(self, *items):
        self.__items += list(items)
        self.__method(items)
        
    def removeItems(self, *items):
        for i in items:
            if i in self.__items:
                self.__items.remove(i)
                self.__layout.removeItem(i)
        
    def getItems(self):
        return self.__items
    
    def size(self):
        return len(self.__items)
        
    def layout(self):
        self.__method(self.__items)
        self.setVisible(True)
        return self.__layout
            
class Button(QWidget):
    def __init__(self, *text):
        self.__mod = sys.modules[__name__]
        ignores = ("Window", "Password")
        self.__childNames = []
        for c in dir(self.__mod):
            if c[:len("Child")] == "Child":
                if not c[len("Child"):] in ignores:              
                    self.__childNames.append(c)
        self.__childClasses = [getattr(self.__mod, name) for name in self.__childNames]
        self.__checkChildren = [c.replace("Child", "child-").lower() for c in self.__childNames]
        self.__childVariables = []
        for c in self.__checkChildren:
            c = c.replace("child-", "")
            if c[-1] == 'x':
                c += "es"
            else:
                c += "s"
            self.__childVariables.append(c)
        self.__tagNames = dict(zip(self.__childNames, self.__checkChildren))
        self.__tagClasses = dict(zip(self.__childClasses, self.__childNames))
        self.__checks = None
        self.tablelize(False)
        super().__init__()
        self.startPosition = None
        self.backgroundColor = Qt.white
        self.clickColor = Qt.gray
        self.hoverColor = Qt.black
        self.entered = False
        self.clearText()
        self.clearAllChildren()
        self.addText(ButtonText(border="1px solid black"))
        self.addText(*text)
        self.clearLayout()
        self.__layout[self.__layoutSize()] = {self: (None, 0)}
        self.addTextToGrid("border")
        self.setObjectName("button") 
        
    def tablelize(self, tablelize):
        self.__tablelize = tablelize
    
    def __checkChildClass(self, classObject):
        for i, c in enumerate(self.__childClasses):
            if isinstance(classObject, c):
                return (True, c, self.__childVariables[i])
        return (False, None, -1)
        
    def __objects(self, what = None):
        objects = [self.__text] + list(self.__children.values())
        if what is None:
            return objects
        else:
            if what == "classes":
                objClasses = [ButtonText] + self.__childClasses
                return dict(zip(objClasses, objects))
            else:
                obdict = {}
                for o in objects:
                    obdict = {**obdict, **o}
                if what == "dict":
                    return obdict
                elif what == "items":
                    return tuple(obdict.items())
                elif what == "keys":
                    return tuple(obdict.keys())
                elif what == "values":
                    return tuple(obdict.values())
        
    def setVisible(self, isVisible):
        for o in self.__objects("values"):
            o.setVisible(isVisible)
        QWidget.setVisible(self, isVisible)
        
    def setEnabled(self, isEnabled):
        for o in self.__objects("values"):
            o.setEnabled(isEnabled)
        QWidget.setEnabled(self, isEnabled)
                
    def __checkName(self, obj, check):
        name = obj.objectName()
        if check in name:
            if self.__checks is None:
                checks = dict(zip(self.__checkChildren, list(self.__children.values())))
                self.__checks = {**{"text": self.__text}, **checks}
            name = [n for n in reversed(self.__checks[check].keys()) if not re.search("^"+check+"\d*$", n) is None]
            if not name == []:
                name = name[0]
                s = re.search(check+"(\d*)", name)
                name = check
                i = s.group(1)
                if i == "":
                    name += "1"
                else:
                    name += str(int(i)+1)
                obj.setObjectName(name)  
        return obj 
            
    def clearText(self):
        self.__text = {}
        
    def addText(self, *text):
        for t in text:
            if isinstance(t, ButtonText):
                t.setButton(self)
                t = self.__checkName(t, "text")
                self.__text[t.objectName()] = t
            
    def removeText(self, *text):
        rem = {}
        for t in text:
            if isinstance(t, ButtonText):
                t = t.objectName()
            if t != "border":
                if t in self.__text:
                    rem[t] = self.__text.pop(t)
                else:
                    print("Attribute: {} not found".format(t))
        return rem
            
    def getText(self, *text):
        if len(text) == 0:
            return self.__text
        else:
            texts = {}
            for t in text:
                if t in self.__text:
                    texts[t] = self.__text[t]
            return texts
    
    def mapText(self, *text):
        text, texts = (self.getText(*text), [])
        for t in text:
            if t != "border":
                texts.append(self.__checkObject(text[t]))
        return "\n".join(texts)
    
    def clearAllChildren(self):
        self.__children = {c: {} for c in self.__childVariables}
        
    def clearChildren(self, what):
        if what in self.__children:
            self.__checkChildren[what] = {}
            
    def addChildren(self, *children):
        for c in children:
            b, cob, key = self.__checkChildClass(c)
            if b:
                c.setButton(self)
                c = self.__checkName(c, self.__tagNames[self.__tagClasses[cob]])
                self.__children[key][c.objectName()] = c
            
    def removeChildren(self, *children):
        rem = {}
        for c in children:
            b, _, key = self.__checkChildClass(c)
            if b:
                c = c.objectName()
            if c in self.__children[key]:
                rem[c] = self.__children[key].pop(c)
            else:
                if key[-2:] == "es":
                    k = key[:-2].replace("box", " box")
                else:
                    k = key[:-1]
                print("Child {}: {} not found".format(k, c))
        return rem
    
    def getAllChildren(self, *children):
        allChildren = {}
        for what in self.__children:
            allChildren = {**allChildren, **self.getChildren(what, *children)}
        return allChildren
                
    def getChildren(self, what, *children):
        if len(children) == 0:
            if what in self.__children:
                return self.__children[what]
            return {}
        else:
            getChildren = {}
            for c in children:
                if what in self.__children:
                    if c in self.__children[what]:
                        getChildren[c] = self.__children[what][c]
            return getChildren
    
    def setFixedSize(self, *args, **kwargs):
        QWidget.setFixedSize(self, *args, **kwargs)
        if "border" in self.__text:
            self.__text["border"].setFixedSize(*args, **kwargs)
        
    def setFixedHeight(self, *args, **kwargs):
        QWidget.setFixedHeight(self, *args, **kwargs)
        if "border" in self.__text:
            self.__text["border"].setFixedHeight(*args, **kwargs)
            
    def setFixedWidth(self, *args, **kwargs):
        QWidget.setFixedWidth(self, *args, **kwargs)
        if "border" in self.__text:
            self.__text["border"].setFixedWidth(*args, **kwargs)
            
    def setFont(self, *args, **kwargs):
        for t in self.__text:
            if t != "border":
                self.__text[t].setFont(*args, **kwargs)
        for obj in self.__objects()[1:]:
            for o in obj:
                obj[o].setFont(*args, **kwargs)
                
    def clearLayout(self):
        self.__layout = {}
        self.__layoutNames = {}
        
    def __layoutSize(self):
        return len(self.__layout)+1
    
    def __checkObject(self, obj, objClass = None):
        if objClass is None:
            objClasses = self.__objects("classes")
            objClasses.pop(ButtonText)
        else:
            objClasses = [objClass]
        for objClass in objClasses:
            if isinstance(obj, objClass):
                obj = obj.objectName()
            if type(obj) is str:
                objects = self.__objects("classes")[objClass]
                if obj in objects:
                    return objects[obj]
        return None
    
    def __appendToLayout(self, obj, name, alignment, move, i):
        if i is None:
            i = self.__layoutNames[name] if name in self.__layoutNames else self.__layoutSize()
        self.__layout[i] = {obj: (alignment, move)}
        self.__layoutNames[name] = i
    
    def addTextToGrid(self, text, alignment = None, move = 0, insert = None):
        text = self.__checkObject(text, ButtonText)
        if text is None:
            print("No ButtonText exists with this attribute")
        else:
            self.__appendToLayout(text, text.objectName(), alignment, move, insert)
            
    def addChildToGrid(self, child, alignment = None, move = 0, insert = None):
        child = self.__checkObject(child)
        if child is None:
            print("No Child exists with this attribute")
        else:
            self.__appendToLayout(child, child.objectName(), alignment, move, insert)
            
    def addBoxLayoutToGrid(self, boxLayout, alignment = None, move = 0, insert = None):
        items = boxLayout.getItems()
        for i, b in enumerate(items):
            if type(b) is str:
                for j in self.__objects():
                    if b in j:
                        items[i] = j[b]
                        break
        boxLayout.setItems(*items)
        self.__appendToLayout(boxLayout, boxLayout.getAttribute(), alignment, move, insert)
        
    def removeFromGrid(self, *grid):
        rem = {}
        for r in grid:
            if r in self.__layoutNames:
                i = self.__layoutNames[r]
                rem[i] = {r: self.__layout.pop(i)}
                lay = [(j-1, j) for j in self.__layout if j > i]
                if len(lay) > 0:
                    for (newKey, key) in lay:
                        self.__layout[newKey] = self.__layout.pop(key)
                names = [(n, self.__layoutNames[n]-1) for n in self.__layoutNames if self.__layoutNames[n] > i]
                if len(names) > 0:
                    for (key, value) in names:
                        self.__layoutNames[key] = value
            else:
                print("{} not found".format(r))
        return rem
    
    def __methods(self):
        g = QGridLayout()
        if self.__tablelize:
            g.setSpacing(0)
            g.setContentsMargins(0, 0, 0, 0)
        objClasses = [type(self), ButtonText, BoxLayout] + self.__childClasses
        lays = [g.addWidget]*2 + [g.addLayout] * (len(objClasses)-2)
        methods = dict(zip(objClasses, lays))
        return (g, methods)        
                                        
    def layout(self):
        g, methods = self.__methods()
        for i in range(1, self.__layoutSize()):
            b, (align, move) = list(self.__layout[i].items())[0]
            a = b
            layoutChecks = []
            layoutChecks.append(isinstance(b, BoxLayout))
            layoutChecks.append(i > 1 and isinstance(b, ChildButton))
            childClasses = [c for c in self.__childClasses if not c is ChildButton]
            for child in childClasses:
                layoutChecks.append(isinstance(b, child))
            for j in tuple(layoutChecks):
                if j: 
                    a = a.layout()
                    break
            args = [a, 0, move]
            if not align is None:
                args.append(align)
            for m in methods:
                c = isinstance(b, m) if i > 1 else type(b) is m
                if c:
                    methods[m](*args)
                    break
        return g
        
    def setColor(self, widget, role, color):
        if not color is None:
            p = widget.palette()
            p.setColor(role, color)
            if not widget.autoFillBackground():
                widget.setAutoFillBackground(True)
            widget.setPalette(p)
            widget.show()
                        
    def enter(self, QMouseEvent):
        if self.isEnabled():
            self.entered = True
            self.setColor(self, self.backgroundRole(), self.hoverColor)
            for t in self.__text.values():
                self.setColor(t, t.foregroundRole(), t.textHoverColor)
                
    def enterEvent(self, QMouseEvent):
        self.enter(QMouseEvent)
                
    def leave(self, QMouseEvent):  
        if self.isEnabled():
            self.entered = False
            self.setColor(self, self.backgroundRole(), self.backgroundColor)
            for t in self.__text.values():
                self.setColor(t, t.foregroundRole(), t.textBackgroundColor)
                
    def leaveEvent(self, QMouseEvent):
        self.leave(QMouseEvent)
        
    def mouseMove(self, QMouseEvent):
        pass
        
    def mouseMoveEvent(self, QMouseEvent):
        if self.isEnabled():
            self.mouseMove(QMouseEvent)
            
    def mouseRightPressed(self, QMouseEvent):
        pass
    
    def mouseMiddlePressed(self, QMouseEvent):
        pass
    
    def mouseLeftPressed(self, QMouseEvent):
        self.setColor(self, self.backgroundRole(), self.clickColor)
        self.startPosition = QMouseEvent.pos()
        
    def mousePressed(self, QMouseEvent):       
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddlePressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed(QMouseEvent)
                
    def mousePressEvent(self, QMouseEvent):
        self.mousePressed(QMouseEvent)
        
    def mouseRightReleased(self, QMouseEvent):
        pass
    
    def mouseMiddleReleased(self, QMouseEvent):
        pass
    
    def mouseLeftReleased(self, QMouseEvent):
        self.setColor(self, self.backgroundRole(), self.hoverColor)
        self.setFocus()
        self.startPosition = None

    def mouseReleased(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddleReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased(QMouseEvent)
                
    def mouseReleaseEvent(self, QMouseEvent):
        self.mouseReleased(QMouseEvent)
        
    def leaveOnMove(self, QMouseEvent):
        s = self.startPosition
        if not s is None:
            if s != QMouseEvent.pos():
                self.leave(QMouseEvent)
                        
class ChildButton(Button):
    def __init__(self, *text):
        super().__init__(*text)
        self.setButton(None)
        self.setObjectName("child-button")
        
    def checkButton(self):
        return self.__button is None
        
    def setButton(self, button):
        self.__button = button
        
    def getButton(self):
        return self.__button
            
    def enterEvent(self, QMouseEvent):
        if self.checkButton():
            self.enter(QMouseEvent)
        else:
            self.__button.enterEvent(QMouseEvent)
        
    def leaveEvent(self, QMouseEvent):
        if self.checkButton():
            self.leave(QMouseEvent)
        else:
            self.__button.leaveEvent(QMouseEvent)
            
    def mouseMoveEvent(self, QMouseEvent):
        if self.checkButton():
            self.mouseMove(QMouseEvent)
        else:
            self.__button.mouseMoveEvent(QMouseEvent)
  
    def mousePressEvent(self, QMouseEvent):
        if self.checkButton():
            self.mousePressed(QMouseEvent)
        else:
            self.__button.mousePressEvent(QMouseEvent)
            
    def mouseReleaseEvent(self, QMouseEvent):
        if self.checkButton():
            self.mouseReleased(QMouseEvent)
        else:
            self.__button.mouseReleaseEvent(QMouseEvent)
            
class ScrollBar(QScrollBar):
    def __init__(self):
        self.pressed = False
        QScrollBar.__init__(self)
    
    def getScrollArea(self):
        return self.parent().parent()
    
    def exists(self):
        if self.isVisible():
            return True
        else:
            for i in ("width: 0", "height: 0"):
                if i in self.styleSheet():
                    return True
        return False
   
    def mouseRightPressed(self, QMouseEvent):
        pass
        
    def mouseMiddlePressed(self, QMouseEvent):
        pass
    
    def mouseLeftPressed(self, QMouseEvent):
        self.pressed = True
        
    def mousePressed(self, QMouseEvent):       
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddlePressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed(QMouseEvent)
                
    def mousePressEvent(self, QMouseEvent):
        QScrollBar.mousePressEvent(self, QMouseEvent)
        self.mousePressed(QMouseEvent)
        
    def mouseRightReleased(self, QMouseEvent):
        pass
        
    def mouseMiddleReleased(self, QMouseEvent):
        pass
    
    def mouseLeftReleased(self, QMouseEvent):
        self.pressed = False

    def mouseReleased(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddleReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased(QMouseEvent)
                
    def mouseReleaseEvent(self, QMouseEvent):
        QScrollBar.mouseReleaseEvent(self, QMouseEvent)
        self.mouseReleased(QMouseEvent)
        
class ScrollArea(QScrollArea):   
    def __init__(self, obj, draggable = False, *dragMouseButtons):
        self.setDraggable(draggable, *dragMouseButtons)
        self.setIncrementBarValue(4)
        self.entered = False
        super().__init__()
        self.setHorizontalScrollBar(ScrollBar())
        self.setVerticalScrollBar(ScrollBar())
        self.__orientation = (Qt.Vertical, Qt.Horizontal)
        attributes = ("width", "height")
        bars = (self.verticalScrollBar(), self.horizontalScrollBar())
        values = (0, 0)
        arrows = ((Qt.Key_Up, Qt.Key_Down), (Qt.Key_Left, Qt.Key_Right))
        direction = (-self.getIncrementBarValue(), self.getIncrementBarValue())
        self.__direction = self.__dictOrientation(direction)
        self.__attributes = self.__dictOrientation(attributes)
        self.scrollBars = self.__dictOrientation(bars)
        self.scrollBarValues = self.__dictOrientation(values)
        arrowKeys = [dict(zip(a, direction)) for a in arrows]
        self.arrowKeys = self.__dictOrientation(arrowKeys)
        valueChanges = (self.verticalScrollValueChanged, self.horizontalScrollValueChanged)
        valueChanges = self.__dictOrientation(valueChanges)
        for s in self.scrollBars:
            self.scrollBars[s].valueChanged.connect(valueChanges[s])
        defaultValues = (self.defaultVerticalScrollValue, self.defaultHorizontalScrollValue)
        self.__defaultValues = self.__dictOrientation(defaultValues)
        self.__startDefault = self.__dictOrientation((False, False))
        self.setObjectName("scroll-area")
        self.currentIndex = -1
        self.previousButton = None
        if isinstance(obj, Form):
            obj.setParent(self)
            obj.layout()
        else:
            layouts = (QHBoxLayout, QVBoxLayout, QFormLayout)
            isLayout = False
            for lay in layouts:
                if isinstance(obj, lay):
                    isLayout = True
                    break
            if isinstance(obj, Group):
                obj.getForm().setParent(self)
            self.setLayout(obj) if isLayout else self.setWidget(obj)
        self.setWidgetResizable(True)
        self.setBackground()
        self.installEventFilter(self)
        
    def __dictOrientation(self, what):
        return dict(zip(self.__orientation, what))
        
    def setIncrementBarValue(self, value = 1):
        self.__incrementBarValue = value
        
    def getIncrementBarValue(self):
        return self.__incrementBarValue
    
    def getWidgetOrLayout(self):
        for i in (self.widget(), self.layout()):
            if not i is None:
                return i
        return None
    
    def checkWidgetOrLayout(self):
        return self.getWidgetOrLayout() is None
     
    def setWidgetOrLayoutVisible(self, isVisible):
        if not self.checkWidgetOrLayout():
            self.getWidgetOrLayout().setVisible(isVisible)
        
    def setWidgetOrLayoutEnabled(self, isEnabled):
        if not self.checkWidgetOrLayout():
            self.getWidgetOrLayout().setEnabled(isEnabled)
        
    def isWidgetOrLayoutVisible(self):
        if self.checkWidgetOrLayout():
            return False
        return self.getWidgetOrLayout().isVisible()

    def isWidgetOrLayoutEnabled(self):
        if self.checkWidgetOrLayout():
            return False
        return self.getWidgetOrLayout().isEnabled()
    
    def isWidgetOrLayoutWaitScreenVisible(self):
        if self.checkWidgetOrLayout():
            return False
        return self.getWidgetOrLayout().isWaitScreenVisible()
        
    def setWidgetOrLayoutWaitScreenVisible(self, isWaitVisible):
        if not self.checkWidgetOrLayout():
            self.getWidgetOrLayout().setWaitScreenVisible(isWaitVisible)
        
    def widgetOrLayoutLoadChunk(self):
        if not self.checkWidgetOrLayout():
            self.getWidgetOrLayout().loadChunk()
           
    def getWidgetOrLayoutRowsPerChunk(self):
        if self.checkWidgetOrLayout():
            return 0
        return self.getWidgetOrLayout().getRowsPerChunk()
    
    def getWidgetOrLayoutRowCount(self):
        if self.checkWidgetOrLayout():
            return 0
        return self.getWidgetOrLayout().getRowCount()
           
    def setBackground(self, name = None, color = "white"):
        if not name is None:
            self.setObjectName(name)
        s = Style()
        s.setWidget("QWidget#{}".format(self.objectName()))
        s.setAttribute("background-color", color)
        s.setAttribute("border", "0")
        self.setStyleSheet(s.css())
                        
    def setMouseButtonsToDragScroll(self, *mouseButtons):
        self.__scrollMouseButtons = mouseButtons
        
    def getMouseButtonsToDragScroll(self):
        return self.__scrollMouseButtons
        
    def setScrollBarVisibility(self, isVisible, orientation = None):
        attributes = self.__attributes
        if not orientation is None:
            if orientation in attributes:
                attributes = {orientation: attributes[orientation]}
        for a in attributes:
            self.scrollBars[a].setStyleSheet("" if isVisible else "{}: 0".format(attributes[a]))
                        
    def setDraggable(self, draggable, *dragMouseButtons):
        self.draggable = draggable
        self.__isScrollOwner = draggable
        self.startPosition = None
        if draggable:
            if len(dragMouseButtons) > 0:
                self.setMouseButtonsToDragScroll(*dragMouseButtons)
            else:
                self.setMouseButtonsToDragScroll(Qt.LeftButton)
        else:
            self.setMouseButtonsToDragScroll()
      
    def setCurrentIndex(self, i):
        self.currentIndex = i
    
    def isCurrentIndex(self, i):
        return i == self.currentIndex
    
    def setPreviousButton(self, pb):
        self.previousButton = pb
                
    def checkPreviousButton(self, currentButton, QMouseEvent):
        if not self.previousButton is None:
            if not currentButton is self.previousButton:
                if self.previousButton.entered:
                    self.previousButton.leaveEvent(QMouseEvent)
              
    def horizontalScrollValueChanged(self):
        return self.__scrollValueChanged(Qt.Horizontal)
    
    def verticalScrollValueChanged(self):
        return self.__scrollValueChanged(Qt.Vertical)
    
    def defaultHorizontalScrollValue(self):
        h = Qt.Horizontal
        self.__startDefault[h] = True
        return self.scrollBarValues[h]
    
    def defaultVerticalScrollValue(self):
        v = Qt.Vertical
        self.__startDefault[v] = True
        return self.scrollBarValues[v]
    
    def startDefaultValues(self, orientation = None):
        d = self.__startDefault
        if not orientation is None:
            if orientation in d:
                d = {orientation: d[orientation]}
        d = tuple(d.keys())
        for orien in d:
            self.__startDefault.pop(orien)
            self.__startDefault[orien] = False
    
    def __scrollValueChanged(self, orientation):
        bar = self.scrollBars[orientation]
        oldValue, newValue = (self.scrollBarValues[orientation], bar.value())
        if abs(oldValue-newValue) == 1:
            self.scrollBarValues[orientation] = newValue
        if newValue == bar.maximum():
            self.widgetOrLayoutLoadChunk()
        return (self.scrollBarValues[orientation], bar)
    
    def __checkValueRange(self, value, orientation, bar):
        if value < bar.minimum():
            value = bar.minimum()
        elif value > bar.maximum():
            value = bar.maximum()
        self.scrollBarValues[orientation] = value
                    
    def __calculateScrollValue(self, orientation, currentPosition, startPosition):
        bar = self.scrollBars[orientation]
        value = bar.value() + (startPosition-currentPosition)
        self.__checkValueRange(value, orientation, bar)
                     
    def enter(self, QMouseEvent):
        if self.isEnabled():
            self.entered = True
            
    def enterEvent(self, QMouseEvent):
        self.enter(QMouseEvent)
                
    def leave(self, QMouseEvent):  
        if self.isEnabled():
            self.entered = False
            
    def leaveEvent(self, QMouseEvent):
        self.leave(QMouseEvent)
        
    def mouseMove(self, QMouseEvent):
        if self.draggable:
            if not self.startPosition is None:
                currentPosition = QMouseEvent.pos()
                if self.verticalScrollBar().exists():
                    self.__calculateScrollValue(Qt.Vertical, currentPosition.y(), self.startPosition.y())
                if self.horizontalScrollBar().exists():
                    self.__calculateScrollValue(Qt.Horizontal, currentPosition.x(), self.startPosition.x())
                if self.__isScrollOwner:
                    self.startPosition = currentPosition
                    
    def mouseMoveEvent(self, QMouseEvent):
        if self.isEnabled():
            if not self.getWidgetOrLayout().isWaitScreenVisible():
                self.mouseMove(QMouseEvent)
    
    def __startScroll(self, QMouseEvent, mouseButton):
        if self.draggable:
            if mouseButton in self.__scrollMouseButtons:
                self.startPosition = QMouseEvent.pos()
                self.__isScrollOwner = self.getWidgetOrLayout() is QApplication.widgetAt(QMouseEvent.globalPos())
                   
    def mouseRightPressed(self, QMouseEvent):
        self.__startScroll(QMouseEvent, Qt.RightButton)
        
    def mouseMiddlePressed(self, QMouseEvent):
        self.__startScroll(QMouseEvent, Qt.MiddleButton)
    
    def mouseLeftPressed(self, QMouseEvent):
        self.__startScroll(QMouseEvent, Qt.LeftButton)
        
    def mousePressed(self, QMouseEvent):       
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddlePressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed(QMouseEvent)
                
    def mousePressEvent(self, QMouseEvent):
        if not self.getWidgetOrLayout().isWaitScreenVisible():
            self.mousePressed(QMouseEvent)
        
    def __endScroll(self, mouseButton):
        if self.draggable:
            if mouseButton in self.__scrollMouseButtons:
                self.startPosition = None
                self.__isScrollOwner = True
    
    def mouseRightReleased(self, QMouseEvent):
        self.__endScroll(Qt.RightButton)
        
    def mouseMiddleReleased(self, QMouseEvent):
        self.__endScroll(Qt.MiddleButton)
    
    def mouseLeftReleased(self, QMouseEvent):
        self.__endScroll(Qt.LeftButton)

    def mouseReleased(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddleReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased(QMouseEvent)
                
    def mouseReleaseEvent(self, QMouseEvent):
        if not self.getWidgetOrLayout().isWaitScreenVisible():
            self.mouseReleased(QMouseEvent)
        
    def valueToSet(self, orientation):
        return self.scrollBarValues[orientation]
        
    #Note: Scrollbars will reset their values when mouse cursor strays too far away in traditional scrolling.
    def __setScrollBarValues(self, QObject, QEvent):
        for s in self.scrollBars:
            bar = self.scrollBars[s]
            if bar.exists():
                value = None
                if bar.pressed: #traditional scrolling
                    value = bar.value()
                elif type(QEvent) is QKeyEvent: #arrow keys
                    key = QEvent.key()
                    if key in self.arrowKeys[s]:
                        value = self.scrollBarValues[s] + self.arrowKeys[s][key]
                elif type(QEvent) is QWheelEvent: #mouse wheel and touchpad
                    if QObject.event(QEvent):
                        delta = QEvent.angleDelta()
                        delta = self.__dictOrientation((delta.y(), delta.x()))
                        value = (delta[s] // 120) * self.getIncrementBarValue()
                        value = self.scrollBarValues[s] + (self.__direction[s]*value)
                elif not self.__startDefault[s]: #default values
                    value = self.__defaultValues[s]()
                if not value is None:
                    self.__checkValueRange(value, s, bar)
                bar.setValue(self.valueToSet(s))
        
    def eventFilter(self, QObject, QEvent):
        self.__setScrollBarValues(QObject, QEvent)
        return QScrollArea.eventFilter(self, QObject, QEvent)
         
class ScrollButton(Button):
    def __init__(self, index, *text):
        super().__init__(*text)
        self.index = index
        self.setObjectName("scroll-button")
        
    def getScrollArea(self):
        p = self.parent()
        while not isinstance(p, ScrollArea):
            p = p.parent() 
        return p
    
    def enterEvent(self, QMouseEvent):
        scroll = self.getScrollArea()
        scroll.checkPreviousButton(self, QMouseEvent)
        scroll.setCurrentIndex(self.index)
        scroll.setPreviousButton(self)
        Button.enterEvent(self, QMouseEvent)
        
    def leaveEvent(self, QMouseEvent):
        self.getScrollArea().setCurrentIndex(-1)
        Button.leaveEvent(self, QMouseEvent)
        
    def mousePressEvent(self, QMouseEvent):
        if self.getScrollArea().isCurrentIndex(self.index):
            Button.mousePressEvent(self, QMouseEvent)
            
    def mouseReleaseEvent(self, QMouseEvent):
        if self.getScrollArea().isCurrentIndex(self.index):
            Button.mouseReleaseEvent(self, QMouseEvent)
        else:
            self.enterEvent(QMouseEvent)
        
class LineBox(QLineEdit): #Add clear button
    class _Message(ButtonText):
        def __init__(self, message, lineBox):
            super().__init__(message, "message")
            self.setAlignment(Qt.AlignLeft)
            self.setToolTip("")
            s = Style(self.styleSheet())
            s.setAttribute("color", "gray" if lineBox.msgIn else "black")
            self.setStyleSheet(s.css())
            if lineBox.msgIn:
                self.setCursor(lineBox.cursor())
            self.lineBox = lineBox
        
        def __getParent(self):
            p = self.lineBox.parent()
            while not isinstance(p, QWidget):
                p = p.parent()
            return p
            
        def mouseLeftReleased(self, QMouseEvent):
            if self.lineBox.msgIn:
                self.lineBox.setFocus()
            else:
                self.__getParent().mouseReleaseEvent(QMouseEvent)
        
    def __init__(self, defaultText = "", message = "", msgIn = True):
        self.entered = False
        self.startPosition = None
        super().__init__()
        self.msgIn = msgIn
        self.setMessage(message)
        if self.checkMessage():
            self.setObjectName("linebox" if message.strip() == "" else message)
        else:
            self.setObjectName("linebox")
        s = Style()
        s.setWidget("QLineEdit")
        s.setAttribute("border", "1px solid black")
        s.setAttribute("selection-background-color", "black")
        self.setStyleSheet(s.css())
        self.textChanged.connect(self.changeText)
        self.setText(defaultText)
              
    def setFont(self, *args, **kwargs):
        QLineEdit.setFont(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFont(*args, **kwargs)
        
    def setFixedHeight(self, *args, **kwargs):
        QLineEdit.setFixedHeight(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFixedHeight(*args, **kwargs)

    def setFixedWidth(self, *args, **kwargs):
        QLineEdit.setFixedWidth(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFixedWidth(*args, **kwargs)

    def setFixedSize(self, *args, **kwargs):
        QLineEdit.setFixedSize(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFixedSize(*args, **kwargs)
            
    def setVisible(self, *args, **kwargs):
        QLineEdit.setVisible(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setVisible(*args, **kwargs)

    def changeText(self):
        t = self.text().strip()
        self.setToolTip(t)
        if self.msgIn:
            if self.checkMessage():
                self.__message.setVisible(t == "")
            
    def getMessage(self):
        return self.__message
    
    def checkMessage(self):
        return not self.__message is None
    
    def setMessage(self, message):
        if not message is None:
            if not isinstance(message, self._Message):
                message = self._Message(message, self)
        self.__message = message
        
    def layout(self):
        if self.msgIn:
            g = QGridLayout()
            g.addWidget(self, 0, 0)
            if self.checkMessage():
                g.addWidget(self.__message, 0, 0, self.__message.alignment())
            return g
        else:
            h = QHBoxLayout()
            if self.checkMessage():
                h.addWidget(self.__message)
            h.addWidget(self)
            return h
                      
    def enter(self, QMouseEvent):
        if self.isEnabled():
            self.entered = True
       
    def enterEvent(self, QMouseEvent):
        QLineEdit.enterEvent(self, QMouseEvent)
        self.enter(QMouseEvent)
                
    def leave(self, QMouseEvent):  
        if self.isEnabled():
            self.entered = False
        
    def leaveEvent(self, QMouseEvent):
        QLineEdit.leaveEvent(self, QMouseEvent)
        self.leave(QMouseEvent)
        
    def mouseMove(self, QMouseEvent):
        pass
        
    def mouseMoveEvent(self, QMouseEvent):
        QLineEdit.mouseMoveEvent(self, QMouseEvent)
        if self.isEnabled():
            self.mouseMove(QMouseEvent)
            
    def mouseRightPressed(self, QMouseEvent):
        pass
    
    def mouseMiddlePressed(self, QMouseEvent):
        pass
    
    def mouseLeftPressed(self, QMouseEvent):
        self.startPosition = QMouseEvent.pos()
        
    def mousePressed(self, QMouseEvent):       
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddlePressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed(QMouseEvent)
                
    def mousePressEvent(self, QMouseEvent):
        QLineEdit.mousePressEvent(self, QMouseEvent)
        self.mousePressed(QMouseEvent)
        
    def mouseRightReleased(self, QMouseEvent):
        pass
    
    def mouseMiddleReleased(self, QMouseEvent):
        pass
    
    def mouseLeftReleased(self, QMouseEvent):
        self.startPosition = None
        
    def mouseReleased(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddleReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased(QMouseEvent)
                
    def mouseReleaseEvent(self, QMouseEvent):
        QLineEdit.mouseReleaseEvent(self, QMouseEvent)
        self.mouseReleased(QMouseEvent)
        
class TextBox(QTextEdit):#Add clear button
    class _Message(ButtonText):
        def __init__(self, message, textBox):
            super().__init__(message, "message")
            self.setAlignment(Qt.AlignLeft)
            self.setToolTip("")
            s = Style(self.styleSheet())
            s.setAttribute("color", "gray" if textBox.msgIn else "black")
            self.setStyleSheet(s.css())
            if textBox.msgIn:
                self.setCursor(textBox.cursor())
            self.textBox = textBox
        
        def __getParent(self):
            p = self.textBox.parent()
            while not isinstance(p, QWidget):
                p = p.parent()
            return p
            
        def mouseLeftReleased(self, QMouseEvent):
            if self.textBox.msgIn:
                self.textBox.setFocus()
            else:
                self.__getParent().mouseReleaseEvent(QMouseEvent)
        
    def __init__(self, defaultText = "", message = "", msgIn = True):
        self.entered = False
        self.startPosition = None
        super().__init__(defaultText)
        self.msgIn = msgIn
        self.setMessage(message)
        if self.checkMessage():
            self.setObjectName("textbox" if message.strip() == "" else message)
        else:
            self.setObjectName("textbox")
        s = Style()
        s.setWidget("QTextEdit")
        s.setAttribute("border", "1px solid black")
        s.setAttribute("selection-background-color", "black")
        self.setStyleSheet(s.css())
        self.textChanged.connect(self.changeText)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(self.toPlainText()))
        self.setTextCursor(cursor)
        self.deselect()
              
    def setFont(self, *args, **kwargs):
        QTextEdit.setFont(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFont(*args, **kwargs)
        
    def setFixedHeight(self, *args, **kwargs):
        QTextEdit.setFixedHeight(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFixedHeight(*args, **kwargs)

    def setFixedWidth(self, *args, **kwargs):
        QTextEdit.setFixedWidth(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFixedWidth(*args, **kwargs)

    def setFixedSize(self, *args, **kwargs):
        QTextEdit.setFixedSize(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setFixedSize(*args, **kwargs)
            
    def setVisible(self, *args, **kwargs):
        QTextEdit.setVisible(self, *args, **kwargs)
        if self.checkMessage():
            self.__message.setVisible(*args, **kwargs)

    def deselect(self):
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def changeText(self):
        t = self.toPlainText().strip()
        self.setToolTip(t)
        if self.msgIn:
            if self.checkMessage():
                self.__message.setVisible(t == "")
            
    def getMessage(self):
        return self.__message
    
    def checkMessage(self):
        return not self.__message is None
    
    def setMessage(self, message):
        if not message is None:
            if not isinstance(message, self._Message):
                message = self._Message(message, self)
        self.__message = message
        
    def layout(self):
        if self.msgIn:
            g = QGridLayout()
            g.addWidget(self, 0, 0)
            if self.checkMessage():
                g.addWidget(self.__message, 0, 0, self.__message.alignment())
            return g
        else:
            h = QHBoxLayout()
            if self.checkMessage():
                h.addWidget(self.__message)
            h.addWidget(self)
            return h
      
    def enter(self, QMouseEvent):
        if self.isEnabled():
            self.entered = True
       
    def enterEvent(self, QMouseEvent):
        QTextEdit.enterEvent(self, QMouseEvent)
        self.enter(QMouseEvent)
                
    def leave(self, QMouseEvent):  
        if self.isEnabled():
            self.entered = False
        
    def leaveEvent(self, QMouseEvent):
        QTextEdit.leaveEvent(self, QMouseEvent)
        self.leave(QMouseEvent)
        
    def mouseMove(self, QMouseEvent):
        pass
        
    def mouseMoveEvent(self, QMouseEvent):
        QTextEdit.mouseMoveEvent(self, QMouseEvent)
        if self.isEnabled():
            self.mouseMove(QMouseEvent)
            
    def mouseRightPressed(self, QMouseEvent):
        pass
    
    def mouseMiddlePressed(self, QMouseEvent):
        pass
    
    def mouseLeftPressed(self, QMouseEvent):
        self.startPosition = QMouseEvent.pos()
        
    def mousePressed(self, QMouseEvent):       
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddlePressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed(QMouseEvent)
                
    def mousePressEvent(self, QMouseEvent):
        QTextEdit.mousePressEvent(self, QMouseEvent)
        self.mousePressed(QMouseEvent)
        
    def mouseRightReleased(self, QMouseEvent):
        pass
    
    def mouseMiddleReleased(self, QMouseEvent):
        pass
    
    def mouseLeftReleased(self, QMouseEvent):
        self.startPosition = None
        
    def mouseReleased(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddleReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased(QMouseEvent)
                
    def mouseReleaseEvent(self, QMouseEvent):
        QTextEdit.mouseReleaseEvent(self, QMouseEvent)
        self.mouseReleased(QMouseEvent)
          
class ChildLineBox(LineBox):
    def __init__(self, defaultText="", message="", msgIn=True):
        LineBox.__init__(self, defaultText, message, msgIn)
        self.setParentButton(None)
        self.setButton(None)
        if self.checkMessage():
            self.setObjectName("child-linebox" if message.strip() == "" else message)
        else:
            self.setObjectName("child-linebox")
        
    def checkButton(self):
        return self.__button is None
    
    def checkParentButton(self):
        return self.__parentButton is None
    
    def setParentButton(self, parentButton):
        self.__parentButton = parentButton
        
    def setButton(self, button):
        self.__button = button
        if self.checkMessage():
            self.getMessage().setButton(button)
        
    def getButton(self):
        return self.__button
    
    def getParentButton(self):
        return self.__parentButton
    
    def enterEvent(self, QMouseEvent):
        if self.checkButton():
            LineBox.enterEvent(self, QMouseEvent)
        else:
            self.__button.enterEvent(QMouseEvent)
            
    def leave(self, QMouseEvent):
        LineBox.leave(self, QMouseEvent)
        self.setButton(self.__parentButton)
        self.setParentButton(None)
        if not self.checkButton():
            self.__button.leaveEvent(QMouseEvent)
            self.__button.setFocus()
        
    def leaveEvent(self, QMouseEvent):
        if self.checkButton():
            LineBox.leaveEvent(self, QMouseEvent)
        else:
            self.__button.leaveEvent(QMouseEvent)
            self.__button.setFocus()
            
    def mouseMoveEvent(self, QMouseEvent):
        if self.checkButton():
            LineBox.mouseMoveEvent(self, QMouseEvent)
        else:
            self.__button.mouseMoveEvent(QMouseEvent)
            
    def mousePressEvent(self, QMouseEvent):
        if self.checkButton():
            LineBox.mousePressEvent(self, QMouseEvent)
        else:
            self.startPosition = QMouseEvent.pos()
            self.__button.mousePressEvent(QMouseEvent)
            self.__button.setFocus()
            
    def mouseReleaseEvent(self, QMouseEvent):
        if self.checkButton():
            LineBox.mouseReleaseEvent(self, QMouseEvent)
        else:
            s = self.startPosition
            self.__button.mouseReleaseEvent(QMouseEvent)
            if QMouseEvent.button() == Qt.LeftButton:
                if s == QMouseEvent.pos():
                    self.setFocus()
                    self.setParentButton(self.__button)
                    self.setButton(None)
            
class ChildTextBox(TextBox):
    def __init__(self, defaultText="", message="", msgIn=True):
        TextBox.__init__(self, defaultText, message, msgIn)
        self.setParentButton(None)
        self.setButton(None)
        if self.checkMessage():
            self.setObjectName("child-textbox" if message.strip() == "" else message)
        else:
            self.setObjectName("child-textbox")
        
    def checkButton(self):
        return self.__button is None
    
    def checkParentButton(self):
        return self.__parentButton is None
    
    def setParentButton(self, parentButton):
        self.__parentButton = parentButton
        
    def setButton(self, button):
        self.__button = button
        if self.checkMessage():
            self.getMessage().setButton(button)
        
    def getButton(self):
        return self.__button
    
    def getParentButton(self):
        return self.__parentButton
    
    def enterEvent(self, QMouseEvent):
        if self.checkButton():
            TextBox.enterEvent(self, QMouseEvent)
        else:
            self.__button.enterEvent(QMouseEvent)
            
    def leave(self, QMouseEvent):
        TextBox.leave(self, QMouseEvent)
        self.setButton(self.__parentButton)
        self.setParentButton(None)
        if not self.checkButton():
            self.__button.leaveEvent(QMouseEvent)
            self.__button.setFocus()
        
    def leaveEvent(self, QMouseEvent):
        if self.checkButton():
            TextBox.leaveEvent(self, QMouseEvent)
        else:
            self.__button.leaveEvent(QMouseEvent)
            self.__button.setFocus()
            
    def mouseMoveEvent(self, QMouseEvent):
        if self.checkButton():
            TextBox.mouseMoveEvent(self, QMouseEvent)
        else:
            self.__button.mouseMoveEvent(QMouseEvent)
            
    def mousePressEvent(self, QMouseEvent):
        if self.checkButton():
            TextBox.mousePressEvent(self, QMouseEvent)
        else:
            self.startPosition = QMouseEvent.pos()
            self.__button.mousePressEvent(QMouseEvent)
            self.__button.setFocus()
            
    def mouseReleaseEvent(self, QMouseEvent):
        if self.checkButton():
            TextBox.mouseReleaseEvent(self, QMouseEvent)
        else:
            s = self.startPosition
            self.__button.mouseReleaseEvent(QMouseEvent)
            if QMouseEvent.button() == Qt.LeftButton:
                if s == QMouseEvent.pos():
                    self.setFocus()
                    self.setParentButton(self.__button)
                    self.setButton(None)
            
class Encode:
    def __init__(self, text):
        self.setText(text)
        
    def setText(self, text):
        self.__text = text
        
    def text(self):
        return self.__text 

class Decode:
    def __init__(self, text):
        self.setText(text)
        
    def setText(self, text):
        self.__text = text
        
    def text(self):
        return self.__text

class Password(LineBox):
    def __init__(self, defaultText = "", message = "", encode = None):
        if not message is None:
            if message.strip() == "":
                message = "Password:"
            else:
                message += " Password:"
        self.encode = Encode if encode is None else encode
        super().__init__(defaultText, message, False)
        self.setEchoMode(LineBox.Password)
    
    def setToolTip(self, toolTip):
        pass
     
    def text(self):
        return self.encode(LineBox.text(self)).text()
        
class ChildPassword(ChildLineBox):
    def __init__(self, defaultText = "", message = "", encode = None):
        if not message is None:
            if message.strip() == "":
                message = "Password:"
            else:
                message += " Password:"
        self.encode = Encode if encode is None else encode
        super().__init__(defaultText, message, False)
        self.setEchoMode(ChildLineBox.Password)
         
    def setToolTip(self, toolTip):
        pass
     
    def text(self):
        return self.encode(ChildLineBox.text(self)).text()
     
class ArrowButton(ChildButton):
    def __init__(self):
        super().__init__()
        self.setObjectName("arrow")
        self.__start = False
        self.setComboBox(None)
        
    def setComboBox(self, combobox):
        self.__combobox = combobox
        
    def __drawArrow(self, paint):
        start = self.width() // 4
        height = self.height() // 6
        start = QPoint(start, start+height)
        mid = QPoint(start.x()*2, start.y()+start.x())
        paint.drawLine(start, mid)
        end = QPoint(start.x()*3, start.y())
        paint.drawLine(mid, end)
        return paint
             
    def paintEvent(self, QPaintEvent):
        if not self.__start:
            self.__start = True
            self.setColor(self, self.backgroundRole(), self.backgroundColor)
        p = QPainter()
        p.begin(self)
        color = self.backgroundColor if self.entered else self.hoverColor
        p.setPen(QPen(color, 2, Qt.SolidLine))
        p = self.__drawArrow(p)
        p.end()
        
    def mouseLeftReleased(self, QMouseEvent):
        s = self.startPosition
        ChildButton.mouseLeftReleased(self, QMouseEvent)
        if not self.__combobox is None:
            if s == QMouseEvent.pos():
                self.__combobox.showPopup()

class ComboBox(QComboBox):
    class _Combo(ChildButton):
        def __init__(self, comboBox):
            currentText = ButtonText(attribute="combo")
            self.arrow = None
            super().__init__(currentText)
            self.addTextToGrid("combo")
            self.setComboBox(comboBox)
            self.setArrowButton(ArrowButton())
            self.currentText = currentText
            self.start = False
        
        def paintEvent(self, QPaintEvent):
            ChildButton.paintEvent(self, QPaintEvent)
            if not self.start:
                self.start = True
                self.setColor(self, self.backgroundRole(), self.backgroundColor)
                
        def checkArrow(self):
            return not self.arrow is None
              
        def setArrowButton(self, arrow):
            if not arrow is None:
                arrow.setComboBox(self.comboBox)
                self.addChildren(arrow)
                arrow.setButton(None)
                self.arrow = arrow
                self.addChildToGrid(arrow.objectName(), Qt.AlignRight)
                
        def setComboBox(self, comboBox):
            self.comboBox = comboBox
            
        def showEvent(self, QEvent):
            if self.isVisible():
                self.setFixedHeight(self.comboBox.height())
            
        def setArrowSize(self):
            if self.checkArrow():
                h = self.height()
                self.arrow.setFixedSize(h, h)      
            
        def enterEvent(self, QMouseEvent):
            ChildButton.enterEvent(self, QMouseEvent)
            self.comboBox.enterEvent(QMouseEvent)
            
        def leaveEvent(self, QMouseEvent):
            ChildButton.leaveEvent(self, QMouseEvent)
            self.comboBox.leaveEvent(QMouseEvent)
            
        def mousePressEvent(self, QMouseEvent):
            ChildButton.mousePressEvent(self, QMouseEvent)
            self.comboBox.mousePressEvent(QMouseEvent)
            
        def mouseReleaseEvent(self, QMouseEvent):
            ChildButton.mouseReleaseEvent(self, QMouseEvent)
            self.comboBox.mouseReleaseEvent(QMouseEvent)
             
        def mouseLeftReleased(self, QMouseEvent):
            s = self.startPosition
            ChildButton.mouseLeftReleased(self, QMouseEvent)
            if s == QMouseEvent.pos():
                self.comboBox.showPopup()
                 
        def setButton(self, button):
            ChildButton.setButton(self, button)
            if self.checkArrow():
                self.arrow.setButton(button)
#             
#         def setFixedHeight(self, *args, **kwargs):
#             ChildButton.setFixedHeight(self, *args, **kwargs)
#             if not self.arrow is None:
#                 self.arrow.setFixedHeight(*args, **kwargs)
#     
#         def setFixedWidth(self, *args, **kwargs):
#             ChildButton.setFixedWidth(self, *args, **kwargs)
#             if not self.arrow is None:
#                 self.arrow.setFixedWidth(*args, **kwargs)
#     
#         def setFixedSize(self, *args, **kwargs):
#             ChildButton.setFixedSize(self, *args, **kwargs)
#             if not self.arrow is None:
#                 self.arrow.setFixedSize(*args, **kwargs)
#                 
#         def setVisible(self, *args, **kwargs):
#             ChildButton.setVisible(self, *args, **kwargs)
#             if not self.arrow is None:
#                 self.arrow.setVisible(*args, **kwargs)
#             
    def __init__(self, *items):
        self.entered = False
        self.startPosition = None
        super().__init__()
        self.setObjectName("combobox")
        s = Style()
        s.setWidget("QComboBox QAbstractItemView")
        s.setAttribute("border", "1px solid black")
        s.setAttribute("background-color", "white")
        s.setAttribute("selection-background-color", "black")
        self.setStyleSheet(s.css())
        self.addItems(items)
        self.__combo = self._Combo(self)
        self.currentTextChanged.connect(self.textChanged)
                
    def setFont(self, *args, **kwargs):
        QComboBox.setFont(self, *args, **kwargs)
        self.__combo.setFont(*args, **kwargs)
        
    def setFixedHeight(self, *args, **kwargs):
        QComboBox.setFixedHeight(self, *args, **kwargs)
        self.__combo.setFixedHeight(*args, **kwargs)

    def setFixedWidth(self, *args, **kwargs):
        QComboBox.setFixedWidth(self, *args, **kwargs)
        self.__combo.setFixedWidth(*args, **kwargs)

    def setFixedSize(self, *args, **kwargs):
        QComboBox.setFixedSize(self, *args, **kwargs)
        self.__combo.setFixedSize(*args, **kwargs)
            
    def setVisible(self, *args, **kwargs):
        QComboBox.setVisible(self, *args, **kwargs)
        self.__combo.setVisible(*args, **kwargs)
        
    def textChanged(self):
        self.__combo.currentText.setText(" "+self.currentText())
        
    def setArrowButton(self, arrow):
        self.__combo.setArrowButton(arrow)
        
    def getCombo(self):
        return self.__combo
        
    def showEvent(self, QEvent):
        if self.isVisible():
            self.__combo.setArrowSize()
        
    def layout(self):
        g = QGridLayout()
        g.addWidget(self, 0, 0)
        g.addLayout(self.__combo.layout(), 0, 0)
        return g
               
    def enter(self, QMouseEvent):
        if self.isEnabled():
            self.entered = True
       
    def enterEvent(self, QMouseEvent):
        QComboBox.enterEvent(self, QMouseEvent)
        self.enter(QMouseEvent)
                
    def leave(self, QMouseEvent):  
        if self.isEnabled():
            self.entered = False
        
    def leaveEvent(self, QMouseEvent):
        QComboBox.leaveEvent(self, QMouseEvent)
        self.leave(QMouseEvent)
        
    def mouseMove(self, QMouseEvent):
        pass
        
    def mouseMoveEvent(self, QMouseEvent):
        QComboBox.mouseMoveEvent(self, QMouseEvent)
        if self.isEnabled():
            self.mouseMove(QMouseEvent)
            
    def mouseRightPressed(self, QMouseEvent):
        pass
    
    def mouseMiddlePressed(self, QMouseEvent):
        pass
    
    def mouseLeftPressed(self, QMouseEvent):
        self.startPosition = QMouseEvent.pos()
        
    def mousePressed(self, QMouseEvent):       
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddlePressed(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed(QMouseEvent)
                
    def mousePressEvent(self, QMouseEvent):
        s = self.startPosition
        if s == QMouseEvent.pos():
            QComboBox.mousePressEvent(self, QMouseEvent)
            self.mousePressed(QMouseEvent)
        
    def mouseRightReleased(self, QMouseEvent):
        pass
    
    def mouseMiddleReleased(self, QMouseEvent):
        pass
    
    def mouseLeftReleased(self, QMouseEvent):
        self.startPosition = None

    def mouseReleased(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.MiddleButton:
                self.mouseMiddleReleased(QMouseEvent)
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased(QMouseEvent)
                
    def mouseReleaseEvent(self, QMouseEvent):
        QComboBox.mouseReleaseEvent(self, QMouseEvent)
        self.mouseReleased(QMouseEvent)
        
class ChildComboBox(ComboBox):
    def __init__(self, *items):
        ComboBox.__init__(self, *items)
        self.setParentButton(None)
        self.setButton(None)
        self.setObjectName("child-combobox")
                
    def checkButton(self):
        return self.__button is None
    
    def checkParentButton(self):
        return self.__parentButton is None
    
    def setParentButton(self, parentButton):
        self.__parentButton = parentButton
        
    def setButton(self, button):
        self.__button = button
        self.getCombo().setButton(button)
        
    def getButton(self):
        return self.__button
    
    def getParentButton(self):
        return self.__parentButton
    
    def enterEvent(self, QMouseEvent):
        if self.checkButton():
            ComboBox.enterEvent(self, QMouseEvent)
        else:
            self.__button.enterEvent(QMouseEvent)
#             
#     def leave(self, QMouseEvent):
#         ComboBox.leave(self, QMouseEvent)
#         self.setButton(self.__parentButton)
#         self.setParentButton(None)
#         if not self.checkButton():
#             self.__button.leaveEvent(QMouseEvent)
#             self.__button.setFocus()
#         
    def leaveEvent(self, QMouseEvent):
        if self.checkButton():
            ComboBox.leaveEvent(self, QMouseEvent)
        else:
            self.__button.leaveEvent(QMouseEvent)
           # self.__button.setFocus()
            
    def mouseMoveEvent(self, QMouseEvent):
        if self.checkButton():
            ComboBox.mouseMoveEvent(self, QMouseEvent)
        else:
            self.__button.mouseMoveEvent(QMouseEvent)
            
    def mousePressEvent(self, QMouseEvent):
        if self.checkButton():
            ComboBox.mousePressEvent(self, QMouseEvent)
        else:
            self.startPosition = QMouseEvent.pos()
            self.__button.mousePressEvent(QMouseEvent)
            
    def mouseReleaseEvent(self, QMouseEvent):
        if self.checkButton():
            ComboBox.mouseReleaseEvent(self, QMouseEvent)
        else:
            s = self.startPosition
            self.__button.mouseReleaseEvent(QMouseEvent)
            if QMouseEvent.button() == Qt.LeftButton:
                if s == QMouseEvent.pos():
                    self.setFocus()
                    self.setParentButton(self.__button)
                    self.setButton(None)
                    ComboBox.mousePressEvent(self, QMouseEvent)
           
class CheckIndicator(ChildButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 16)
        self.setObjectName("indicator")
        self.clickColor = None
        self.__hover = self.hoverColor
        self.hoverColor = None
        self.__checked = False
      
    def __drawIndicator(self, paint):
        start = QPoint(3, 9)
        mid = QPoint(6, 12)
        end = QPoint(13, 5)
        paint.drawLine(start, mid)
        paint.drawLine(mid, end)
        return paint
             
    def paintEvent(self, QPaintEvent):
        p = QPainter()
        p.begin(self)
        color = self.__hover if self.__checked else self.backgroundColor
        p.setPen(QPen(color, 2, Qt.SolidLine))
        p = self.__drawIndicator(p)
        p.end()
        
    def isChecked(self):
        return self.__checked
        
    def mouseLeftReleased(self, QMouseEvent):
        ChildButton.mouseLeftReleased(self, QMouseEvent)
        self.__checked = not self.__checked
        
class CheckBox(Button):
    class _Text(ButtonText):
        def __init__(self, text):
            super().__init__(text)
            self.textHoverColor = None
            self.setToolTip("")
       
    def __init__(self, text = "checkbox"):
        super().__init__(self._Text(text))
        border = self.getText("border")["border"]
        s = Style(border.styleSheet())
        s.setAttribute("border", "1px solid white")
        border.setStyleSheet(s.css())
        self.addText(border)
        self.addTextToGrid("border")
        self.addTextToGrid("text", Qt.AlignRight)
        self.setObjectName(text)
        self.setCheckIndicator()
        self.hoverColor = None
        self.clickColor = None
        self.__start = True
        
    def setCheckIndicator(self, indicator = None):
        if indicator is None:
            indicator = CheckIndicator()
        self.indicator = indicator
        self.addChildren(indicator)
        self.addChildToGrid(indicator.objectName(), Qt.AlignLeft)
        
    def showEvent(self, QEvent):
        if self.__start:
            if self.isVisible():
                self.setFixedWidth(self.width()+self.indicator.width())
                self.__start = False
        
    def mouseLeftReleased(self, QMouseEvent):
        Button.mouseLeftReleased(self, QMouseEvent)
        self.indicator.mouseLeftReleased(QMouseEvent)
         
    def isChecked(self):
        return self.indicator.isChecked()
    
class MessageBox(ChildWindow):
    QUESTION_ICON = "question_icon"
    INFORMATION_ICON = "information_icon"
    WARNING_ICON = "warning_icon"
    CRITICAL_ICON = "critical_icon"
    
    OK_BUTTON = "ok_button"
    CANCEL_BUTTON = "cancel_button"
    CLOSE_BUTTON = "close_button"
    OK_CANCEL_BUTTONS = "ok_cancel_buttons"
    YES_BUTTON = "yes_button"
    NO_BUTTON = "no_button"
    YES_NO_BUTTONS = "yes_no_buttons"
            
    class _Icon(ChildButton):
        def __init__(self, icon, backgroundColor):
            self.icon = icon
            super().__init__()
            self.backgroundColor = backgroundColor
            self.clickColor = None
            self.hoverColor = None
            self.setObjectName(icon)
            s = 50
            self.setFixedSize(s, s)
            border = self.getText("border")["border"]
            s = Style(border.styleSheet())
            s.setAttribute("border", "1px solid white")
            border.setStyleSheet(s.css())
            self.addText(border)
            self.addTextToGrid("border")
            
        def __color(self, color):
            b = self.backgroundColor
            return color if b is None else b
          
        def __drawIcon(self, paint):
            def circle(color):
                paint.setPen(QPen(Qt.white, 1, Qt.SolidLine))
                paint.setBrush(self.__color(color))
                paint.drawEllipse(0, 0, w, h)
                
            w, h = (self.width()-2, self.height()-2)
            paint.setFont(QFont("Times New Roman", 25))
            if self.icon == MessageBox.QUESTION_ICON or self.icon == MessageBox.INFORMATION_ICON:
                circle(Qt.black)
                paint.setPen(QPen(Qt.white, 2, Qt.SolidLine))
                if self.icon == MessageBox.QUESTION_ICON:
                    paint.drawText(QPoint((w//2)-8, h-10), "?")
                else:
                    paint.drawText(QPoint((w//2)-6, h-10), "i")
            elif self.icon == MessageBox.WARNING_ICON:
                top = QPoint(w // 2, 2)
                bleft = QPoint(2, h)
                bright = QPoint(w, h)
                paint.setPen(QPen(Qt.black, 2, Qt.SolidLine))
                paint.setBrush(self.__color(Qt.yellow))
                paint.drawPolygon(QPolygon([top, bleft, bright]))
                paint.drawText(QPoint(top.x()-7, h-6), "!")
            elif self.icon == MessageBox.CRITICAL_ICON:
                circle(Qt.red)
                n = w // 3
                w, h = (w-n, h-n)
                paint.setPen(QPen(Qt.white, 4, Qt.SolidLine))
                paint.drawLine(n, n, w, h)
                paint.drawLine(w, n, n, h)
            else:
                if not self.icon == "":
                    self.icon = ""
            return paint
                 
        def paintEvent(self, QPaintEvent):
            p = QPainter()
            p.begin(self)
            p = self.__drawIcon(p)
            p.end()
            
    class _Button(Button):
        def __init__(self, name, msg):
            super().__init__(ButtonText(name, name))
            self.setObjectName(name)
            self.addTextToGrid(name)
            self.msg = msg
            
        def showEvent(self, QEvent):
            if self.isVisible():
                self.setFixedSize(self.width()+5, self.height()+5)
                 
        def mouseLeftReleased(self, QMouseEvent):
            Button.mouseLeftReleased(self, QMouseEvent)
            msg = self.msg
            msg.setButtonClicked(self.objectName())
            msg.hide()
    
    def __init__(self, message = "Enter your message here", icon = "", iconBackground = None, buttonLayout = OK_BUTTON):
        self.setMessage(message)
        self.setIcon(icon, iconBackground)
        self.setButtonLayouts(buttonLayout)
        self.setButtonClicked(None)
        super().__init__(flags=Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        
    def __getButtonNames(self, name = ""):
        md = vars(MessageBox)
        buttons = {}
        for b in list(md.keys()).copy():
            if "BUTTON" in b:
                buttons[md[b]] = [n.lower().capitalize() for n in b[:b.rfind('_')].split('_')]
        return buttons[name] if name in buttons else buttons
        
    def setMessage(self, message):
        self.__message = message
        return self
    
    def getMessage(self):
        return self.__message
        
    def setIcon(self, icon, backgroundColor = None):
        self.__icon = self._Icon(icon, backgroundColor) if type(icon) is str else icon
        return self
    
    def getIcon(self):
        return self.__icon
        
    def setButtonLayouts(self, *buttonLayouts):
        self.__buttonLayouts = list(buttonLayouts)
        buttons = []
        for b in buttonLayouts:
            buttons += self.__getButtonNames(b)
        return self.setButtons(*buttons)
    
    def addButtonLayouts(self, *buttonLayouts):
        self.__buttonLayouts += list(buttonLayouts)
        buttons = []
        for b in buttonLayouts:
            buttons += self.__getButtonNames(b)
        return self.addButtons(*buttons)
    
    def removeButtonLayouts(self, *buttonLayouts):
        for b in buttonLayouts:
            if b in self.__buttonLayouts:
                self.__buttonLayouts.remove(b)
        return self.setButtonLayouts(*self.__buttonLayouts)
    
    def getButtonLayouts(self):
        return self.__buttonLayouts
    
    def setButtons(self, *buttons):
        self.__buttons = {}
        return self.addButtons(*buttons)
    
    def addButtons(self, *buttons):
        for name in buttons:
            self.__buttons[name] = self._Button(name, self)
        return self
    
    def removeButtons(self, *buttons):
        for b in buttons:
            if b in self.__buttons:
                self.__buttons.pop(b)
        return self
    
    def getButtons(self):
        return self.__buttons
    
    def closeEvent(self, QEvent):
        self.setButtonClicked("Close")
        self.hide()
        
    def setButtonClicked(self, buttonClicked):
        self.__buttonClicked = buttonClicked
    
    def isButtonClicked(self, button):
        return self.__buttonClicked == button
    
    def getButtonClicked(self):
        return self.__buttonClicked    
    
    def setupWindow(self):
        ChildWindow.setupWindow(self)
        self.setWindowTitle("Message")
        f = Form(self)
        f.setFont(self.getFont())
        i = self.__icon
        if "icon" in i.__dict__:
            if not i.icon == "":
                f.addButton(i)
        else:
            f.addButton(i)
        mes = self.__message
        if type(mes) is str:
            f.addLabel(mes).addRow()
        else:
            m, mes = (mes[0], mes[1:])
            if type(m) is str:
                f.addLabel(m)
            else:
                f.addButtonText(buttonText=m)
            f.addRow()
            for m in mes:
                if type(m) is str:
                    m = ButtonText(m)
                    m.setAlignment(Qt.AlignLeft)
                if isinstance(m, ButtonText):
                    space = ButtonText(attribute="space")
                    space.setFixedWidth(i.width()+2)
                    f.addButtonText(buttonText=space)
                    f.addButtonText(buttonText=m).addRow()
        for b in tuple(self.getButtons().values()):
            f.addButton(b)
        f.addRow(Qt.AlignCenter)
        f.layout()
        
class Group(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("group")
        self.setForm(None)
        self.setStyleSheet("border:0")
        
    def setForm(self, form):
        self.__form = form
        return self
        
    def getForm(self):
        return self.__form
    
    def checkForm(self):
        return self.__form is None
        
    def searchObjects(self, searchForm = None):
        if self.checkForm():
            return None
        return self.__form.searchObjects(searchForm)
    
    def setWaitScreenVisible(self, isWaitVisible):
        if self.checkForm():
            return self
        return self.__form.setWaitScreenVisible(isWaitVisible)
        
    def isWaitScreenVisible(self):
        if self.checkForm():
            return False
        return self.__form.isWaitScreenVisible()
    
    def loadChunk(self):
        if not self.checkForm():
            self.__form.loadChunk()
        return self
           
    def getRowsPerChunk(self):
        if self.checkForm():
            return 0
        return self.__form.getRowsPerChunk()
           
    def getRowCount(self):
        if self.checkForm():
            return 0
        return self.__form.getRowCount()
           
    def __getParent(self):
        p = self.parent()
        while not isinstance(p, QWidget):
            p = p.parent()
        return p
        
    def mouseReleaseEvent(self, QMouseEvent):
        self.__getParent().mouseReleaseEvent(QMouseEvent)
        
class FormLayout(QFormLayout):
    def __init__(self, parent = None):
        self.setForm()
        self.__isVisible = True
        self.__isEnabled = True
        super().__init__(parent)
        
    def setForm(self, form = None):
        self.__form = form
        return self
        
    def getForm(self):
        return self.__form
    
    def checkForm(self):
        return self.__form is None
    
    def searchObjects(self, searchForm = None):
        if self.checkForm():
            return None
        return self.__form.searchObjects(searchForm)
    
    def clear(self):
        self.__clearLayout(self)
        return self
        
    def isVisible(self):
        return self.__isVisible
    
    def isEnabled(self):
        return self.__isEnabled
    
    def __clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if not child.widget() is None:
                    child.widget().deleteLater()
                elif not child.layout() is None:
                    self.__clearLayout(child.layout())
                    
    def __setLayoutVisibility(self, layout, isVisible):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if not child.widget() is None:
                    child.widget().setVisible(isVisible)
                elif not child.layout() is None:
                    self.__setLayoutVisibility(child.layout(), isVisible)            
                            
    def setVisible(self, isVisible):
        self.__setLayoutVisibility(self, isVisible)
        self.__isVisible = isVisible
        return self
                           
    def __setLayoutEnabled(self, layout, isEnabled):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if not child.widget() is None:
                    child.widget().setEnabled(isEnabled)
                elif not child.layout() is None:
                    self.__setLayoutEnabled(child.layout(), isEnabled)            
                            
    def setEnabled(self, isEnabled):
        self.__setLayoutEnabled(self, isEnabled)
        self.__isEnabled = isEnabled
        return self
        
    def setWaitScreenVisible(self, isWaitVisible):
        if self.checkForm():
            return self
        return self.__form.setWaitScreenVisible(isWaitVisible)
        
    def isWaitScreenVisible(self):
        if self.checkForm():
            return False
        return self.__form.isWaitScreenVisible()
    
    def loadChunk(self):
        if not self.checkForm():
            self.__form.loadChunk()
        return self
    
    def getRowsPerChunk(self):
        if self.checkForm():
            return 0
        return self.__form.getRowsPerChunk()
           
    def getRowCount(self):
        if self.checkForm():
            return 0
        return self.__form.getRowCount()
           
    def timerEvent(self, QTimerEvent):
        if self.isWaitScreenVisible():
            self.setWaitScreenVisible(False)
            self.killTimer(0)
           
class FormGridLayout(QGridLayout):
    def __init__(self, *args, **kwargs):
        self.setForm()
        QGridLayout.__init__(self, *args, **kwargs)
                
    def setForm(self, form = None):
        self.__form = form
        return self
        
    def getForm(self):
        return self.__form
    
    def checkForm(self):
        return self.__form is None
    
    def searchObjects(self, searchForm = None):
        if self.checkForm():
            return None
        return self.__form.searchObjects(searchForm)        
    
    def clear(self):
        if not self.checkForm():
            self.__form.clearForm()
        return self
        
    def isVisible(self):
        if self.checkForm():
            return False
        return self.__form.isVisible()
    
    def isEnabled(self):
        if self.checkForm():
            return False
        return self.__form.isEnabled()
                              
    def setVisible(self, isVisible):
        if not self.checkForm():
            self.__form.setVisible(isVisible)
        return self
                                  
    def setEnabled(self, isEnabled):
        if not self.checkForm():
            self.__form.setEnabled(isEnabled)
        return self
        
    def setWaitScreenVisible(self, isWaitVisible):
        if not self.checkForm():
            self.__form.setWaitScreenVisible(isWaitVisible)
        return self
        
    def isWaitScreenVisible(self):
        if self.checkForm():
            return False
        return self.__form.isWaitScreenVisible()
    
    def loadChunk(self):
        if not self.checkForm():
            self.__form.loadChunk()
        return self
    
    def getRowsPerChunk(self):
        if self.checkForm():
            return 0
        return self.__form.getRowsPerChunk()
    
    def getRowCount(self):
        if self.checkForm():
            return 0
        return self.__form.getRowCount()
           
class WaitIcon(ChildButton):
    def __init__(self, degree = 45):
        self.__center = None
        self.__totalCircles = 0
        self.__radius = 0
        self.setDegree(degree)
        self.__currentIndex = 0
        super().__init__()
        self.setObjectName("wait")
        self.__currentColor = self.clickColor
        self.__defaultColor = self.hoverColor
        self.clickColor = None
        self.hoverColor = None
        self.__start = True
        self.startTimer(150, Qt.PreciseTimer)
        self.installEventFilter(self)
        border = self.getText("border")["border"]
        s = Style(border.styleSheet())
        s.setAttribute("border", "1px solid white")
        border.setStyleSheet(s.css())
        self.addText(border)
        self.addTextToGrid("border")
        
    def setDegree(self, degree):
        self.__degree = degree
        self.__totalCircles = 360//degree
        positions = [n for n in range(self.__totalCircles)]
        positions = list(reversed(positions))
        n = -3
        positions = positions[n:] + positions[:n]
        self.__positions = positions
        
    def __isCurrentIndex(self, index):
        return self.__currentIndex == index
        
    def __paintCircle(self, paint, index):
        color = self.__currentColor if self.__isCurrentIndex(index) else self.__defaultColor
        paint.setPen(QPen(color, 2, Qt.SolidLine))
        paint.setBrush(color)
        degree = self.__positions[index]*self.__degree
        theta = (math.pi * degree) / 180
        x = self.__center.x() + self.__radius * math.cos(theta)
        y = self.__center.y() - self.__radius * math.sin(theta)
        size = 10
        paint.drawEllipse(x, y, size, size)
        return paint
     
    def __setCenter(self):
        radius = self.height()//2
        self.__center = QPoint(radius-(radius//6), radius-4)
        self.__radius = radius-14
       
    def paintEvent(self, QPaintEvent):
        if self.isVisible():
            p = QPainter()
            p.setFont(self.font())
            p.begin(self)
            for n in range(self.__totalCircles):
                p = self.__paintCircle(p, n)
            p.end()
            self.update()
        
    def timerEvent(self, QTimerEvent):
        if self.isVisible():
            self.__currentIndex = 0 if self.__currentIndex == self.__totalCircles-1 else self.__currentIndex + 1
         
    def eventFilter(self, QObject, QEvent):
        if self.isVisible():
            if self.__start:
                self.__start = False
                self.setFixedHeight(70)
                self.setFixedWidth(self.height())
                self.__setCenter()
        return ChildButton.eventFilter(self, QObject, QEvent)
         
class WaitScreen(Button):
    def __init__(self, message):
        waitMessage = ButtonText(message, "text")
        waitMessage.setToolTip("")
        waitMessage.textHoverColor = None
        self.__start = True
        self.setForm(None)
        Button.__init__(self, waitMessage)
        border = self.getText("border")["border"]
        s = Style(border.styleSheet())
        s.setAttribute("border", "1px solid white")
        border.setStyleSheet(s.css())
        self.addText(border)
        self.addTextToGrid("border")
        self.addChildren(WaitIcon())
        boxLayout = BoxLayout(Qt.Horizontal, "text", "wait")
        self.addBoxLayoutToGrid(boxLayout, Qt.AlignCenter)
        self.clickColor = None
        self.hoverColor = None
        self.installEventFilter(self)
        
    def setForm(self, form):
        self.__form = form
        
    def eventFilter(self, QObject, QEvent):
        if self.isVisible():
            if self.__start:
                self.leave(QMouseEvent)
                self.__start = False
            if not self.__form is None:
                parent = self.__form.getParent()
                if not parent is None:
                    self.setFixedHeight(parent.height())
        return Button.eventFilter(self, QObject, QEvent)
    
class Form:
    def __init__(self, parent = None):
        self.setParent(parent)
        self.tablelize(False)
        self.mapCustomResults(False)
        self.__layout = None
        self.__gridLayout = None
        self.__currentRow = None
        self.setAddingItems(False)
        self.clearForm()
        self.newRow()
        self.setFont(None)
        self.searchResults(None)
        self.__merged = False
        self.setColumnSize(None)
        self.__rowsAligned = {}
        self.setFormLayout().setFormArguments()
        self.setWaitScreen()
        self.setRowsPerChunk().__addNewChunk(False)
        
    def setFormLayout(self, formLayout = FormLayout):
        self.__formLayout = formLayout
        return self
        
    def setFormArguments(self, *args):
        self.__args = list(args)
        return self
        
    def setVisible(self, isVisible):
        if not self.__form is None:
            for r in self.__form:
                row = self.__form[r]
                for name in row:
                    obj = row[name]
                    obj.setVisible(isVisible)
        
    def setEnabled(self, isEnabled):
        if not self.__form is None:
            for r in self.__form:
                row = self.__form[r]
                for name in row:
                    obj = row[name]
                    obj.setVisible(isEnabled)
                    
    def isVisible(self):
        if self.__form is None:
            return False
        return self.__layout.isVisible()
                  
    def isEnabled(self):
        if self.__form is None:
            return False
        return self.__layout.isEnabled()
        
    def tablelize(self, tablelize):
        self.__tablelize = tablelize
        return self
    
    def setColumnSize(self, columnSize):
        self.__columnSize = columnSize
        return self
        
    def checkColumnSize(self):
        if self.__columnSize is None:
            return False
        if self.__columnSize < 0:
            return False
        return len(self.__row) == self.__columnSize
        
    def setParent(self, parent = None):
        self.__parent = parent
        return self
    
    def getParent(self):
        return self.__parent
    
    def __clearLayout(self):
        self.__formRows = {}
        self.__setStartRow(0)
        if not self.__layout is None:
            self.__layout.clear()
        if not self.__currentRow is None:
            self.__currentRow = None
        
    def clearForm(self):
        self.__form = {}
        self.__clearFilteredForm()
        self.__start = True
        self.__clearLayout()
        return self
        
    def newRow(self):
        self.__row = {}
        return self
    
    def setRow(self, row):
        self.__row = row
        return self
    
    def setAddingItems(self, isAdding):
        self.__isAdding = isAdding
        return self
    
    def isAddingItems(self):
        return self.__isAdding
    
    def searchResults(self, results):
        self.results = results
        return self
    
    def setFont(self, font):
        self.__font = font
        return self
    
    def getFont(self, size = 10):
        font = QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(size)
        font.setBold(True)
        font.setWeight(75)
        return font
    
    def __checkName(self, obj, check):
        if isinstance(obj, BoxLayout):
            name = obj.getAttribute()
        else:
            name = obj.objectName()
        if check in name:
            name = [n for n in reversed(self.__row.keys()) if not re.search("^"+check+"\d*$", n) is None]
            if not name == []:
                name = name[0]
                s = re.search(check+"(\d*)", name)
                name = check
                i = s.group(1)
                if i == "":
                    name += "1"
                else:
                    name += str(int(i)+1)
                if isinstance(obj, BoxLayout):
                    obj.setAttribute(name)
                else:
                    obj.setObjectName(name)  
        return obj 
            
    def __add(self, obj, font, *check):
        for c in check:
            obj = self.__checkName(obj, c)
        name = obj.getAttribute() if isinstance(obj, BoxLayout) else obj.objectName()
        if font is None:
            font = self.__font
        if not font is None:
            if obj.font() == QLabel().font():
                obj.setFont(font)
        if self.isAddingItems():
            if self.__currentRow is None:
                if self.__start:
                    self.__start = False
                    self.addCurrentRow()
        self.__row[name] = obj
        if not self.__currentRow is None:
            if not self.__stopLoading(self.newFormRow()):
                self.__currentRow.addItems(obj)
        if self.checkColumnSize():
            self.addRow()
        return self
        
    def addLabel(self, name = "", font = None, label = None):  
        if label is None:
            label = QLabel(name)
            label.setObjectName("label" if name.strip() == "" else name)
        return self.__add(label, font, "label")  
    
    def addButtonText(self, text = "", attribute = "", border = None, font = None, buttonText = None):
        if buttonText is None:
            buttonText = ButtonText(text, attribute, border)
        return self.__add(buttonText, font, "text")
    
    def addButton(self, button, font = None):
        but = {ChildButton: "child-button", ScrollButton: "scroll-button", ArrowButton: "arrow", Button: "button"}
        for b in but:
            if isinstance(button, b):
                return self.__add(button, font, but[b])
        return self
    
    def addBoxLayout(self, boxLayout, font = None):
        return self.__add(boxLayout, font, "vlayout", "hlayout")
    
    def addLineBox(self, defaultText = "", message = "", msgIn = True, font = None, lineBox = None): 
        if lineBox is None:
            lineBox = LineBox(defaultText, message, msgIn)
        return self.__add(lineBox, font, "linebox")  
    
    def addTextBox(self, defaultText = "", message = "", msgIn = True, font = None, textBox = None): 
        if textBox is None:
            textBox = TextBox(defaultText, message, msgIn)
        return self.__add(textBox, font, "textbox")  
    
    def addPassword(self, defaultText = "", message = "", font = None, password = None):
        if password is None:
            password = Password(defaultText, message)
        return self.__add(password, font, "password")
    
    def addComboBox(self, comboBox, font = None):
        return self.__add(comboBox, font, "combobox")
    
    def addCheckBox(self, text = "", font = None, checkbox = None):
        if checkbox is None:
            checkbox = CheckBox(text)
        return self.__add(checkbox, font, "checkbox")
    
    def addGroup(self, group, font = None):
        return self.__add(group, font, "group")
    
    def addScrollArea(self, scrollArea):
        return self.__add(scrollArea, None, "scroll-area")
    
    def addObject(self, obj, font = None):
        if isinstance(obj, QScrollArea):
            return self.addScrollArea(obj)
        elif isinstance(obj, Group):
            return self.addGroup(obj, font)
        elif isinstance(obj, CheckBox) or isinstance(obj, QCheckBox):
            return self.addCheckBox(font = font, checkbox = obj)
        elif isinstance(obj, QComboBox):
            return self.addComboBox(obj, font)
        elif isinstance(obj, Password):
            return self.addPassword(font = font, password = obj)
        elif isinstance(obj, LineBox):
            return self.addLineBox(font = font, lineBox = obj)
        elif isinstance(obj, TextBox):
            return self.addTextBox(font = font, textBox = obj)
        elif isinstance(obj, BoxLayout):
            return self.addBoxLayout(obj, font)
        elif isinstance(obj, Button):
            return self.addButton(obj, font)
        elif isinstance(obj, ButtonText):
            return self.addButtonText(font = font, buttonText = obj)
        elif isinstance(obj, QLabel):
            return self.addLabel(font = font, label = obj)
        else:
            print("This object doesn't exist.")
            return self
    
    def removeObject(self, name):
        if name in self.__row:
            r = self.__row.pop(name)
            if not self.__currentRow is None:
                self.__currentRow.removeItems(r)
            return r
        return None
    
    def formSize(self):
        return len(self.__form)
    
    def newFormRow(self):
        return self.formSize()+1
    
    def addCurrentRow(self, row = None, alignment = None, font = None):
        if row is None:
            row = self.newFormRow()
        if self.__stopLoading(row):
            if not self.__currentRow is None:
                self.__currentRow = None
        else:
            self.__currentRow = BoxLayout(Qt.Horizontal)
            self.__currentRow.setAttribute(str(row))
            self.__currentRow.setFont(self.__font if font is None else font)
            if not alignment is None:
                self.__currentRow.setAlignment(alignment)
            self.__layout.addRow(self.__currentRow.layout())
            self.__formRows[row] = self.__currentRow
        return self
    
    def setCurrentRow(self, row):
        if row in self.__formRows:
            self.__currentRow = self.__formRows[row]
        return self
        
    def isCurrentRowVisible(self):
        if self.__currentRow is None:
            return False
        return self.__currentRow.isVisible()
    
    def currentRowSize(self):
        if self.__currentRow is None:
            return 0
        return self.__currentRow.size()
    
    def __filteredSize(self):
        return len(self.__filteredForm)
    
    def loadChunk(self):
        startRow = self.__startFilteredRow if self.__filterOn else self.__startRow 
        start = startRow-1
        size = self.__filteredSize() if self.__filterOn else self.formSize()
        if start < size and start > -1:
            self.__addNewChunk(True)
            f = self.__filteredForm if self.__filterOn else self.__form
            unloadedRows = list(f.keys())[start:]
            for row in unloadedRows:
                if self.__stopLoading(row):
                    break
                else:
                    self.addCurrentRow(row)
                    for name in f[row]:
                        self.__currentRow.addItems(f[row][name])
            if len(unloadedRows) <= self.__chunkSize:
                if self.__filterOn:
                    self.__setFilteredStartRow(row+1)
                else:
                    self.__setStartRow(row+1)
            self.__addNewChunk(False)
        return self
        
    def addRow(self, alignment = None, font = None):
        row = self.newFormRow()
        if not font is None:
            for name in self.__row:
                self.__row[name].setFont(font)
        if not alignment is None:
            self.__rowsAligned[row] = alignment
        if not self.__layout is None:
            if self.checkColumnSize():
                self.addCurrentRow(row, alignment, font)
        self.__form[row] = self.__row
        return self.newRow()
    
    def removeRow(self, rowNumber = None):
        if rowNumber is None:
            rowNumber = len(self.__form)
        if rowNumber in self.__form:
            r = self.__form.pop(rowNumber)
            self.__formRows.pop(rowNumber)
            nums = [(n-1, n) for n in self.__form if n > rowNumber]
            if len(nums) > 0:
                for (newKey, key) in nums:
                    self.__form[newKey] = self.__form.pop(key)
                    self.__formRows[newKey] = self.__formRows.pop(key)
            if not self.__layout is None:
                self.__layout.removeRow(rowNumber-1)
            return r
        return None
    
    def __searchRow(self, searchForm, row):
        if self.checkRowsPerChunk():
            if searchForm.isVisible():
                if row >= self.__startRow:
                    return False
        searchForm.search(row, self.__form[row])
        return True
    
    def searchObjects(self, searchForm = None):
        if searchForm is None:
            results = self.__form
        else:
            if searchForm.searchAllRows():
                for r in self.__form:
                    if not self.__searchRow(searchForm, r):
                        break
            else:
                for r in searchForm.rows:
                    if r in self.__form:
                        if not self.__searchRow(searchForm, r):
                            break
                    else:
                        print("Row {} does not exist".format(r))
            results = searchForm.results
            searchForm.__init__()
        return self.searchResults(results)
    
    def __clearFilteredForm(self):
        self.__filteredForm = {}
        self.__setFilteredStartRow(0)
        self.isFilterOn(False)
        return self
    
    def isFilterOn(self, filterOn):
        self.__filterOn = filterOn
        return self
    
    #searches and displays filtered rows and objects
    def filter(self, searchForm = None):
        self.__clearLayout()
        if searchForm is None:
            self.__clearFilteredForm()
            self.loadChunk()
        else:
            self.searchObjects(searchForm)
            self.__filteredForm = {**self.results}
            self.isFilterOn(True)
            r = 1
            for i in self.__filteredForm:
                self.__filteredForm[r] = self.__filteredForm.pop(i)
                r += 1
            self.__setFilteredStartRow()
            if len(self.__filteredForm) > 0:
                self.__setFilteredStartRow(1)
                self.loadChunk()
    
    def mapCustomResults(self, isCustom):
        self.__mapCustom = isCustom
        return self
    
    def getCustomResults(self, obj):
        return obj
    
    def __checkObject(self, obj):
        if self.__mapCustom:
            self.mapCustomResults(False)
            return self.getCustomResults(obj)
        else:
            if isinstance(obj, CheckBox) or isinstance(obj, QCheckBox):
                return obj.isChecked()
            if isinstance(obj, QLineEdit):
                return obj.text().strip()
            elif isinstance(obj, QTextEdit):
                return obj.toPlainText().strip()
            elif isinstance(obj, ComboBox):
                return obj.currentText().strip()
            elif isinstance(obj, Button):
                return obj.mapText()
            elif isinstance(obj, ButtonText):
                return obj.getText().strip()
            elif isinstance(obj, QLabel):
                return obj.text().strip()
            elif isinstance(obj, ScrollArea):
                return obj.getWidgetOrLayout()
            elif isinstance(obj, QScrollArea):
                return obj
            else:
                return None
    
    def resultValues(self):
        if not self.results is None:
            if self.__merged:
                for name in self.results:
                    self.results[name] = self.__checkObject(self.results[name])
            else:
                for rowNumber in self.results:
                    row = self.results[rowNumber]
                    for name in row:
                        row[name] = self.__checkObject(row[name])
                    self.results[rowNumber] = row
        return self
    
    def mergeResults(self):
        if not self.results is None:
            merge = {}
            dicts = list(self.results.values())
            for d in dicts:
                merge = {**merge, **d}
            self.results = merge
            self.__merged = True
        return self
    
    def setWaitScreen(self, message = "Please wait...", font = None, waitScreen = None):
        if waitScreen is None:
            waitScreen = WaitScreen(message)
            if font is None:
                font = self.getFont(20)
            waitScreen.setFont(font)
        waitScreen.tablelize(self.__tablelize)
        g = Group()
        g.setLayout(waitScreen.layout())
        g.setVisible(False)
        self.__waitScreen = g
        return self
    
    def setWaitScreenVisible(self, isWaitVisible):
        self.__waitScreen.setForm(self if isWaitVisible else None)
        self.__waitScreen.setVisible(isWaitVisible)
        return self
        
    def isWaitScreenVisible(self):
        return self.__waitScreen.isVisible()
    
    def getFormLayout(self):
        return self.__layout
    
    #allows dynamic scrolling functionality, loading "N" rows everytime scroll reaches max value 
    def setRowsPerChunk(self, rows = 0):
        self.__chunkSize = rows
        return self
    
    def getRowsPerChunk(self):
        return self.__chunkSize
    
    def checkRowsPerChunk(self):
        return self.__chunkSize > 0
    
    def __setStartRow(self, row = 0):
        self.__startRow = row
        return self
    
    def __setFilteredStartRow(self, row = 0):
        self.__filteredStartRow = row
        return self
    
    def getRowCount(self):
        if self.checkRowsPerChunk():
            startRow = self.__filteredStartRow if self.__filterOn else self.__startRow
            return startRow-1
        return self.formSize()
        
    def __stopLoading(self, row):
        if self.checkRowsPerChunk():
            if self.__isNewChunk:
                startRow = self.__filteredStartRow if self.__filterOn else self.__startRow
                check = row - startRow == self.__chunkSize
            else:
                check = row > self.__chunkSize
            if check:
                if self.__isNewChunk:
                    if self.__filterOn:
                        self.__setFilteredStartRow()
                    else:
                        self.__setStartRow()
                startRow = self.__filteredStartRow if self.__filterOn else self.__startRow
                if startRow < 1:
                    if self.__filterOn:
                        self.__setFilteredStartRow(row)
                    else:
                        self.__setStartRow(row)
                return True
        return False

    def __addNewChunk(self, isNewChunk):
        self.__isNewChunk = isNewChunk
        return self
    
    def __checkNewChunk(self):
        return not self.__isNewChunk
        
    def layout(self, parent = None):
        if self.__layout is None:
            if parent is None:
                parent = self.__parent
            args = [parent]
            if len(self.__args) > 0:
                args += self.__args
            form = self.__formLayout(*args)
            form.setForm(self)
            size = self.newFormRow()
            for i in range(1, size):
                if self.__stopLoading(i):
                    size = i
                    break
                else:
                    row = list(self.__form[i].values())                    
                    h = BoxLayout(Qt.Horizontal, *row)
                    h.setAttribute(str(i))
                    h.setFont(self.__font)
                    hlay = h.layout()
                    if i in self.__rowsAligned:
                        hlay.setAlignment(self.__rowsAligned[i])
                    form.addRow(hlay)
                    self.__formRows[i] = hlay
            if self.__tablelize:
                form.setContentsMargins(0, 0, 0, 0)
                form.setSpacing(0)
            form.setForm(self)
            self.__layout = form
            gridLayout = FormGridLayout()
            gridLayout.setForm(self)
            gridLayout.addLayout(self.__layout, 0, 0)
            gridLayout.addWidget(self.__waitScreen, 0, 0)
            if self.__tablelize:
                gridLayout.setContentsMargins(0, 0, 0, 0)
                gridLayout.setSpacing(0)
            self.__gridLayout = gridLayout
            if self.__isAdding:
                self.addCurrentRow(size)
        return self.__gridLayout
    
    def group(self, parent = None):
        g = Group()
        g.setForm(self)
        g.setLayout(self.layout(parent))
        return g