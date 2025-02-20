import math

from PySide6.QtCore import QPoint, QRect, QPointF
from PySide6.QtGui import QBrush, QColor, QPixmap, QPolygon, Qt
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsPolygonItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsTextItem, QGraphicsItem)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.gnat import scripting
from src.gnat.animation import AnimationTimer
from src.gnat.bonus import BonusHand
from src.gnat.game_state import GameState
from src.gnat.hand import GnatAttackHand
from src.gnat.spawning import LevelSpawnManger
from src.gnat.ui import UILife, UIPauseScreen, UIRank, UIScore


class GameScene(QGraphicsScene):
    def __init__(self, projectData: ProjectData):
        super().__init__(0, 0, 256, 224)
        self.projectData = projectData
        self.setBackgroundBrush(Qt.GlobalColor.white)
        
        self.animationTimer = AnimationTimer(16)
        self.animationTimer.tick.connect(lambda: self.views()[0].viewport().repaint())
        self.animationTimer.tick.connect(lambda: scripting.step())

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
        
        self.gameState = GameState(self, self.animationTimer)
        
        self.levelSpawnManager = LevelSpawnManger(common.absolutePath("assets/gnat/levels/1.json"))
        self.levelSpawnManager.startSpawning()
        
        self.handCursor = GnatAttackHand(self.animationTimer)
        self.handCursor.setPos(QPoint(120, 104))
        self.addItem(self.handCursor)
        
        self.lastPos = QPoint(0, 0)
        
        self.pause()
        
    def getProximityToHand(self, pos: QPointF):
        return abs(math.dist(pos.toTuple(), self.handCursor.pos().toTuple()))
    
    def getAngleToHand(self, pos: QPointF):
        return math.atan2(self.handCursor.x() - pos.x(), self.handCursor.y() - pos.y())
    
    def isIntersectingWithHand(self, item: QGraphicsItem):
        return self.handCursor in self.collidingItems(item)
        
    def spawnLife(self):
        BonusHand()
        
    def newLevel(self, level: int):
        self.levelSpawnManager = LevelSpawnManger(common.absolutePath(f"assets/gnat/levels/{str(level)}.json"))
        
    def pause(self, pos: QPoint = QPoint(128, 122)):
        self.handCursor.hide()
        self.pauseScreen.onPause(pos)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.animationTimer.paused:
            if event.button() == Qt.MouseButton.LeftButton:
                # self.scoreItem.reduce()
                self.handCursor.swat()
            elif event.button() == Qt.MouseButton.RightButton:
                self.pause(event.scenePos().toPoint())
            
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        self.handCursor.setPos(event.scenePos().toPoint())
        self.pauseScreen.setHandPos(event.scenePos().toPoint())
        
        self.lastPos = event.scenePos().toPoint()
        
        return super().mouseMoveEvent(event)