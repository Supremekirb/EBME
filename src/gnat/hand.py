from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPixmap

import src.misc.common as common
from src.gnat.animation import AnimatedGraphicsItem, Animation, loadAnimations
from src.gnat.game_state import GameState


class GnatAttackHand(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/hand.json"))
    INVINCIBLE_TIME = 180
    
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/hand.png"), GnatAttackHand.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.HAND)
        
        self.play(self.getAnimation("idle"))
        
        self.respawnInvincible = 0
        self.flash = True
        
        self.swatting = False
        self.hurting = False
        
        self.forceHidden = False
        
    def swat(self):
        if not self.swatting and not self.hurting and not self.forceHidden:
            self.swatting = True
            
            intersecting = self.scene().items(QRect(self.pos().x()-8, self.pos().y()-8, 16, 16))
            
            landedHit = False
            for i in intersecting:
                if hasattr(i, "swatted"):
                    # dont cancel a landed hit animation if something else can't be hit
                    landedHit: bool = i.swatted() or landedHit

            if landedHit:
                self.play(self.getAnimation("hit"))
            else:
                self.play(self.getAnimation("swat"))
                GameState.playSFX("swing")
                
    def hurt(self):
        if not self.hurting and self.respawnInvincible <= 0:
            self.hurting = True
            GameState.playSFX("hurt")
            self.play(self.getAnimation("hurt"))
        
    def onNonLoopingAnimationEnd(self, last: Animation):
        if last in (self.getAnimation("swat"), self.getAnimation("hit")):
            self.swatting = False
        if last == self.getAnimation("hurt"):
            self.swatting = False # in case we got hit during
            self.hurting = False
            self.respawnInvincible = GnatAttackHand.INVINCIBLE_TIME
            GameState.takeLife()
            self.setPos(GameState.getScene().lastPos)
        self.play(self.getAnimation("idle"))
        
    def setPos(self, pos: QPoint):
        if not self.hurting:
            super().setPos(QPoint(common.cap(pos.x(), 24, 232), common.cap(pos.y(), 24, 200)))
        
    def tickAnimation(self):
        if self.respawnInvincible > 0:
            self.respawnInvincible -= 1
            self.flash = not self.flash
            if not self.forceHidden:
                self.show() if self.flash else self.hide()
        elif self.respawnInvincible == 0:
            if not self.forceHidden: 
                self.show()
            self.flash = True
        
        return super().tickAnimation()