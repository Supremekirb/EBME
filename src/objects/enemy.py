import math

# Qt subclasses for better organisation and control
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPixmap
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsSimpleTextItem)

import src.misc.common as common
from src.misc.coords import EBCoords

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
    colours = []
    def __init__(self, groupID: int, flag: int, colour: tuple|None, 
                 subgroup1: dict, subgroup2: dict, subgroup1rate = int, subgroup2rate = int):
        self.groupID = groupID
        self.flag = flag
        self.subGroup1 = subgroup1
        self.subGroup2 = subgroup2
        self.subGroup1Rate = subgroup1rate
        self.subGroup2Rate = subgroup2rate
        
        if colour == None:
            self.colour = EnemyMapGroup.colourGen(self.groupID)
        else:
            self.colour = colour

        EnemyMapGroup.colours.append(EnemyMapGroup.colourGen(self.groupID))

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

# BUG Known issue: sometimes these things show up as black rectangles. A possible fix is to override show and hide.
class MapEditorEnemyTile(QGraphicsRectItem):
    EnemyTilesShown = True
    instances = []
    brushes = {}

    def __init__(self, coords: EBCoords):
        super().__init__()
        MapEditorEnemyTile.instances.append(self)

        self.setPos(coords.x, coords.y)
        self.setZValue(common.MAPZVALUES.ENEMY)

        self.setRect(0, 0, 64, 64)
        # self.setOpacity(0.7)
        self.setBrush(BLACKBRUSH)
        
        self.enemyGroup = 0
        
        self.sprites1: list[QGraphicsPixmapItem] = []
        self.sprites2: list[QGraphicsPixmapItem] = []
        
        self.valuesBg = QGraphicsRectItem(0, 0, 64, 24, self)
        self.valuesBg.setOpacity(0.5)
        self.valuesBg.setBrush(BLACKBRUSH)
        self.valuesBg.setPen(Qt.PenStyle.NoPen)

        self.numShadow = QGraphicsSimpleTextItem(self)
        self.num = QGraphicsSimpleTextItem(self)

        self.flagShadow = QGraphicsSimpleTextItem(self)
        self.flag = QGraphicsSimpleTextItem(self)

        self.line = QGraphicsLineItem(self)
        self.lineShadow = QGraphicsLineItem(self)

        self.probability1Shadow = QGraphicsSimpleTextItem(self)
        self.probability1 = QGraphicsSimpleTextItem(self)
        self.probability2Shadow = QGraphicsSimpleTextItem(self)
        self.probability2 = QGraphicsSimpleTextItem(self)

        self.num.setFont("EBMain")
        self.numShadow.setFont("EBMain")

        self.flag.setFont("EBMain")
        self.flagShadow.setFont("EBMain")

        self.probability1.setFont("EBMain")
        self.probability1Shadow.setFont("EBMain")
        self.probability2.setFont("EBMain")
        self.probability2Shadow.setFont("EBMain")

        self.num.setBrush(WHITEBRUSH)
        self.flag.setBrush(WHITEBRUSH)
        self.probability1.setBrush(WHITEBRUSH)
        self.probability2.setBrush(WHITEBRUSH)
        self.line.setPen(WHITEPEN)
        self.lineShadow.setPen(BLACKPEN)

        self.numShadow.setPos(3, 3)
        self.num.setPos(2, 2)

        self.flag.setPos(32, 2)
        self.flagShadow.setPos(33, 3)

        self.line.setLine(1.5, 13.5, 61.5, 13.5) # .5 makes the line stay on the pixels. weird...
        self.lineShadow.setLine(2.5, 14.5, 62.5, 14.5)

        self.probability1Shadow.setPos(6, 15)
        self.probability1.setPos(5, 14)
        self.probability2Shadow.setPos(33, 15)
        self.probability2.setPos(32, 14)
        
        self.setPen(Qt.PenStyle.NoPen)

        if not MapEditorEnemyTile.EnemyTilesShown:
            self.hide()
        
    def setGroup(self, group: int):
        self.numShadow.setText(str(group).zfill(3))
        self.num.setText(str(group).zfill(3))
        self.enemyGroup = group

        if group == 0:
            self.setBrush(Qt.GlobalColor.transparent)
            self.valuesBg.hide()
            self.num.hide()
            self.numShadow.hide()
            self.flag.hide()
            self.flagShadow.hide()
            self.probability1.hide()
            self.probability1Shadow.hide()
            self.probability2.hide()
            self.probability2Shadow.hide()
            self.line.hide()
            self.lineShadow.hide()
            for i in self.sprites1:
                i.hide()
            for i in self.sprites2:
                i.hide()
        else:
            self.valuesBg.show()
            self.num.show()
            self.numShadow.show()
            self.flag.show()
            self.flagShadow.show()
            self.probability1.show()
            self.probability1Shadow.show()
            self.probability2.show()
            self.probability2Shadow.show()
            self.line.show()
            self.lineShadow.show()
            for i in self.sprites1:
                i.show()
            for i in self.sprites2:
                i.show()

            colour = EnemyMapGroup.colours[group]
            MapEditorEnemyTile.brushes[group] = QBrush(QColor(colour[0], colour[1], colour[2], 178))
            
            self.setBrush(MapEditorEnemyTile.brushes[group])


    def setFlag(self, flag: int):
        self.flagShadow.setText(str(flag))
        self.flag.setText(str(flag))


    def setProbability1(self, probability: int):
        self.probability1.setText(f"{probability}%")
        self.probability1Shadow.setText(f"{probability}%")

    def setProbability2(self, probability: int):
        self.probability2.setText(f"{probability}%")
        self.probability2Shadow.setText(f"{probability}%")

    def setSprites1(self, sprites: tuple[QPixmap]):
        for i in self.sprites1:
            self.scene().removeItem(i)
        self.sprites1 = []
        
        if len(sprites) > 0:
            distribution = 42//(len(sprites))

            for i, sprite in reversed(list(enumerate(sprites))):
                item = QGraphicsPixmapItem(sprite, self)
                item.setOffset(-sprite.width()/2, -sprite.height())
                item.setPos(16, 64-(distribution*i))
                item.setZValue(-1)
                self.sprites1.append(item)


    def setSprites2(self, sprites: tuple[QPixmap]):
        for i in self.sprites2:
            self.scene().removeItem(i)
        self.sprites2 = []

        if len(sprites) > 0:
            distribution = 42//(len(sprites))

            for i, sprite in reversed(list(enumerate(sprites))):
                item = QGraphicsPixmapItem(sprite, self)
                item.setOffset(-sprite.width()/2, -sprite.height())
                item.setPos(48, 64-(distribution*i))
                item.setZValue(-1)
                self.sprites2.append(item)

    @classmethod
    def hideEnemyTiles(cls):
        MapEditorEnemyTile.EnemyTilesShown = False
        for i in cls.instances:
            i.hide()

    @classmethod
    def showEnemyTiles(cls):
        MapEditorEnemyTile.EnemyTilesShown = True
        for i in cls.instances:
            if i.enemyGroup == 0:
                i.setBrush(Qt.GlobalColor.transparent)
                i.valuesBg.hide()
                i.num.hide()
                i.numShadow.hide()
                i.flag.hide()
                i.flagShadow.hide()
                i.probability1.hide()
                i.probability1Shadow.hide()
                i.probability2.hide()
                i.probability2Shadow.hide()
                i.line.hide()
                i.lineShadow.hide()
                for j in i.sprites1:
                    j.hide()
                for j in i.sprites2:
                    j.hide()
            else: i.show()