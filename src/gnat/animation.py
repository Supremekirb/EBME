import json

from PySide6.QtCore import QObject, QPoint, QRect, QRectF, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPixmap, Qt
from PySide6.QtWidgets import (QGraphicsObject, QGraphicsPixmapItem,
                               QGraphicsScene, QGraphicsTextItem,
                               QStyleOptionGraphicsItem, QWidget)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData


def loadAnimations(path: str):
    def frameFromName(frames: list[SpriteFrame], name: str):
        for i in frames:
            if i.name == name:
                return i
        else:
            raise ValueError(f"Frame '{name}' not found!")
    
    with open(path) as file:
        data = json.load(file)
        
        frames: list[SpriteFrame] = []
        for name, bounds in data["frames"].items():
            rect = QRect(*bounds[:4])
            offset = QPoint(*bounds[-2:])
            frames.append(SpriteFrame(name, rect, offset))
        
        animations: list[Animation] = []
        for name, anim in data["animations"].items():
            animFrames = []
            for frame in anim["frames"]:
                animFrames.append(AnimationFrame(frameFromName(frames, frame["name"]), frame["duration"]))
            animations.append(Animation(name, animFrames, anim["loop"]))
        
        return animations
                

class AnimationTimer(QObject):
    tick = Signal(float)
    def __init__(self, tickrate = 16):
        super().__init__()
        self.timer = QTimer()
        self.timer.setInterval(tickrate)
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(lambda: self.tick.emit(tickrate))
        self.timer.start()
        
        self.paused = False
    
    def pause(self):
        self.timer.stop()
        self.paused = True
    
    def resume(self):
        self.timer.start()
        self.paused = False
        

class SpriteFrame:
    def __init__(self, name: str, rect: QRect, offset: QPoint = QPoint(0, 0)):
        self.name = name
        self.rect = rect
        self.offset = offset
        
class AnimationFrame:
    def __init__(self, frame: SpriteFrame, duration: int):
        self.frame = frame
        self.duration = duration
        
class Animation:
    def __init__(self, name: str, frames: list[AnimationFrame], loop: int):
        self.name = name
        self.frames = frames
        self.loop = loop
        
    
class AnimatedGraphicsItem(QGraphicsObject):
    def __init__(self, animationTimer: AnimationTimer, spritesheet: QPixmap, animations: list[Animation]):
        animationTimer.tick.connect(self.tickAnimation)
        
        self.animations = animations
        self.spritesheet = spritesheet.toImage()
        
        self.frameIndex: int = 0
        self.frameTime: int = 0
        
        self.currentAnimation: Animation|None = None
        self.currentSpriteFrame: SpriteFrame|None = None
        
        self.colorR = 0
        
        super().__init__()
        
    def onNonLoopingAnimationEnd(self, last: Animation):
        ... # virtual
    
    def getAnimation(self, name: str) -> Animation|None:
        for i in self.animations:
            if i.name == name:
                return i
        
        
    def play(self, animation: Animation|None):
        self.currentAnimation = animation
        self.frameIndex = 0
        self.frameTime = 0
        if animation:
            self.currentSpriteFrame = animation.frames[0].frame
        else:
            self.currentSpriteFrame = None


    def tickAnimation(self):
        if self.currentAnimation:
            self.frameTime += 1
            try:
                frame = self.currentAnimation.frames[self.frameIndex]
                # increment frame time 
                if self.frameTime > frame.duration:
                    # increment frame index
                    self.frameTime = 0
                    self.frameIndex += 1
                    
                    # looping animation logic
                    # use == instead of >= so onNonLoopingAnimationEnd does not
                    # get called constantly
                    if self.frameIndex == len(self.currentAnimation.frames):
                        if self.currentAnimation.loop == -1:
                            return self.onNonLoopingAnimationEnd(self.currentAnimation)
                        else:
                            self.frameIndex = self.currentAnimation.loop
                        
                    self.currentSpriteFrame = self.currentAnimation.frames[self.frameIndex].frame
                    try:
                        self.prepareGeometryChange() # this is necessary. See documentation
                    except RuntimeError:
                        # this happens bc of something to do with the internal object
                        # being deleted, and then we call this afterwards...
                        # there was another issue which I couldn't figure out where
                        # the entire program would just crash with no error and
                        # the random tinkering I did to fix it wound up throwing
                        # this error a bunch instead. Better than a crash...
                        pass 
            except IndexError:
                    raise
                
                
    def paint(self, painter: QPainter, style: QStyleOptionGraphicsItem, widget: QWidget):
        if self.currentSpriteFrame:
            painter.drawImage(self.currentSpriteFrame.offset,
                              self.spritesheet,
                              self.currentSpriteFrame.rect)
            
            # painter.setBrush(Qt.BrushStyle.NoBrush)
            # painter.setPen(Qt.GlobalColor.red)
            # painter.drawRect(self.boundingRect())
            
    def boundingRect(self):
        if self.currentSpriteFrame:
            offsetX, offsetY = self.currentSpriteFrame.offset.toTuple()
            return QRectF(0+offsetX, 0+offsetY, self.currentSpriteFrame.rect.width(), self.currentSpriteFrame.rect.height())
        else:
            return QRectF(0, 0, 1, 1)