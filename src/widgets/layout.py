from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QResizeEvent, QTransform, QWheelEvent
from PySide6.QtWidgets import (QBoxLayout, QFrame, QGraphicsView, QSpacerItem,
                               QTabWidget, QWidget)


# https://stackoverflow.com/questions/10053839/how-does-designer-create-a-line-widget
class HSeparator(QFrame):
    """Custom horizontal separation line"""
    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class VSeparator(QFrame):
    """Custom vertical separation line"""
    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

# https://stackoverflow.com/a/49851646
class AspectRatioWidget(QWidget):
    def __init__(self, widget: QWidget, parent: QWidget = None):
        super().__init__(parent)
        self.aspect_ratio = widget.size().width() / widget.size().height()
        self.setLayout(QBoxLayout(QBoxLayout.Direction.LeftToRight, self))
        #  add spacer, then widget, then spacer
        self.layout().addItem(QSpacerItem(0, 0))
        self.layout().addWidget(widget)
        self.layout().addItem(QSpacerItem(0, 0))
        
        self.setContentsMargins(0, 0, 0, 0)
        # self.layout().setAlignment(widget, Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event: QResizeEvent):
        w = event.size().width()
        h = event.size().height()

        if w / h > self.aspect_ratio:  # too wide
            self.layout().setDirection(QBoxLayout.Direction.LeftToRight)
            widget_stretch = h * self.aspect_ratio
            outer_stretch = (w - widget_stretch) / 2 + 0.5
        else:  # too tall
            self.layout().setDirection(QBoxLayout.Direction.TopToBottom)
            widget_stretch = w / self.aspect_ratio
            outer_stretch = (h - widget_stretch) / 2 + 0.5

        self.layout().setStretch(0, outer_stretch)
        self.layout().setStretch(1, widget_stretch)
        self.layout().setStretch(2, outer_stretch)
        
class HorizontalGraphicsView(QGraphicsView):    
    def wheelEvent(self, event: QWheelEvent):
        self.horizontalScrollBar().event(event)
        
class UprightIconsWestTabWidget(QTabWidget):
    def addTab(self, widget: QWidget, icon: QIcon, label: str):
        icon = QIcon(icon.pixmap(QSize(100, 100)).transformed(QTransform().rotate(90)))
        return super().addTab(widget, icon, label)
