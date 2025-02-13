from PySide6.QtCore import QPoint
from PySide6.QtGui import QBrush, QColor, QPixmap, Qt
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsTextItem)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.gnat.animation import (AnimatedGraphicsItem, Animation,
                                AnimationTimer, loadAnimations)


class GnatAttackHand(AnimatedGraphicsItem):
    INVINCIBLE_TIME = 180
    
    def __init__(self, animationTimer: AnimationTimer):
        animations = loadAnimations(common.absolutePath("assets/gnat/animations/hand.json"))
        
        super().__init__(animationTimer, QPixmap(":/gnat/spritesheets/hand.png"), animations)
        self.setZValue(common.GNATZVALUES.HAND)
        
        self.play(self.getAnimation("idle"))
        
        self.respawnInvincible = 180
        self.flash = True
        
    def onNonLoopingAnimationEnd(self, last: Animation):
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