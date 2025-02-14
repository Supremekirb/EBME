from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QBrush, QColor, QPixmap, Qt
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsTextItem)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.gnat.animation import (AnimatedGraphicsItem, Animation,
                                AnimationTimer, loadAnimations)


class GnatAttackHand(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/hand.json"))
    INVINCIBLE_TIME = 180
    
    def __init__(self, animationTimer: AnimationTimer):
        
        
        super().__init__(animationTimer, QPixmap(":/gnat/spritesheets/hand.png"), GnatAttackHand.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.HAND)
        
        self.play(self.getAnimation("idle"))
        
        self.respawnInvincible = 0
        self.flash = True
        
        self.swatting = False
        
    def swat(self, pos: QPoint):
        if not self.swatting:
            self.swatting = True
            
            intersecting = self.scene().items(QRect(pos.x(), pos.y(), 16, 16))
            
            landedHit = False
            for i in intersecting:
                if hasattr(i, "swatted"):
                    # dont cancel a landed hit animation if something else can't be hit
                    landedHit: bool = i.swatted() or landedHit

            if landedHit:
                self.play(self.getAnimation("hit"))
            else:
                self.play(self.getAnimation("swat"))
        
    def onNonLoopingAnimationEnd(self, last: Animation):
        if last in (self.getAnimation("swat"), self.getAnimation("hit")):
            self.swatting = False
        self.play(self.getAnimation("idle"))
        
    def setPos(self, pos: QPoint):
        super().setPos(QPoint(common.cap(pos.x(), 16, 224), common.cap(pos.y(), 16, 192)))
        
    def tickAnimation(self):
        if self.respawnInvincible > 0:
            self.respawnInvincible -= 1
            self.flash = not self.flash
            self.show() if self.flash else self.hide()
        elif self.respawnInvincible == 0:
            self.show()
            self.flash = True
        
        return super().tickAnimation()