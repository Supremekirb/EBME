from types import MethodType

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem

# getting around circular deps with this
import src.gnat.game_state
import src.misc.common as common
from src.gnat.scripting import Script


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
        await fader.waitForFade()
        
        display.show()
        await self.pause(120)
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
            if self.alpha > self.targetAlpha:
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