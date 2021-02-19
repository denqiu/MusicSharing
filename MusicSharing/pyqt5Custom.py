from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import re

class Style:
    def __init__(self, style = ""):
        if style.strip() == "":
            self.clear()
        else:
            self.importStyle(style)
        
    def setWidget(self, name):
        self.__widget = name
        if not name in self.__style:
            self.__style[name] = {}
        
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
        self.searchRows()
        self.searchNames()
        self.searchClasses()
        self.setMatchCases()
        self.clearResults()
        
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

class Group(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("group")
        self.setForm(None)
        self.setStyleSheet("border:0")
        
    def setForm(self, form):
        self.__form = form
        
    def getForm(self):
        return self.__form
        
    def searchObjects(self, searchForm):
        if self.__form is None:
            return None
        return self.__form.searchObjects(searchForm)
    
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
        super().__init__(parent)
        
    def setForm(self, form = None):
        self.__form = form
        
    def getForm(self):
        return self.__form
        
class Form:
    def __init__(self, parent = None):
        self.setParent(parent)
        self.clearForm()
        self.newRow()
        self.setFont(None)
        self.searchResults(None)
        self.__merged = False
        self.__layout = None
        self.__currentRow = None
        self.isAddingItems(False)
        self.setRowSize(None)
        self.__rowsAligned = {}
        
    def setRowSize(self, rowSize):
        self.__rowSize = rowSize
        return self
        
    def checkRowSize(self):
        if self.__currentRow is None or self.__rowSize is None:
            return False
        if self.__rowSize < 0:
            return False
        return self.__currentRow.size() == self.__rowSize
        
    def setParent(self, parent = None):
        self.__parent = parent
        return self
    
    def getParent(self):
        return self.__parent
        
    def clearForm(self):
        self.__form = {}
        return self
        
    def newRow(self):
        self.__row = {}
        return self
    
    def setRow(self, row):
        self.__row = row
        return self
    
    def isAddingItems(self, isAdding):
        self.__isAdding = isAdding
        return self
    
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
                obj.setObjectName(name)  
        return obj 
            
    def __add(self, obj, font, *check):
        if self.checkRowSize():
            self.addRow()
        for c in check:
            obj = self.__checkName(obj, c)
        name = obj.getAttribute() if isinstance(obj, BoxLayout) else obj.objectName()
        if font is None:
            font = self.__font
        if not font is None:
            if obj.font() == QLabel().font():
                obj.setFont(font)
        self.__row[name] = obj
        if not self.__currentRow is None:
            self.__currentRow.addItems(obj)
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
        but = {ChildButton: "child-button", ScrollChildButton: "scroll-child-button", ArrowButton: "arrow", Button: "button"}
        for b in but:
            if isinstance(button, b):
                return self.__add(button, font, but[b])
        return self
    
    def addBoxLayout(self, boxLayout, font = None):
        return self.__add(boxLayout, font, "vlayout", "hlayout")
      
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
    
    def setCurrentRow(self, row = None):
        if row is None:
            row = self.formSize()
        self.__currentRow = BoxLayout(BoxLayout.ALIGN_HORIZONTAL)
        self.__currentRow.setAttribute(str(row))
        self.__currentRow.setFont(self.__font)
        self.__layout.addRow(self.__currentRow.layout())
        
    def isCurrentRowVisible(self):
        if self.__currentRow is None:
            return False
        return self.__currentRow.isVisible()
    
    def currentRowSize(self):
        if self.__currentRow is None:
            return 0
        return self.__currentRow.size()
        
    def addRow(self, alignment = None):
        row = self.newFormRow()
        if not self.__layout is None:
            if self.checkRowSize():
                self.setCurrentRow(row)
            else:
                return self
        self.__form[row] = self.__row
        if not alignment is None:
            self.__rowsAligned[row] = alignment
        return self.newRow()
    
    def removeRow(self, rowNumber = None):
        if rowNumber is None:
            rowNumber = len(self.__form)
        if rowNumber in self.__form:
            r = self.__form.pop(rowNumber)
            nums = [(n-1, n) for n in self.__form if n > rowNumber]
            if len(nums) > 0:
                for (newKey, key) in nums:
                    self.__form[newKey] = self.__form.pop(key)
            if not self.__layout is None:
                self.__layout.removeRow(rowNumber-1)
            return r
        return None
    
    def searchObjects(self, searchForm):
        if searchForm.searchAllRows():
            for r in self.__form:
                searchForm.search(r, self.__form[r])
        else:
            for r in searchForm.rows:
                if r in self.__form:
                    searchForm.search(r, self.__form[r])
                else:
                    print("Row {} does not exist".format(r))
        results = searchForm.results
        searchForm.__init__()
        return self.searchResults(results)
    
    def __checkObject(self, obj):
        if isinstance(obj, CheckBox) or isinstance(obj, QCheckBox):
            return obj.isChecked()
        if isinstance(obj, QLineEdit):
            return obj.text().strip()
        elif isinstance(obj, ComboBox):
            return obj.currentText().strip()
        elif isinstance(obj, Button):
            text, texts = (obj.getText(), [])
            for t in text:
                if t != "border":
                    texts.append(self.__checkObject(text[t]))
            return "\n".join(texts)
        elif isinstance(obj, ButtonText):
            return obj.getText().strip()
        elif isinstance(obj, QLabel):
            return obj.text().strip()
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
    
    def layout(self, parent = None):
        if self.__layout is None:
            if parent is None:
                parent = self.__parent
            form = FormLayout(parent)
            form.setForm(self)
            size = self.newFormRow()
            for i in range(1, size):
                row = list(self.__form[i].values())                    
                h = BoxLayout(BoxLayout.ALIGN_HORIZONTAL, *row)
                h.setAttribute(str(i))
                h.setFont(self.__font)
                hlay = h.layout()
                if i in self.__rowsAligned:
                    hlay.setAlignment(self.__rowsAligned[i])
                form.addRow(hlay)
            self.__layout = form
            if self.__isAdding:
                self.setCurrentRow(size)
        return self.__layout
    
    def group(self, parent = None):
        g = Group()
        g.setForm(self)
        g.setLayout(self.layout(parent))
        return g
    
class ParentWindow(QWidget):
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
        
    def changeEvent(self, QEvent):
        if QEvent.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.minimizeChildren()
        elif self.isVisible():
            self.mousePressEvent(QEvent)
                    
    def mousePressEvent(self, QEvent):
        self.restoreChildren()
            
    def focusInEvent(self, QEvent):
        self.mousePressEvent(QEvent)
        
    def eventFilter(self, QObject, QEvent):
        if QEvent.type() == QEvent.NonClientAreaMouseButtonPress:
            if not self.windowState() & Qt.WindowMinimized:
                self.mousePressEvent(QEvent)
        return super().eventFilter(QObject, QEvent)

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
            
    def changeEvent(self, QEvent):
        if self.checkParentWindow():
            if self.isVisible(): #when opening from taskbar
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
            
    def changeEvent(self, QEvent):
        if QEvent.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.minimizeChildren()
        else:
            if self.checkParentWindow():
                if self.isVisible(): #when opening from taskbar
                    self.__change()
            if self.isVisible():
                self.mousePressEvent(QEvent)
            
    def mousePressEvent(self, QEvent):
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
        
class ButtonText(QLabel):
    def __init__(self, text = "", attribute = "", border = None):
        super().__init__()
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
  
    def setButton(self, button):
        self.__button = button
        
    def enterText(self, QMouseEvent):
        self.entered = True
            
    def enterEvent(self, QMouseEvent):
        if self.__button is None:
            self.enterText(QMouseEvent)
        else:
            self.__button.enterEvent(QMouseEvent)
            
    def leaveText(self, QMouseEvent):
        self.entered = False
          
    def leaveEvent(self, QMouseEvent):
        if self.__button is None:
            self.leaveText(QMouseEvent)
        else:
            self.__button.leaveEvent(QMouseEvent)
            
    def mouseLeftPressed(self):
        pass
    
    def mouseRightPressed(self):
        pass
            
    def mousePressText(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed()
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed()
        
    def mousePressEvent(self, QMouseEvent):
        if self.__button is None:
            self.mousePressText(QMouseEvent)
        else:
            self.__button.mousePressEvent(QMouseEvent)

    def mouseLeftReleased(self):
        pass
    
    def mouseRightReleased(self):
        pass
            
    def mouseReleaseText(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased()
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased()
        
    def mouseReleaseEvent(self, QMouseEvent):
        if self.__button is None:
            self.mouseReleaseText(QMouseEvent)
        else:
            self.__button.mouseReleaseEvent(QMouseEvent)

class BoxLayout:
    ALIGN_VERTICAL = "vertical"
    ALIGN_HORIZONTAL = "horizontal"
    
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
        align = {QVBoxLayout: self.ALIGN_VERTICAL, QHBoxLayout: self.ALIGN_HORIZONTAL}[type(self.__layout)]
        align = {self.ALIGN_VERTICAL: "v", self.ALIGN_HORIZONTAL: "h"}[align]
        if attribute.strip() != "":
            attribute = "-" + attribute.strip()
        self.__attribute = "{}layout{}".format(align, attribute)
        self.__layout.setObjectName(self.__attribute)
        
    def getAttribute(self):
        return self.__attribute
        
    def setLayout(self, alignment):
        self.__layout = {self.ALIGN_VERTICAL: QVBoxLayout, self.ALIGN_HORIZONTAL: QHBoxLayout}[alignment]()
        
    def setItems(self, *items):
        self.__items = list(items)
        
    def __method(self, items):
        method = {True: self.__layout.addWidget, False: self.__layout.addLayout}
        widgets = (QLabel, QGroupBox)
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
        super().__init__()
        self.backgroundColor = Qt.white
        self.clickColor = Qt.gray
        self.hoverColor = Qt.black
        self.entered = False
        self.clearText()
        self.clearChildButtons()
        self.addText(ButtonText(border="1px solid black"))
        self.addText(*text)
        self.clearLayout()
        self.__layout[self.__layoutSize()] = {self: (None, 0)}
        self.addTextToGrid("border")
        self.setObjectName("button")
        
    def clearText(self):
        self.__text = {}
        
    def __checkName(self, obj, check):
        name = obj.objectName()
        if check in name:
            c = {"text": self.__text, "button": self.__buttons, "child-button": self.__buttons, "scroll-child-button": self.__buttons}
            name = [n for n in reversed(c[check].keys()) if not re.search("^"+check+"\d*$", n) is None]
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
        return self.__text if len(text) == 0 else [self.__text[t] if t in self.__text else None for t in text]
    
    def clearChildButtons(self):
        self.__buttons = {}
        
    def addChildButtons(self, *children):
        for c in children:
            if isinstance(c, ChildButton):
                c.setButton(self)
                c = self.__checkName(c, "child-button")
                self.__buttons[c.objectName()] = c
                
    def removeChildButtons(self, *children):
        rem = {}
        for c in children:
            if isinstance(c, ChildButton):
                c = c.objectName()
            if c in self.__buttons:
                rem[c] = self.__buttons.pop(c)
            else:
                print("Child button: {} not found".format(c))
        return rem
                
    def getChildButtons(self, *children):
        return tuple(self.__buttons if len(children) == 0 else [self.__buttons[c] if c in self.__buttons else None for c in children])
    
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
        for b in self.__buttons:
            self.__buttons[b].setFont(*args, **kwargs)
            
    def clearLayout(self):
        self.__layout = {}
        self.__layoutNames = {}
        
    def __layoutSize(self):
        return len(self.__layout)+1
    
    def __checkObject(self, obj, objClass):
        if isinstance(obj, objClass):
            obj = obj.objectName()
        if type(obj) is str:
            o = {ButtonText: self.__text, ChildButton: self.__buttons}[objClass]
            if obj in o:
                return o[obj]
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

    def addChildButtonToGrid(self, childButton, alignment = None, move = 0, insert = None):
        childButton = self.__checkObject(childButton, ChildButton)
        if childButton is None:
            print("No ChildButton exists with this attribute")
        else:
            self.__appendToLayout(childButton, childButton.objectName(), alignment, move, insert)
            
    def addBoxLayoutToGrid(self, boxLayout, alignment = None, move = 0, insert = None):
        items = boxLayout.getItems()
        for i, b in enumerate(items):
            if type(b) is str:
                for j in (self.__text, self.__buttons):
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
                                        
    def layout(self):
        g = QGridLayout()
        method = {type(self): g.addWidget, ButtonText: g.addWidget, BoxLayout: g.addLayout, ChildButton: g.addLayout}
        for i in range(1, self.__layoutSize()):
            b, (align, move) = list(self.__layout[i].items())[0]
            a = b
            for j in (isinstance(b, BoxLayout), i > 1 and isinstance(b, ChildButton)):
                if j: 
                    a = a.layout()
                    break
            args = [a, 0, move]
            if not align is None:
                args.append(align)
            for m in method:
                c = isinstance(b, m) if i > 1 else type(b) is m
                if c:
                    method[m](*args)
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
            
    def mouseRightPressed(self):
        pass
    
    def mouseLeftPressed(self):
        self.setColor(self, self.backgroundRole(), self.clickColor)
        
    def mousePressed(self, QMouseEvent):       
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftPressed()
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightPressed()
                
    def mousePressEvent(self, QMouseEvent):
        self.mousePressed(QMouseEvent)
        
    def mouseRightReleased(self):
        pass
    
    def mouseLeftReleased(self):
        self.setColor(self, self.backgroundRole(), self.hoverColor)
        self.setFocus()

    def mouseReleased(self, QMouseEvent):
        if self.isEnabled():
            if QMouseEvent.button() == Qt.LeftButton:
                self.mouseLeftReleased()
            elif QMouseEvent.button() == Qt.RightButton:
                self.mouseRightReleased()
                
    def mouseReleaseEvent(self, QMouseEvent):
        self.mouseReleased(QMouseEvent)
                
class ChildButton(Button):
    def __init__(self, *text):
        super().__init__(*text)
        self.setButton(None)
        self.setObjectName("child-button")
        
    def setButton(self, button):
        self.__button = button
            
    def enterEvent(self, QMouseEvent):
        if self.__button is None:
            self.enter(QMouseEvent)
        else:
            self.__button.enterEvent(QMouseEvent)
        
    def leaveEvent(self, QMouseEvent):
        if self.__button is None:
            self.leave(QMouseEvent)
        else:
            self.__button.leaveEvent(QMouseEvent)
  
    def mousePressEvent(self, QMouseEvent):
        if self.__button is None:
            self.mousePressed(QMouseEvent)
        else:
            self.__button.mousePressEvent(QMouseEvent)
            
    def mouseReleaseEvent(self, QMouseEvent):
        if self.__button is None:
            self.mouseReleased(QMouseEvent)
        else:
            self.__button.mouseReleaseEvent(QMouseEvent)
        
class ScrollArea(QScrollArea):
    def __init__(self, widget):
        super().__init__()
        self.setObjectName("scroll-area")
        self.currentIndex = -1
        self.previousButton = None
        if isinstance(widget, Form):
            widget.setParent(self)
            widget.layout()
        else:
            self.setWidget(widget)
        self.setWidgetResizable(True)
        s = Style()
        s.setWidget("QWidget#scroll-area")
        s.setAttribute("background-color", "white")
        s.setAttribute("border", "0")
        self.setStyleSheet(s.css())
        
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
                    
class ScrollChildButton(Button):
    def __init__(self, index, *text):
        super().__init__(*text)
        self.index = index
        self.setObjectName("scroll-child-button")
        
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
            
class TextBox(QLineEdit):
    class _Message(ButtonText):
        def __init__(self, message, textBox):
            super().__init__(message, "message")
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
            
        def mouseLeftReleased(self):
            if self.textBox.msgIn:
                self.textBox.setFocus()
            else:
                self.__getParent().mouseReleaseEvent(QMouseEvent)
        
    def __init__(self, defaultText = "", message = "", msgIn = True):
        super().__init__()
        self.setObjectName("textbox" if message.strip() == "" else message)
        s = Style()
        s.setWidget("QLineEdit")
        s.setAttribute("border", "1px solid black")
        s.setAttribute("selection-background-color", "black")
        self.setStyleSheet(s.css())
        self.msgIn = msgIn
        self.__message = self._Message(message, self)
        self.textChanged.connect(self.changeText)
        self.setText(defaultText)
              
    def setFont(self, *args, **kwargs):
        QLineEdit.setFont(self, *args, **kwargs)
        self.__message.setFont(*args, **kwargs)
        
    def changeText(self):
        t = self.text().strip()
        self.setToolTip(t)
        if self.msgIn:
            self.__message.setVisible(t == "")
        
    def layout(self):
        if self.msgIn:
            g = QGridLayout()
            g.addWidget(self, 0, 0)
            g.addWidget(self.__message, 0, 0, Qt.AlignLeft)
            return g
        else:
            h = QHBoxLayout()
            h.addWidget(self.__message)
            h.addWidget(self)
            return h

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

class Password(TextBox):
    def __init__(self, defaultText = "", message = "", encode = None):
        if message.strip() == "":
            message = "Password:"
        else:
            message += " Password:"
        super().__init__(defaultText, message, False)
        self.encode = Encode if encode is None else encode
        self.setEchoMode(TextBox.Password)
        
    def setToolTip(self, string):
        return
   
    def text(self):
        return self.encode(TextBox.text(self)).text()
        
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
             
    def paintEvent(self, event):
        if not self.__start:
            self.__start = True
            self.setColor(self, self.backgroundRole(), self.backgroundColor)
        p = QPainter()
        p.begin(self)
        color = self.backgroundColor if self.entered else self.hoverColor
        p.setPen(QPen(color, 2, Qt.SolidLine))
        p = self.__drawArrow(p)
        p.end()
        
    def mouseLeftReleased(self):
        ChildButton.mouseLeftReleased(self)
        if not self.__combobox is None:
            self.__combobox.showPopup()

class ComboBox(QComboBox):
    class _Combo(Button):
        def __init__(self, comboBox):
            currentText = ButtonText(attribute="combo")
            super().__init__(currentText)
            self.addTextToGrid("combo")
            self.setComboBox(comboBox)
            self.setArrowButton()
            self.currentText = currentText
            self.start = False
            
        def paintEvent(self, event):
            Button.paintEvent(self, event)
            if not self.start:
                self.start = True
                self.setColor(self, self.backgroundRole(), self.backgroundColor)
              
        def setArrowButton(self, arrow = None):
            if arrow is None:
                arrow = ArrowButton()
            arrow.setComboBox(self.comboBox)
            self.addChildButtons(arrow)
            arrow.setButton(None)
            self.arrow = arrow
            self.addChildButtonToGrid(arrow.objectName(), Qt.AlignRight)
            
        def setComboBox(self, comboBox):
            self.comboBox = comboBox
            
        def showEvent(self, event):
            if self.isVisible():
                self.setFixedHeight(self.comboBox.height())
            
        def setArrowSize(self):
            h = self.height()
            self.arrow.setFixedSize(h, h)      
              
        def mouseLeftReleased(self):
            Button.mouseLeftReleased(self)
            self.comboBox.showPopup()
        
    def __init__(self, *items):
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
        
    def textChanged(self):
        self.__combo.currentText.setText(" "+self.currentText())
        
    def setArrowButton(self, arrow):
        self.__combo.setArrowButton(arrow)
        
    def showEvent(self, event):
        if self.isVisible():
            self.__combo.setArrowSize()
        
    def layout(self):
        g = QGridLayout()
        g.addWidget(self, 0, 0)
        g.addLayout(self.__combo.layout(), 0, 0)
        return g
    
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
             
    def paintEvent(self, event):
        p = QPainter()
        p.begin(self)
        color = self.__hover if self.__checked else self.backgroundColor
        p.setPen(QPen(color, 2, Qt.SolidLine))
        p = self.__drawIndicator(p)
        p.end()
        
    def isChecked(self):
        return self.__checked
        
    def mouseLeftReleased(self):
        ChildButton.mouseLeftReleased(self)
        self.__checked = not self.__checked
        
class CheckBox(Button):
    class _Text(ButtonText):
        def __init__(self, text):
            super().__init__(text)
            self.textHoverColor = None
            self.setToolTip("")
       
    def __init__(self, text = "checkbox"):
        super().__init__(self._Text(text))
        border = self.getText("border")[0]
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
        self.addChildButtons(indicator)
        self.addChildButtonToGrid(indicator.objectName(), Qt.AlignLeft)
        
    def showEvent(self, event):
        if self.__start:
            if self.isVisible():
                self.setFixedWidth(self.width()+self.indicator.width())
                self.__start = False
        
    def mouseLeftReleased(self):
        Button.mouseLeftReleased(self)
        self.indicator.mouseLeftReleased()
         
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
            border = self.getText("border")[0]
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
                 
        def paintEvent(self, event):
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
            
        def showEvent(self, event):
            if self.isVisible():
                self.setFixedSize(self.width()+5, self.height()+5)
                 
        def mouseLeftReleased(self):
            Button.mouseLeftReleased(self)
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
        md = MessageBox.__dict__
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