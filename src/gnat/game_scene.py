import enum

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QBrush, QColor, QPixmap, QPolygon, Qt
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsPolygonItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsTextItem)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.gnat.animation import AnimatedGraphicsItem, AnimationTimer
from src.gnat.hand import GnatAttackHand
from src.gnat.ui import UILife, UIPauseScreen, UIRank, UIScore


class GameScene(QGraphicsScene):
    def __init__(self, projectData: ProjectData):
        super().__init__(0, 0, 256, 224)
        self.projectData = projectData
        self.setBackgroundBrush(Qt.GlobalColor.white)
        
        self.animationTimer = AnimationTimer()
        self.animationTimer.tick.connect(lambda: self.views()[0].viewport().repaint())

        screenMask = QGraphicsPolygonItem(QPolygon(QRect(0, 0, 256, 224)).subtracted(QRect(16, 16, 224, 192)))
        screenMask.setBrush(Qt.GlobalColor.black)
        screenMask.setPen(Qt.PenStyle.NoPen)
        screenMask.setZValue(common.GNATZVALUES.MASK)
        self.addItem(screenMask)
        
        self.scoreItem = UIScore()
        self.addItem(self.scoreItem)
        self.livesItem = UILife(self.animationTimer)
        self.addItem(self.livesItem)
        self.livesItem.setLifeCount(3)
        self.rankItem = UIRank(self.animationTimer)
        self.addItem(self.rankItem)
        self.rankItem.setRank(0)
        
        self.pauseScreen = UIPauseScreen(self.animationTimer)
        self.addItem(self.pauseScreen)
        self.pauseScreen.hide()
        
        self.pauseScreen.animationTimer.tick.connect(lambda: self.views()[0].viewport().repaint())
        
        self.setBackgroundBrush(QPixmap(":/gnat/spritesheets/bg1.png"))
        
        # item2 = QGraphicsTextItem("LEVEL")
        # item2.setFont("Mario Paint Letters")
        # item2.setDefaultTextColor(Qt.GlobalColor.black)
        # item2.setPos(16, 48)
        # self.addItem(item2)
        
        self.handCursor = GnatAttackHand(self.animationTimer)
        self.handCursor.setPos(QPoint(120, 104))
        self.addItem(self.handCursor)
        
    def pause(self, pos: QPoint):
        self.handCursor.hide()
        self.pauseScreen.onPause(pos)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.animationTimer.paused:
            if event.button() == Qt.MouseButton.LeftButton:
                self.scoreItem.reduce()
                self.handCursor.play(self.handCursor.getAnimation("swat"))
            elif event.button() == Qt.MouseButton.RightButton:
                self.pause(event.scenePos().toPoint())
            
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        self.handCursor.setPos(event.scenePos().toPoint())
        self.pauseScreen.setHandPos(event.scenePos().toPoint())
        
        return super().mouseMoveEvent(event)