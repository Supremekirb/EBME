from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (QComboBox, QDialog, QItemDelegate, QLineEdit,
                               QListWidget, QListWidgetItem, QSizePolicy)

import src.misc.common as common


# QIntValidator apparently has an overflow error with unsigned 32-bit. Wow!
# So we will do it ourselves.
class BigIntegerValidator(QValidator):
    """QValidator for big integers (greater or less than signed 32-bit)"""
    # Just a Python reimplementation because Python doesn't have that issue lol
    def __init__(self, minimum: int, maximum: int, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        if maximum < minimum:
            self.minimum = maximum
            self.maximum = minimum
        
    def validate(self, text: str, pos: int):
        if len(text) == 0:
            return QValidator.State.Intermediate
        if text == "-":
            return QValidator.State.Intermediate
        try: number = int(text)
        except ValueError:
            return QValidator.State.Invalid
        if not self.minimum <= number <= self.maximum:
            return QValidator.State.Intermediate
        else:
            return QValidator.State.Acceptable
    
    def fixup(self, text: str):
        try: number = int(text)
        except ValueError:
            return text # Gets passed back to validate(), so will be invalid
        if number < self.minimum:
            number = self.minimum
        if number > self.maximum:
            number = self.maximum
        return str(number)


# Item delegates for editing the cells. Thankfully, we can reuse them with some arguments

class SizedIntDelegate(QItemDelegate):
    def __init__(self, parent, lower: int, upper: int):
        super().__init__(parent)
        self.lower = lower
        self.upper = upper
        
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(BigIntegerValidator(self.lower, self.upper, editor))
        return editor
    
    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex):
        # Janky, but we only want one signal to be emitted. Otherwise we get two actions sent.
        model.blockSignals(True)
        model.setData(index, editor.text())
        model.blockSignals(False)
        model.setData(index, int(editor.text()), Qt.ItemDataRole.UserRole)


class BitFieldDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QListWidget(parent)
        for i in range(8):
            item = QListWidgetItem(f"Bit {i} (${hex(1<<i)[2:].upper()})")
            item.setCheckState(Qt.CheckState.Unchecked)
            editor.addItem(item)
        return editor
    
    def setModelData(self, editor: QListWidget, model: QAbstractItemModel, index: QModelIndex):
        data = 0
        for i in range(8):
            item = editor.item(i)
            data |= (item.checkState() == Qt.CheckState.Checked) << i
        # Janky, but we only want one signal to be emitted. Otherwise we get two actions sent.
        model.blockSignals(True)
        model.setData(index, data)
        model.blockSignals(False)
        model.setData(index, data, Qt.ItemDataRole.UserRole)
    
    def setEditorData(self, editor: QListWidget, index: QModelIndex):
        data = index.data(Qt.ItemDataRole.UserRole)
        if data is None: data = 0
        data = int(data)
        for i in range(8):
            item = editor.item(i)
            if data & (1 << i):
                item.setCheckState(Qt.CheckState.Checked)
                
    def updateEditorGeometry(self, editor, option, index):
        height = editor.parent().geometry().height()-option.rect.y()
        height = min(height, editor.sizeHint().height())
        editor.setGeometry(option.rect.x(), option.rect.y(), option.rect.width(), height)
        
    def paint(self, painter, option, index):
        return super().paint(painter, option, index)


class CCScriptIdentifierDelegate(QItemDelegate):        
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(common.CCScriptNameValidator(parent, True))
        return editor
    
    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex):
        model.setData(index, editor.text())
        model.setData(index, editor.text(), Qt.ItemDataRole.UserRole)

# These are not meant to be instantiated.
# All their methods are class methods.
# UserDataType will be subclassed to provide functionality.

class UserDataType:
    """Abstract class for userdata types. Should not be used on its own."""
    NAME = "User Data"
    
    # This one doesn't need to be reimplemented
    @classmethod
    def name(cls):
        return cls.NAME
        
    @staticmethod
    def dataSize() -> int:
        raise NotImplementedError("Must be subclassed!")
    
    @staticmethod
    def serialise(data) -> str:
        raise NotImplementedError("Must be subclassed!")

    @staticmethod
    def deserialise(data: str):
        raise NotImplementedError("Must be subclassed!")

    @staticmethod
    def delegate(parent) -> QItemDelegate:
        raise NotImplementedError("Must be subclassed!")

    @staticmethod
    def display(data) -> str:
        raise NotImplementedError("Must be subclassed!")


