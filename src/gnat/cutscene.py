import math
from types import MethodType

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QBrush, QColor, QPixmap
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem

# getting around circular deps with this
import src.gnat.game_state
import src.misc.common as common
from src.gnat.animation import AnimatedGraphicsItem, loadAnimations
from src.gnat.scripting import Script, ScriptedAnimatedItem


class Applause(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/applause.json"))
    def __init__(self, pos: QPoint):
        super().__init__(src.gnat.game_state.GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/applause.png"), Applause.ANIMATIONS)
        
        self.play(self.getAnimation("clap"))
        self.setPos(pos)
        
        src.gnat.game_state.GameState.getScene().addItem(self)

class WinnerGnat(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/gnat.json"))
    def __init__(self):
        super().__init__(src.gnat.game_state.GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/gnat.png"), WinnerGnat.ANIMATIONS)
        self.play(self.getAnimation("fly"))
        self.setPos(72, 0)
        
        src.gnat.game_state.GameState.getScene().addItem(self)
    
    async def script(self):
        trigIncrement = math.radians(90)
         
        await self.pause(140)
        self.vy = 2
        while self.y() < 24:
            await self.pause()
            
        while trigIncrement > math.radians(-360):
            self.vx = math.cos(trigIncrement)*2
            self.vy = math.sin(trigIncrement)*2
            trigIncrement -= 0.3
            await self.pause()
            
        
        while self.x() < 91:
            self.vy = 0
            self.vx = 2
            await self.pause()
            
        while self.vy < 1:
            self.vy += 0.2
            await self.pause()
        while self.vy > 0:
            self.vy -= 0.2
            await self.pause()
        
        trigIncrement = 0
        while self.vy < 1.8:
            self.vx = math.cos(trigIncrement)*2
            self.vy = math.sin(trigIncrement)*2
            trigIncrement -= 0.2
            await self.pause()
        
        self.vx = 1.8
        self.vy = 2
        
        while self.vx > 0:
            self.vx -= 0.1
            await self.pause()
        self.vx = 0
        
        while self.y() < 90:
            await self.pause()
        
        self.vx = 0
        self.vy = 0
        
        await self.pause(80)
        self.vy = -4
        
        while self.y() > 0:
            await self.pause()
        
        self.deleteLater()

class Koopa(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/koopa.json"))
    def __init__(self):
        super().__init__(src.gnat.game_state.GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/koopa.png"), Koopa.ANIMATIONS)
        
        self.play(self.getAnimation("walk"))
        self.setPos(240, 112)
        
        src.gnat.game_state.GameState.getScene().addItem(self)
        
    async def script(self):
        await self.pause(275+12)
        self.vx = -2
        while self.x() > -16:
            await self.pause()
        self.deleteLater()

class TheOtherGuys(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/bobomb_galoomba_spiny.json"))
    def __init__(self, who: str, where: int):
        super().__init__(src.gnat.game_state.GameState.getAnimationTimer(), QPixmap(f":/gnat/spritesheets/{who}.png"), TheOtherGuys.ANIMATIONS)
        
        self.play(self.getAnimation("walk"))
        self.setPos(240, 128)
        self.where = where
        
        src.gnat.game_state.GameState.getScene().addItem(self)
    
    async def script(self):
        await self.pause(275+(12*self.where)+12)
        self.vx = -2
        while self.x() > 0:
            await self.pause()
        self.deleteLater()
        
        
class Luigi(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/luigi.json"))
    def __init__(self, final: bool):
        super().__init__(src.gnat.game_state.GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/luigi.png"), Luigi.ANIMATIONS)
        
        self.final = final
        self.play(self.getAnimation("walk"))
        
        self.setPos(240, 120)
        
        state = src.gnat.game_state.GameState
        state.getScene().addItem(self)
    
    async def script(self):
        if not self.final:
            await self.pause(275)
            self.vx = -2
            
            while self.x() > 144:
                await self.pause()
            
            self.play(self.getAnimation("jump"))
            self.vy = -5
            self.vx = -4
            await self.pause()
            self.vx = -2
            while self.y() < 120:
                self.vy += 0.6
                await self.pause()
            self.vy = 0
            self.setY(120)
            
            self.play(self.getAnimation("walk"))
            while self.x() > 0:
                await self.pause()
            
            self.deleteLater()
        
        else: # special final anim
            await self.pause(170)
            self.vx = -2
            
            while self.x() > 144:
                await self.pause()
            
            self.play(self.getAnimation("jump"))
            self.vy = -5
            self.vx = -4
            await self.pause()
            self.vx = -2
            while self.y() < 120:
                self.vy += 0.6
                await self.pause()
            self.vy = 0
            self.setY(120)
            
            self.play(self.getAnimation("turn"))
            while self.vx < 0:
                self.vx += 0.3
                await self.pause()
                
            self.play(self.getAnimation("walkr"))
            while self.vx < 2:
                self.vx += 0.3
                await self.pause()
            self.vx = 2
            
            while self.x() < 119:
                await self.pause()
            
            self.vx = 0
            self.play(self.getAnimation("facer"))
            await self.pause(18)
            self.play(self.getAnimation("peace"))
        
        
class GameOverCutsceneHandler(Script):
    def __init__(self, callback: MethodType = lambda: ..., *callback_args):
        super().__init__()
        
        self.callback = callback
        self.callback_args = callback_args
    
    async def script(self):
        scene = src.gnat.game_state.GameState.getScene()
        fader = scene.screenFaderItem
        display = scene.roundDisplayItem
        
        scene.livesItem.hide()
        scene.handCursor.hide()
        scene.handCursor.forceHidden = True
        
        src.gnat.game_state.GameState.playBGM("gameover")
        
        display.levelNum.hide()
        display.levelText.setPlainText("GAME OVER")
        display.show()
        
        await self.pause(540)
        fader.fadeToBlack(10, 1)
        await fader.waitForFade()
        
        display.hide()
        display.levelNum.show()
        display.setPos(84, 84)
        
        scene.livesItem.show()
        scene.handCursor.show()
        scene.handCursor.forceHidden = False
        scene.handCursor.respawnInvincible = 0


        await self.pause(30) # breather
        
        if len(self.callback_args) > 0:
            self.callback(*self.callback_args)
        else:
            self.callback()
    

class CongratulationsCutsceneHandler(Script):
    def __init__(self, level: int, final: bool = False, callback: MethodType = lambda: ..., *callback_args):
        super().__init__()
        
        self.level = level
        self.final = final
        self.callback = callback
        self.callback_args = callback_args
        
    async def script(self):
        scene = src.gnat.game_state.GameState.getScene()
        fader = scene.screenFaderItem
        display = scene.roundDisplayItem
        
        src.gnat.game_state.GameState.getScene().clearEnemies()
        
        scene.livesItem.hide()
        scene.handCursor.hide()
        scene.handCursor.forceHidden = True
        
        applause1 = Applause(QPoint(39, 160))
        applause2 = Applause(QPoint(87, 160))
        applause3 = Applause(QPoint(135, 160))
        applause4 = Applause(QPoint(183, 160))
        luigi = Luigi(self.final)
        
        if not self.final:
            if self.level > 1:
                koopa = Koopa()
            if self.level > 2:
                galoomba = TheOtherGuys("galoomba", 1)
                spiny = TheOtherGuys("spiny", 2)
                bobomb = TheOtherGuys("bobomb", 3)
            
            gnat = WinnerGnat()
            
        
        if self.final:
            src.gnat.game_state.GameState.playBGM("thankyou")
        else:
            src.gnat.game_state.GameState.playBGM("congratulations")
        
        display.levelNum.hide()
        display.setPos(60, 68)
        display.levelText.setPlainText("CONGRATULATIONS!")
        display.show()
        
        await self.pause(540)
        
        if self.final:
            while True:
                await self.pause()
        
        fader.fadeToBlack(10, 1)
        await fader.waitForFade()
        
        display.hide()
        display.levelNum.show()
        display.setPos(84, 84)
        
        scene.livesItem.show()
        scene.handCursor.show()
        scene.handCursor.forceHidden = False
        scene.handCursor.respawnInvincible = 0
        
        applause1.deleteLater()
        applause2.deleteLater()
        applause3.deleteLater()
        applause4.deleteLater()
        # luigi.deleteLater()
        
        await self.pause(30) # breather
        
        if len(self.callback_args) > 0:
            self.callback(*self.callback_args)
        else:
            self.callback()


class RoundStartCutsceneHandler(Script):
    def __init__(self, levelText: str = "LEVEL", levelNum: str = "1", callback: MethodType = lambda: ..., *callback_args):
        super().__init__()
        
        self.levelText = levelText
        self.levelNum = levelNum
        self.callback = callback
        self.callback_args = callback_args
        
    async def script(self):
        fader = src.gnat.game_state.GameState.getScene().screenFaderItem
        display = src.gnat.game_state.GameState.getScene().roundDisplayItem
        
        display.hide()
        display.levelNum.setPlainText(self.levelNum)
        display.levelText.setPlainText(self.levelText)
        
        fader.fadeFromBlack(10, 1)
        src.gnat.game_state.GameState.setLevelBackground()
        await fader.waitForFade()
        
        display.show()
        await self.pause(60)
        display.hide()
        
        src.gnat.game_state.GameState.playCurrentLevelBGM()
        
        await self.pause(120)
        
        if len(self.callback_args) > 0:
            self.callback(*self.callback_args)
        else:
            self.callback()

# just inherit textitem here
# so i dont have to write a paint() method
# because i am tired
class RoundStartDisplay(QGraphicsTextItem, Script):
    def __init__(self):
        super().__init__()
        
        self.setPos(84, 84)
        self.setZValue(common.GNATZVALUES.TEXT)
        
        self.levelText = QGraphicsTextItem("LEVEL", self)
        self.levelText.setDefaultTextColor(Qt.GlobalColor.black)
        self.levelText.setFont("Mario Paint Letters")
        
        self.levelNum = QGraphicsTextItem(self)
        self.levelNum.setDefaultTextColor(Qt.GlobalColor.black)
        self.levelNum.setFont("Mario Paint Numbers")
        self.levelNum.setPos(56, 0)
        
        self.hide()
        
        self._shown = False
        
        self.callback: MethodType = None
        self.callback_args: tuple = (None,)
        
    def displayLevelWithCallback(self, level: int, callback: MethodType, *callback_args):
        self._shown = True
        self.levelNum.setPlainText(str(level))
        self.callback = callback
        self.callback_args = callback_args
        
    async def script(self):
        while True:
            while not self._shown:
                await self.pause()
            
            # displaying
            self.show()
            await self.pause(180)
            
            self.levelText.hide()
            self.levelNum.hide()
            await self.pause(60)
            
            if self.callback:
                if self.callback_args:            
                    self.callback(*self.callback_args)
                else:
                    self.callback()
            
            self.hide()
            self._shown = False
            
class ScreenFader(QGraphicsRectItem, Script):
    def __init__(self):
        super().__init__()
        self.setPos(0, 0)
        self.setRect(0, 0, 256, 224)
        self.setZValue(common.GNATZVALUES.SCREENFX)
        
        self.maskBrush = QBrush(QColor(0, 0, 0, 0))
        self.alpha = 0
        self.targetAlpha = 0
        self.delta = 0
        self.pauseTime = 1
        
        self.setBrush(self.maskBrush)
        
    def setAlpha(self, alpha):
        self.alpha = alpha
        self.targetAlpha = alpha
        self.maskBrush.setColor(QColor(0, 0, 0, self.alpha))
        self.setBrush(self.maskBrush)
    
    def fadeToBlack(self, delta=1, pause=1):
        self.alpha = 0
        self.targetAlpha = 255
        self.delta = delta
        self.pauseTime = pause
    
    def fadeFromBlack(self, delta=1, pause=1):
        self.alpha = 255
        self.targetAlpha = 0
        self.delta = delta
        self.pauseTime = pause
        
    async def waitForFade(self):
        while self.targetAlpha != self.alpha:
            await self.pause()
    
    async def script(self):
        while True:
            if self.alpha < self.targetAlpha:
                self.alpha += self.delta
            elif self.alpha > self.targetAlpha:
                self.alpha -= self.delta

            if self.alpha > 255:
                self.alpha = 255
            if self.targetAlpha > 255:
                self.targetAlpha = 255
            if self.alpha < 0:
                self.alpha = 0
            if self.targetAlpha < 0:
                self.targetAlpha = 0
            
            self.maskBrush.setColor(QColor(0, 0, 0, self.alpha))
            self.setBrush(self.maskBrush)
            
            await self.pause(self.pauseTime)