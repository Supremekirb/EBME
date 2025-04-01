import math

from PySide6.QtCore import QPoint, QPointF, QRect
from PySide6.QtGui import QBrush, QColor, QPixmap, QPolygon, Qt
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsPolygonItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QGraphicsTextItem)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.gnat import scripting
from src.gnat.animation import AnimationTimer
from src.gnat.attack import Attack
from src.gnat.bomb import Bomb
from src.gnat.bonus import BonusHand
from src.gnat.boss import Boss
from src.gnat.cutscene import RoundStartDisplay, ScreenFader
from src.gnat.game_state import GameState
from src.gnat.gnat import Gnat
from src.gnat.hand import GnatAttackHand
from src.gnat.levels import LevelManager
from src.gnat.misc import AttackProjectile, BossMini, BossProjectile, Mini
from src.gnat.sound import SoundManager
from src.gnat.spawner import Spawner
from src.gnat.ui import UILife, UIPauseScreen, UIRank, UIScore


class GameScene(QGraphicsScene):
    def __init__(self):
        super().__init__(0, 0, 256, 224)
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
        
        self.roundDisplayItem = RoundStartDisplay()
        self.addItem(self.roundDisplayItem)
        
        self.screenFaderItem = ScreenFader()
        self.addItem(self.screenFaderItem)
        
        self.pauseScreen = UIPauseScreen()
        self.addItem(self.pauseScreen)
        self.pauseScreen.hide()
        
        self.pauseScreen.animationTimer.tick.connect(lambda: self.views()[0].viewport().repaint())
        
        self.setBackgroundBrush(QPixmap(":/gnat/spritesheets/bg1.png"))
        
        self.gameState = GameState(self)
        
        self.handCursor = GnatAttackHand()
        self.handCursor.setPos(QPoint(120, 104))
        self.addItem(self.handCursor)
        
        self.gameState.pauseGame()
        
        self.lastPos = QPoint(0, 0)

        
    def getProximityToHand(self, pos: QPointF):
        return abs(math.dist(pos.toTuple(), self.handCursor.pos().toTuple()))
    
    def getAngleToHand(self, pos: QPointF):
        return math.atan2(self.handCursor.x() - pos.x(), self.handCursor.y() - pos.y())
    
    def isIntersectingWithHand(self, item: QGraphicsItem):
        return self.handCursor in self.collidingItems(item)
        
    def spawnLife(self):
        BonusHand()
        
    def spawnBoss(self):
        Boss()
        
    def clearEnemies(self):
        for i in self.items():
            if isinstance(i, (
                Gnat,
                Spawner,
                Bomb,
                Attack,
                Mini,
                BossMini,
                AttackProjectile,
                BossProjectile,
                BonusHand,
                Boss
            )):
                i.deleteLater()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.animationTimer.paused:
            if event.button() == Qt.MouseButton.LeftButton:
                # self.scoreItem.reduce()
                # self.screenFaderItem.alpha = 255
                # self.screenFaderItem.fadeFromBlack(10, 1)
                self.handCursor.swat()
            elif event.button() == Qt.MouseButton.RightButton:
                self.gameState.pauseGame(event.scenePos().toPoint())
            
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        self.handCursor.setPos(event.scenePos().toPoint())
        self.pauseScreen.setHandPos(event.scenePos().toPoint())
        
        self.lastPos = event.scenePos().toPoint()
        
        return super().mouseMoveEvent(event)