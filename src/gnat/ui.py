from PySide6.QtCore import QPoint, QRect, QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QPixmap, Qt
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsScene,
                               QGraphicsTextItem)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.gnat.animation import (AnimatedGraphicsItem, AnimationTimer,
                                loadAnimations)
from src.gnat.game_state import GameState


class UIScore(QGraphicsTextItem):
    def __init__(self):
        super().__init__()
        self.setFont("Mario Paint Numbers")
        self.setDefaultTextColor(Qt.GlobalColor.black)
        self.setScore(100)
        self.setPos(92, 12)
        self.setZValue(common.GNATZVALUES.TEXT)
        
    def reduce(self):
        if self.score > 0:
            self.setScore(self.score-1)
    
    def setScore(self, score: int):
        self.score = score
        self.setPlainText(str(self.score).rjust(3))

class UILife(QGraphicsItem):
    def __init__(self, animationTimer: AnimationTimer):
        super().__init__()
        
        self.animationTimer = animationTimer
        self.animations = loadAnimations(common.absolutePath("assets/gnat/animations/bonus.json"))
        self.pixmap = QPixmap(":/gnat/spritesheets/bonus.png")
        self.lifeDisplay: list[AnimatedGraphicsItem] = []
        self.setZValue(common.GNATZVALUES.TEXT)
        
        self.setPos(176, 16)
    
    def setLifeCount(self, new: int):
        for item in self.lifeDisplay:
            self.scene().removeItem(item)
        self.lifeDisplay = []
        
        for i in range(new):
            item = AnimatedGraphicsItem(self.animationTimer, self.pixmap, self.animations)
            item.setParentItem(self)
            item.play(item.getAnimation("display"))
            item.setPos((i%3)*16, (i//3)*16)
            self.lifeDisplay.append(item)
            
    def boundingRect(self):
        return QRectF(176, 16, 48, 228)
    
    
class UIRank(QGraphicsRectItem):
    def __init__(self, animationTimer: AnimationTimer):
        super().__init__()
        
        self.animationTimer = animationTimer
        self.animations = loadAnimations(common.absolutePath("assets/gnat/animations/rank.json"))
        self.pixmap = QPixmap(":/gnat/spritesheets/rank.png")
        self.rankDisplay: list[AnimatedGraphicsItem] = []
        self.setZValue(common.GNATZVALUES.TEXT)
        
        self.setPos(16, 16)
    
    def setRank(self, new: int):
        new = new % 16
        
        for item in self.rankDisplay:
            self.scene().removeItem(item)
        self.rankDisplay = []
                
        for i in range(new):
            item = AnimatedGraphicsItem(self.animationTimer, QPixmap(":/gnat/spritesheets/rank.png"), self.animations)
            item.setParentItem(self)
            item.play(item.animations[i])
            item.setPos((i%5)*16, (i//5)*16)
            self.rankDisplay.append(item)
            
    def boundingRect(self):
        return QRectF(16, 16, 80, 48)
    
    
class UILever(AnimatedGraphicsItem):
    pulled = Signal()
    def __init__(self, animationTimer: AnimationTimer):
        animations = loadAnimations(common.absolutePath("assets/gnat/animations/lever.json"))
        super().__init__(animationTimer, QPixmap(":/gnat/spritesheets/lever.png"), animations)
        self.setZValue(common.GNATZVALUES.PAUSELEVER)
        self.play(self.getAnimation("idle"))
        self.disabled = False
    
    def pull(self):
        if not self.disabled:
            self.disabled = True
            GameState.playSFX("lever")
            self.play(self.getAnimation("pull"))
    
    def reset(self):
        self.disabled = False
        self.play(self.getAnimation("idle"))
    
    def onNonLoopingAnimationEnd(self, last):
        self.pulled.emit()
        self.reset()
        
    def boundingRect(self):
        return QRectF(0, 0, 16, 24)
    

class UIHand(AnimatedGraphicsItem):
    def __init__(self, animationTimer: AnimationTimer):
        animations = loadAnimations(common.absolutePath("assets/gnat/animations/hand.json"))
        super().__init__(animationTimer, QPixmap(":/gnat/spritesheets/hand.png"), animations)
        self.setZValue(common.GNATZVALUES.PAUSEHAND)
        self.play(self.getAnimation("large"))
        

class UIDance(AnimatedGraphicsItem):
    def __init__(self, animationTimer: AnimationTimer):
        animations = loadAnimations(common.absolutePath("assets/gnat/animations/dance.json"))
        super().__init__(animationTimer, QPixmap(":/gnat/spritesheets/dance.png"), animations)
        self.setZValue(common.GNATZVALUES.PAUSELEVER)
        self.play(self.getAnimation("idle"))
        
        self._dancing = False
        
    def reset(self):
        self._dancing = False
        self.play(self.getAnimation("idle"))
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._dancing:
                self._dancing = True
                self.play(self.getAnimation("dance"))
        return super().mousePressEvent(event)
        
        
class UIPauseScreen(QGraphicsPixmapItem):
    def __init__(self, animationTimerToPause: AnimationTimer):
        super().__init__()
        self.setPixmap(QPixmap(":/gnat/spritesheets/pause.png"))
        self.setZValue(common.GNATZVALUES.PAUSEBG)
        
        self.animationTimerToPause = animationTimerToPause
        self.animationTimer = AnimationTimer()
        
        self.resumeLever = UILever(self.animationTimer)
        self.resumeLever.pulled.connect(self.onResume)
        self.resumeLever.setPos(10, 49)
        self.resumeLever.setParentItem(self)
        
        self.quitLever = UILever(self.animationTimer)
        self.quitLever.setPos(10, 81)
        self.quitLever.setParentItem(self)
        
        self.hand = UIHand(self.animationTimer)
        self.hand.setParentItem(self)
        
        self.dance = UIDance(self.animationTimer)
        self.dance.setPos(9, 13)
        self.dance.setParentItem(self)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if 47 <= event.pos().y() <= 72:
                self.resumeLever.pull()
                self.quitLever.disabled = True
            if 80 <= event.pos().y() <= 105:
                self.quitLever.pull()
                self.resumeLever.disabled = True
        return super().mousePressEvent(event)
        
    def setHandPos(self, pos: QPoint):
        pos = self.mapFromScene(pos)
        self.hand.setPos(QPoint(common.cap(pos.x(), 0, 103), common.cap(pos.y(), 0, 111)))
        
    def onPause(self, pos: QPoint):
        self.animationTimerToPause.pause()
        self.setPos((common.cap(pos.x()-48, 32, 120)//8)*8,
                    (common.cap(pos.y()-64, 32, 80)//8)*8)
        
        self.resumeLever.reset()
        self.quitLever.reset()
        self.dance.reset()
        self.show()
        
        self.setHandPos(pos)
        
    def onResume(self):
        self.hide()
        self.animationTimerToPause.resume()
        self.scene().soundManager.currentBGM.resume()
