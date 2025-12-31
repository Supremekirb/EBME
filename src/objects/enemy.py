import math
from typing import TYPE_CHECKING

from PIL import ImageQt
# Qt subclasses for better organisation and control
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsLineItem,
                               QGraphicsRectItem)

import src.misc.common as common
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.coilsnake.project_data import ProjectData
    


WHITEBRUSH = QBrush(Qt.white)
BLACKBRUSH = QBrush(Qt.black)
WHITEPEN = QPen(Qt.white)
BLACKPEN = QPen(Qt.black)

class EnemyTile:
    """Enemy tiles on the map"""
    def __init__(self, coords: EBCoords, groupID: int):
        self.coords = coords
        self.groupID = groupID
        self.isPlaced = False

class EnemyMapGroup:
    """Enemy tile groups"""
    colours = {}
    def __init__(self, groupID: int, flag: int, colour: tuple|None, 
                 subgroup1: dict, subgroup2: dict, subgroup1rate = int, subgroup2rate = int):
        self.groupID = groupID
        self.flag = flag
        self.subGroup1 = subgroup1
        self.subGroup2 = subgroup2
        self.subGroup1Rate = subgroup1rate
        self.subGroup2Rate = subgroup2rate
        
        self.rendered: QPixmap | None = None
        
        if colour == None:
            self.colour = EnemyMapGroup.colourGen(self.groupID)
        else:
            self.colour = colour

        EnemyMapGroup.colours[self.groupID] = EnemyMapGroup.colourGen(self.groupID)

    def render(self, projectData: "ProjectData"):
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor.fromRgb(self.colour[0], self.colour[1], self.colour[2], 178))
        painter = QPainter()
        pixmap.initPainter(painter)
        painter.begin(pixmap)
        
        
        # Enemy overworld sprites
        sprites1: list[QPixmap] = []
        sprites2: list[QPixmap] = []
        for i in self.subGroup1.values():
            for e in projectData.enemyGroups[i["Enemy Group"]].enemies:
                spr = projectData.getSprite(projectData.enemySprites[e["Enemy"]])
                sprites1.append(QPixmap.fromImage(ImageQt.ImageQt(spr.renderFacingImg(4))))
        for i in self.subGroup2.values():
            for e in projectData.enemyGroups[i["Enemy Group"]].enemies:
                spr = projectData.getSprite(projectData.enemySprites[e["Enemy"]])
                sprites2.append(QPixmap.fromImage(ImageQt.ImageQt(spr.renderFacingImg(4))))
        
        if len(sprites1) > 0:
            distribution = 42//len(sprites1)
            for i, sprite in reversed(list(enumerate(sprites1))):
                painter.drawPixmap(
                    16 - sprite.width()//2, 64-(distribution*i) - sprite.height(),
                    sprite
                )
        if len(sprites2) > 0:
            distribution = 42//len(sprites2)
            for i, sprite in reversed(list(enumerate(sprites2))):
                painter.drawPixmap(
                    48 - sprite.width()//2, 64-(distribution*i) - sprite.height(),
                    sprite
                )
        
        # Values background
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setOpacity(0.5)
        painter.drawRect(0, 0, 64, 24)
        
        painter.setOpacity(1)
        
        # Horizontal line
        painter.setBrush(Qt.BrushStyle.NoBrush)
        #    - Shadow
        painter.setPen(Qt.GlobalColor.black)
        painter.drawLine(3.5, 14.5, 62.5, 14.5)
        #    - Line
        painter.setPen(Qt.GlobalColor.white)
        painter.drawLine(2.5, 13.5, 61.5, 13.5)
        
        painter.setFont("EBMain")
        font = painter.font()
        font.setPixelSize(16)
        font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
        painter.setFont(font)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        
        # Group ID
        #    - Shadow
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(3, 14, str(self.groupID).zfill(3))
        #    - Text
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(2, 13, str(self.groupID).zfill(3))
        
        # Flag
        if self.flag >= 0x8000:
            x = 29
            text = f"!{self.flag-0x8000}"
        else:
            x = 32
            text = str(self.flag)
        #    - Shadow
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(x+1, 14, text)
        #    - Text
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(x, 13, text)
        
        # Probability 1
        #    - Shadow
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(6, 26, str(self.subGroup1Rate) + "%")
        #    - Text
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(5, 25, str(self.subGroup1Rate) + "%")
        
        # Probability 2
        #    - Shadow
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(33, 26, str(self.subGroup2Rate) + "%")
        #    - Text
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(32, 25, str(self.subGroup2Rate) + "%")
        
        painter.end()
        
        self.rendered = pixmap       
    
    @staticmethod
    def colourGen(i: int) -> tuple[int, int, int]:
        """Generate a unique colour.

        Args:
            i (int): "seed" (should be group ID)

        Returns:
            tuple[int, int, int]: R, G, B
        """
        # https://docs.oracle.com/javase/8/docs/api/java/awt/Color.html
        # https://github.com/tolmar/EbProjectEditor/blob/bbd990b01b69db6bcb70ded0f57c317f34393c8d/src/ebhack/MapDisplay.java#L478
        # produces different results though
        colour = int(math.e * 0x100000 * i) & 0x9F9F9F # last & controls brightness
        colourR = (colour & 0xFF0000) >> 16 # bits 16-23
        colourG = (colour & 0x00FF00) >> 8 # bits 8-15
        colourB = (colour & 0x0000FF) # bits 0-7 
        return (colourR, colourG, colourB)

class EnemyGroup:
    """Enemy data groups"""
    def __init__(self, groupID: int, bg1: int, bg2: int, enemies: list, fearFlag: int, fearMode: str, letterboxSize: int):
        self.groupID = groupID
        self.bg1 = bg1
        self.bg2 = bg2
        self.enemies = enemies
        self.fearFlag = fearFlag
        self.fearMode = fearMode
        self.letterboxSize = letterboxSize


class EnemySpawnLines(QGraphicsRectItem):
    def __init__(self, parent: QGraphicsItem|None = None):
        super().__init__(parent)
        self.setZValue(common.MAPZVALUES.ENEMY)
        pen = QPen(Qt.GlobalColor.yellow, 4)
        bgPen = QPen(Qt.GlobalColor.black, 6)
        
        self.setRect(0, 0, 64, 64)
        self.setPen(bgPen)
        
        self.FGRect = QGraphicsRectItem(0, 0, 64, 64, self)
        self.FGRect.setPen(pen)
        
        self.BGTopLine = QGraphicsLineItem(-64, -192, 256, -192, self)
        self.BGTopLine.setPen(bgPen)
        self.BGRightLine = QGraphicsLineItem(192, -64, 192, 256, self)
        self.BGRightLine.setPen(bgPen)
        self.BGBottomLine = QGraphicsLineItem(-64, 192, 256, 192, self)
        self.BGBottomLine.setPen(bgPen)
        self.BGLeftLine = QGraphicsLineItem(-192, -64, -192, 256, self)
        self.BGLeftLine.setPen(bgPen)
        
        self.topLine = QGraphicsLineItem(-64, -192, 256, -192, self)
        self.topLine.setPen(pen)
        self.rightLine = QGraphicsLineItem(192, -64, 192, 256, self)
        self.rightLine.setPen(pen)
        self.bottomLine = QGraphicsLineItem(-64, 192, 256, 192, self)
        self.bottomLine.setPen(pen)
        self.leftLine = QGraphicsLineItem(-192, -64, -192, 256, self)
        self.leftLine.setPen(pen)
        