class UserDataInt8(UserDataType):
    """8-bit unsigned integer userdata type."""
    NAME = "Int8"
    @staticmethod
    def dataSize() -> int:
        return 1
    
    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: str):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, 0, (2**8)-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)

class UserDataInt16(UserDataType):
    """16-bit unsigned integer userdata type."""
    NAME = "Int16"
    @staticmethod
    def dataSize() -> int:
        return 2

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, 0, (2**16)-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)

class UserDataInt24(UserDataType):
    """24-bit unsigned integer userdata type."""
    NAME = "Int24"
    @staticmethod
    def dataSize() -> int:
        return 3

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, 0, (2**24)-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)

class UserDataInt32(UserDataType):
    """32-bit unsigned integer userdata type."""
    NAME = "Int32"
    @staticmethod
    def dataSize() -> int:
        return 4

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, 0, (2**32)-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)



class UserDataSInt8(UserDataType):
    """8-bit signed integer userdata type."""
    NAME = "SignedInt8"
    @staticmethod
    def dataSize() -> int:
        return 1
    
    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, -2**8//2+1, 2**8//2-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)

class UserDataSInt16(UserDataType):
    """16-bit signed integer userdata type."""
    NAME = "SignedInt16"
    @staticmethod
    def dataSize() -> int:
        return 2

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, -2**16//2+1, 2**16//2-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)

class UserDataSInt24(UserDataType):
    """24-bit signed integer userdata type."""
    NAME = "SignedInt24"
    @staticmethod
    def dataSize() -> int:
        return 3

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, -2**24//2+1, 2**24//2-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)

class UserDataSInt32(UserDataType):
    """32-bit signed integer userdata type."""
    NAME = "SignedInt32"
    @staticmethod
    def dataSize() -> int:
        return 4

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)
    
    @staticmethod
    def delegate(parent):
        return SizedIntDelegate(parent, -2**32//2+1, 2**32//2-1)
    
    @staticmethod
    def display(data) -> str:
        return str(data)


class UserDataBitfield(UserDataType):
    """8-bit bitfield userdata type."""
    NAME = "Bitfield"
    @staticmethod
    def dataSize() -> int:
        return 1

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: int):
        return int(data)

    @staticmethod
    def delegate(parent):
        return BitFieldDelegate(parent)
    
    @staticmethod
    def display(data) -> str:
        string = ""
        for i in range(8):
            if data & (1<<i):
                string += "✓"
            else:
                string += "✗"
        return string


class UserDataIdentifier8(UserDataType):
    """8-bit CCScript identifier type."""
    NAME = "Identifier8"
    @staticmethod
    def dataSize() -> int:
        return 1

    @staticmethod
    def serialise(data) -> str:
        return str(data)
    
    @staticmethod
    def deserialise(data: str):
        return str(data)
    
    @staticmethod
    def delegate(parent):
        return CCScriptIdentifierDelegate(parent)

    @staticmethod
    def display(data) -> str:
        return str(data)

class UserDataIdentifier16(UserDataIdentifier8):
    """16-bit CCScript identifier type"""
    NAME = "Identifier16"
    @staticmethod
    def dataSize() -> int:
        return 2

class UserDataIdentifier24(UserDataIdentifier8):
    """24-bit CCScript identifier type"""
    NAME = "Identifier24"
    @staticmethod
    def dataSize() -> int:
        return 3

class UserDataIdentifier32(UserDataIdentifier8):
    """32-bit CCScript identifier type"""
    NAME = "Identifier32"
    @staticmethod
    def dataSize() -> int:
        return 4
    

USERDATA_TYPES: tuple[UserDataType] = (
    UserDataBitfield,
    UserDataInt8,
    UserDataInt16,
    UserDataInt24,
    UserDataInt32,
    UserDataSInt8,
    UserDataSInt16,
    UserDataSInt24,
    UserDataSInt32,
    UserDataIdentifier8,
    UserDataIdentifier16,
    UserDataIdentifier24,
    UserDataIdentifier32,
)