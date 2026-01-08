import copy
import json
import logging
import math
import sys
import traceback
from math import ceil
from typing import TYPE_CHECKING
from uuid import UUID

import numpy
from ordered_set import OrderedSet
from PySide6.QtCore import QPoint, QRect, QRectF, QSettings, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QKeySequence, QPainter,
                           QPainterPath, QPen, QPixmap, QPolygon, QUndoCommand)
from PySide6.QtWidgets import (QApplication, QGraphicsLineItem,
                               QGraphicsPathItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsScene,
                               QGraphicsSceneContextMenuEvent,
                               QGraphicsSceneMouseEvent, QInputDialog, QMenu,
                               QMessageBox, QProgressDialog)

import src.misc.common as common
import src.misc.icons as icons
import src.objects.trigger as trigger
from src.actions.changes_actions import (ActionAddMapChangeEvent,
                                         ActionAddTileChange,
                                         ActionChangeMapChangeEvent,
                                         ActionChangeTileChange,
                                         ActionMoveMapChangeEvent,
                                         ActionMoveTileChange,
                                         ActionRemoveMapChangeEvent,
                                         ActionRemoveTileChange)
from src.actions.enemy_actions import (ActionPlaceEnemyTile,
                                       ActionUpdateEnemyMapGroup)
from src.actions.fts_actions import (ActionAddPalette, ActionChangeCollision,
                                     ActionRemovePalette)
from src.actions.hotspot_actions import (ActionChangeHotspotColour,
                                         ActionChangeHotspotComment,
                                         ActionChangeHotspotLocation)
from src.actions.misc_actions import ActionReplaceTileset
from src.actions.npc_actions import (ActionAddNPCInstance,
                                     ActionChangeNPCInstance, ActionCreateNPC,
                                     ActionDeleteNPCInstance,
                                     ActionMoveNPCInstance, ActionUpdateNPC)
from src.actions.sector_actions import (ActionAddSectorUserDataField,
                                        ActionChangeSectorAttributes,
                                        ActionImportSectorUserData,
                                        ActionRemoveSectorUserDataField)
from src.actions.tile_actions import ActionPlaceTile, ActionSwapTiles
from src.actions.trigger_actions import (ActionAddTrigger, ActionDeleteTrigger,
                                         ActionMoveTrigger,
                                         ActionUpdateTrigger)
from src.actions.warp_actions import (ActionMoveTeleport, ActionMoveWarp,
                                      ActionUpdateTeleport, ActionUpdateWarp)
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.dialogues import ClearDialog
from src.objects.changes import MapChangeEvent
from src.objects.enemy import EnemySpawnLines
from src.objects.hotspot import MapEditorHotspot
from src.objects.npc import NPC, MapEditorNPC, NPCInstance
from src.objects.sector import Sector
from src.objects.sprite import Sprite
from src.objects.tile import MapTile
from src.objects.warp import MapEditorWarp

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState


class MapEditorScene(QGraphicsScene):
    PREVIEWNPCMAXSAMPLES = 4 # higher = less jittering on diagonals, but more delay. 4 seems to work nicely
    PREVIEWNPCANIMDELAY = 7 # how many mouse-move inputs before switching animation frame
    def __init__(self, parent: "MapEditor", state: "MapEditorState", data: ProjectData):
        super().__init__(parent)

        self.projectData = data
        self.state = state       

        self.undoStack = self.parent().parent().undoStack
        self.undoStack.undone.connect(self.onAction)
        self.undoStack.redone.connect(self.onAction)
        self.undoStack.pushed.connect(self.onAction)

        self.setSceneRect(-128, -128, common.EBMAPWIDTH+256, common.EBMAPHEIGHT+256)

        self.grid = QGraphicsRectItem(0, 0, common.EBMAPWIDTH, common.EBMAPHEIGHT)
        self.grid.setBrush(QBrush(QPixmap(":/grids/32grid0.png")))
        self.grid.setZValue(common.MAPZVALUES.GRID)
        self.addItem(self.grid)
        self.grid.hide()
        self._currentGrid = 0

        path = QPainterPath()
        path.addRect(QRect(0, 0, 256, 128))
        self.sectorSelect = QGraphicsPathItem(path)
        self.sectorSelect.setPen(QPen(Qt.GlobalColor.yellow, 1))
        self.sectorSelect.setBrush(QBrush(QColor(255, 255, 0, 0)))
        self.sectorSelect.setZValue(common.MAPZVALUES.SECTORSELECT)
        self.addItem(self.sectorSelect)
        self.sectorBrushChangeTimer = QTimer(self)
        self.sectorBrushChangeTimer.setInterval(50)
        self.sectorBrushChangeTimer.timeout.connect(self.changeSectorBrush)
        self.sectorBrushChangeTimer.start()
        
        spr = self.projectData.getSprite(self.projectData.playerSprites[common.PLAYERSPRITES.NORMAL])
        self.previewNPC = MapEditorNPC(EBCoords(), -1, UUID(int=0), spr)
        self.previewNPC.setDummy()
        self.previewNPC.setCursor(Qt.CursorShape.BlankCursor)
        self.previewNPCPositionSamples: list[EBCoords] = []
        self.previewNPCAnimTimer = self.PREVIEWNPCANIMDELAY
        self.previewNPCAnimState = 0
        self.previewNPCCurrentDir = common.DIRECTION8.down
        self.previewNPCStillTimer = QTimer()
        self.previewNPCStillTimer.setInterval(500)
        self.previewNPCStillTimer.timeout.connect(self.resetPreviewNPCAnim)
        
        self.previewNPC.setSprite(spr, common.DIRECTION8.down, 0, False)
        self.previewNPC.setCollisionBounds(8, 8) # use player's hardcoded collision
        # self.previewNPC.collisionBounds.setY(4)
        self.previewNPC.hide()
        self.addItem(self.previewNPC)
        
        self.hoverSpawnLines = EnemySpawnLines()
        self.addItem(self.hoverSpawnLines)
        self.hoverSpawnLines.hide()
        
        self.selectionChanged.connect(self.updateSelected)

        self.setBackgroundBrush(
            QBrush(QPixmap(":/ui/bg.png"))
        )

        # easier access
        self.placedNPCsByID: dict[int, list[MapEditorNPC]] = {}
        self.placedNPCsByUUID: dict[UUID, MapEditorNPC] = {}
        self.placedTriggersByUUID: dict[UUID, trigger.MapEditorTrigger] = {} 
        self.placedHotspots: list[MapEditorHotspot] = []
        self.placedWarps: list[MapEditorWarp] = []
        self.placedTeleports: list[MapEditorWarp] = []
        
        self.populateNPCs()
        self.populateTriggers()
        self.populateHotspots()
        self.populateWarps()
        
        # door destination preview
        self.doorDestShowIcon = QGraphicsPixmapItem(self.imgTriggerDest)
        self.addItem(self.doorDestShowIcon)
        self.doorDestShowIcon.setZValue(common.MAPZVALUES.DOORDESTICON)
        self.doorDestShowIcon.hide()
        
        self.doorDestShowLine = QGraphicsLineItem()
        self.addItem(self.doorDestShowLine)
        self.doorDestShowLine.setZValue(common.MAPZVALUES.DOORDESTLINE)
        self.doorDestShowLine.setPen(QPen(Qt.red, 2))
        self.doorDestShowLine.hide()
        
        # door destination set
        self.doorDestPlacer = QGraphicsPixmapItem(self.imgTriggerDest)
        self.addItem(self.doorDestPlacer)
        self.doorDestPlacer.setZValue(common.MAPZVALUES.DOORDESTICON)
        self.doorDestPlacer.hide()
        
        self.doorDestLine = QGraphicsLineItem()
        self.addItem(self.doorDestLine)
        self.doorDestLine.setPen(QPen(Qt.red, 2))
        self.doorDestLine.setZValue(common.MAPZVALUES.DOORDESTLINE)
        self.doorDestLine.hide()
        
        self.enabledMapEvents: OrderedSet[MapChangeEvent] = OrderedSet()
        self.mapEventTileMappings: dict[dict[int, int]] = {} # Tileset: [ {Before: after} ]
        
        self.dontUpdateModeNextAction = False
        """Avoid updating the current mode when pushing an action to the stack. Unset after the action is received. Won't affect undo/redo later on."""
        
        self._lastSector = self.projectData.getSector(EBCoords(0, 0))
        self._lastCoords = EBCoords(0, 0)
    
    def updateSelected(self):
        match self.state.mode:
            case common.MODEINDEX.NPC:
                self.state.currentNPCInstances = []
                for i in self.selectedItems():
                    if isinstance(i, MapEditorNPC):
                        self.state.currentNPCInstances.append(self.projectData.npcInstanceFromUUID(i.uuid))
                self.parent().sidebarNPC.fromNPCInstances()
                
            case common.MODEINDEX.TRIGGER:
                self.state.currentTriggers = []
                for i in self.selectedItems():
                    if isinstance(i, trigger.MapEditorTrigger):
                        self.state.currentTriggers.append(self.projectData.triggerFromUUID(i.uuid))
                self.parent().sidebarTrigger.fromTriggers() 
            
            case common.MODEINDEX.HOTSPOT:
                self.state.currentHotspot = None
                for i in self.selectedItems():
                    if isinstance(i, MapEditorHotspot):
                        self.state.currentHotspot = self.projectData.hotspots[i.id]
                        break       
                self.parent().sidebarHotspot.fromHotspot()
                
            case common.MODEINDEX.WARP:
                self.state.currentWarp = None
                for i in self.selectedItems():
                    if isinstance(i, MapEditorWarp):
                        if i.warpType == "warp":
                            self.state.currentWarp = self.projectData.warps[i.id]
                        else:
                            self.state.currentWarp = self.projectData.teleports[i.id]
                        break
                self.parent().sidebarWarp.fromWarp()
                    
        
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        coords = EBCoords(event.scenePos().x(), event.scenePos().y())
        restrictedCoords = EBCoords(*coords.coords())
        restrictedCoords.restrictToMap()
        self.parent().status.updateCoords(coords)
        self.hoverSpawnLines.setPos(*restrictedCoords.roundToEnemy())
        if self.state.tempMode == common.TEMPMODEINDEX.NONE:
            match self.state.mode:
                case common.MODEINDEX.TILE:
                    if event.buttons() == Qt.MouseButton.LeftButton:
                        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                            self.placeTile(coords)
                        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.pickTile(coords)
                    if event.buttons() == Qt.MouseButton.RightButton:
                        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                            self.selectSector(coords)
                        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.selectSector(coords, True, True)
                case common.MODEINDEX.SECTOR:
                    if event.buttons() == Qt.MouseButton.LeftButton:
                        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                            self.selectSector(coords)
                        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.selectSector(coords, True, True)
                case common.MODEINDEX.ENEMY:
                    if event.buttons() == Qt.MouseButton.LeftButton:
                        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                            self.placeEnemyTile(coords)
                        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.pickEnemyTile(coords)
                case common.MODEINDEX.COLLISION:
                    if event.buttons() == Qt.MouseButton.LeftButton:
                        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                            self.placeCollision(coords)
                        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.pickCollision(coords)
                case common.MODEINDEX.CHANGES:
                    if event.buttons() == Qt.MouseButton.LeftButton:
                        self.pickMapChanges(coords)
                case common.MODEINDEX.GAME:
                    if not self.state.previewLocked: # only move if we're not panning - messes with anim
                        if not (Qt.KeyboardModifier.ShiftModifier in event.modifiers() and \
                        Qt.MouseButton.LeftButton in event.buttons()) and \
                            Qt.MouseButton.MiddleButton not in event.buttons():
                            self.moveGameModeMask(coords)
        else:
            match self.state.tempMode:
                case common.TEMPMODEINDEX.IMPORTMAP:
                    self.moveImportMap(coords)
                case common.TEMPMODEINDEX.SETDOORDEST:
                    self.moveDoorDest(coords)
                            
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        coords = EBCoords(event.scenePos().x(), event.scenePos().y())
        
        if event.buttons() == Qt.MouseButton.RightButton and event.modifiers() == Qt.KeyboardModifier.AltModifier:
            if QSettings().value("personalisation/coordCopyAuto", True, type=bool):
                match self.state.mode:
                    case common.MODEINDEX.TILE | common.MODEINDEX.CHANGES:
                        toCopy = coords.coordsTile()
                    case common.MODEINDEX.SECTOR:
                        toCopy = coords.coordsSector()
                    case common.MODEINDEX.ENEMY:
                        toCopy = coords.coordsEnemy()
                    case common.MODEINDEX.NPC | common.MODEINDEX.ALL | common.MODEINDEX.GAME:
                        toCopy = coords.coords()
                    case _:
                        toCopy = coords.coordsWarp()
            else:
                toCopy = coords.coords()
            QApplication.clipboard().setText(QSettings().value
                                             ("personalisation/coordCopyStyle", r"(%X, %Y)", type=str)
                                             .replace(r'%X', str(toCopy[0]))
                                             .replace(r'%Y', str(toCopy[1])))
            
        else:
            if self.state.tempMode == common.TEMPMODEINDEX.NONE:
                match self.state.mode:
                    case common.MODEINDEX.TILE:
                        if event.buttons() == Qt.MouseButton.LeftButton:
                            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                                self.placeTile(coords)
                            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                                self.pickTile(coords)
                        if event.buttons() == Qt.MouseButton.RightButton:
                            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                                self.selectSector(coords)
                            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                                self.selectSector(coords, True)
                                
                    case common.MODEINDEX.SECTOR:
                        if event.buttons() == Qt.MouseButton.LeftButton:
                            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                                self.selectSector(coords)
                            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                                self.selectSector(coords, True)
                    
                    case common.MODEINDEX.ENEMY:
                        if event.buttons() == Qt.MouseButton.LeftButton:
                            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                                self.placeEnemyTile(coords)
                            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                                self.pickEnemyTile(coords)
                        if event.buttons() == Qt.MouseButton.RightButton:
                            if self.parent().enemyLinesAction.isChecked():
                                if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                                    enemyCoords = coords.coordsEnemy()
                                    if enemyCoords in self.state.lockedSpawnLines:
                                        self.state.lockedSpawnLines.discard(enemyCoords)
                                    else:
                                        self.state.lockedSpawnLines.add(enemyCoords)
                                    self.update()
                                if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                                    self.state.lockedSpawnLines.clear()
                                    self.update()
                    
                    case common.MODEINDEX.COLLISION:
                        if event.buttons() == Qt.MouseButton.LeftButton:
                            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                                self.placeCollision(coords)
                            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                                self.pickCollision(coords)
                    
                    case common.MODEINDEX.CHANGES:
                        if event.buttons() == Qt.MouseButton.LeftButton:
                            self.pickMapChanges(coords)
                    
                    case common.MODEINDEX.GAME:
                        if event.buttons() == Qt.MouseButton.LeftButton:
                            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                                self.state.previewLocked = not self.state.previewLocked
                                if not self.state.previewLocked:
                                    self.moveGameModeMask(coords)
                                    self.previewNPC.setCursor(Qt.CursorShape.BlankCursor)
                                else:
                                    self.previewNPC.setCursor(Qt.CursorShape.ArrowCursor)
                                    
            else:
                # handle temporary mode
                match self.state.tempMode:
                    case common.TEMPMODEINDEX.IMPORTMAP:
                        self.finaliseImportMap(coords)
                    
                    # Handling of SETDOORDEST is in map_view.py.
                    # This is because the view is in control of handling selections,
                    # and we want to change the behaviour of clicking off the object.
                    
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        coords = EBCoords(event.scenePos().x(), event.scenePos().y())
        if self.state.tempMode == common.TEMPMODEINDEX.NONE:
            match self.state.mode:
                case common.MODEINDEX.TILE:
                    if event.buttons() == Qt.MouseButton.RightButton:
                        self.selectMultipleSectors(coords)
                case common.MODEINDEX.SECTOR:
                    if event.buttons() == Qt.MouseButton.LeftButton:
                        self.selectMultipleSectors(coords)
                    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):        
        if self.state.tempMode == common.TEMPMODEINDEX.NONE:
            match self.state.mode:
                case common.MODEINDEX.TILE:
                    if event.buttons() == Qt.MouseButton.NoButton:
                        self.endPlacingTiles()
                case common.MODEINDEX.ENEMY:
                    if event.buttons() == Qt.MouseButton.NoButton:
                        self.endPlacingEnemyTiles()
                case common.MODEINDEX.COLLISION:
                    if event.buttons() == Qt.MouseButton.NoButton:
                        self.endPlacingCollision()
                    
        super().mouseReleaseEvent(event)
        
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        # query if we have any other buttons pressed. We should only ever open the context menu if ONLY RMB was pressed.
        # (also on some systems (mine) it looks like RMB is still in mouseButtons at this point so...)
        if QApplication.mouseButtons() not in [Qt.MouseButton.NoButton, Qt.MouseButton.RightButton]:
            return
        
        # if we're holding Alt, don't do anything, because we're copying coords in mousePressEvent
        if Qt.KeyboardModifier.AltModifier in event.modifiers():
            return super().contextMenuEvent(event)
        
        items = self.items(event.scenePos())
        
        # first, see if anything should get the menu first
        for i in items:
            if isinstance(i, (MapEditorNPC, trigger.MapEditorTrigger)):
                i.contextMenuEvent(event)
                return

        # no items to pass the event to
        if self.state.tempMode == common.TEMPMODEINDEX.NONE:
            menu = QMenu()
            x = event.scenePos().x()
            y = event.scenePos().y()
            match self.state.mode:
                case common.MODEINDEX.SECTOR:
                    if len(self.state.currentSectors) > 1:
                        entireSectorStr = "Copy entirety of sectors"
                        dataSectorStr = "Copy data of sectors"
                        paletteSectorStr = "Copy only sector palettes"
                    else:
                        entireSectorStr = "Copy entire sector"
                        dataSectorStr = "Copy sector data"
                        paletteSectorStr = "Copy only sector palette"
                    
                    menu.addAction(icons.ICON_RECT, entireSectorStr, self.copySelectedSectors, shortcut=QKeySequence.StandardKey.Copy)
                    menu.addAction(icons.ICON_COPY, dataSectorStr, self.copySelectedSectorAttributes, shortcut=QKeySequence("Ctrl+Shift+C"))
                    menu.addAction(icons.ICON_PALETTE, paletteSectorStr, self.copySelectedSectorPalettes, shortcut=QKeySequence("Ctrl+Alt+Shift+C"))
                    menu.addSeparator()
                    menu.addAction(icons.ICON_PASTE, "Paste", self.onPaste)
                case common.MODEINDEX.NPC:
                    menu.addAction(icons.ICON_NEW, "New NPC instance", lambda: self.newNPCInstance(EBCoords(x, y)))
                    if self.projectData.isFeatureAvailable(common.COILSNAKEFEATUREIDS.CREATENPCS):
                        menu.addAction(icons.ICON_NEW_NPC, "Create new NPC && add instance", lambda: self.createNPCAndInstance(EBCoords(x, y)))
                    menu.addAction(icons.ICON_PASTE, "Paste", self.onPaste)
                case common.MODEINDEX.TRIGGER:
                    menu.addAction(icons.ICON_NEW, "New &trigger", lambda: self.newTrigger(EBCoords(x, y)))
                    menu.addAction(icons.ICON_NEW, "New &ladder", lambda: self.addTrigger(trigger.Trigger(EBCoords(event.scenePos().x(), event.scenePos().y()),
                                                                         trigger.TriggerLadder())))
                    menu.addAction(icons.ICON_NEW, "New &rope", lambda: self.addTrigger(trigger.Trigger(EBCoords(event.scenePos().x(), event.scenePos().y()),
                                                                       trigger.TriggerRope())))
                    menu.addAction(icons.ICON_PASTE, "Paste", self.onPaste)
                case common.MODEINDEX.HOTSPOT:
                    menu.addAction(icons.ICON_EXPORT, "&Move hotspot here...", lambda: self.moveHotspot(EBCoords(x, y)))
                case common.MODEINDEX.WARP:
                    menu.addAction(icons.ICON_EXPORT, "Move &warp here...", lambda: self.moveWarp(EBCoords(x, y)))
                    menu.addAction(icons.ICON_EXPORT, "Move &teleport here...", lambda: self.moveTeleport(EBCoords(x, y)))    
                case _:
                    return super().contextMenuEvent(event)
            menu.exec(event.screenPos())

    def onAction(self, command: QUndoCommand):
        # handle graphics updating and whatnot
        # we don't actually store a reference to the graphics object in the undo command
        # this is because we'd have to make copies of tile graphics and whatever
        # and im not totally sure about referencing ProjectData in undo commands
        # even though it would make this quite a bit easier.
        # oh well, it's more memory-efficient anyway.
        # we can just look at the command and see what it's up to.
        
        if not command:
            return # idk why this happens but uh. it does. probably A Qt Thing:tm:
        
        actionType = None
        commands = []

        count = command.childCount()
        if count > 0: # handle macros
            for c in range(command.childCount()):
                commands.append(command.child(c))
            commands.append(command)
                        
        elif hasattr(command, "commands"): # handle multis (which should not have children)
            for c in command.commands:
                commands.append(c)
                
        # do this *always* to be safe        
        commands.append(command)
        
        for c in commands:
            if isinstance(c, ActionPlaceTile):
                actionType = "tile"

            if isinstance(c, ActionMoveNPCInstance) or isinstance(c, ActionChangeNPCInstance):
                actionType = "npc"
                self.refreshNPCInstance(c.instance.uuid)
            
            if isinstance(c, ActionAddNPCInstance):
                actionType = "npc"
                try:
                    self.refreshNPCInstance(c.instance.uuid)
                except KeyError:
                    pass # happens on undo due to NPC being not present
            
            if isinstance(c, ActionUpdateNPC):
                actionType = "npc"
                self.refreshNPC(c.npc.id)
            
            if isinstance(c, ActionDeleteNPCInstance):
                actionType = "npc"
                
            if isinstance(c, ActionMoveTrigger) or isinstance(c, ActionUpdateTrigger):
                actionType = "trigger"
                self.refreshTrigger(c.trigger.uuid)
                
            if isinstance(c, ActionAddTrigger):
                actionType = "trigger"
                try:
                    self.refreshTrigger(c.trigger.uuid)
                except KeyError:
                    pass # happens on undo due to trigger being not present
            
            if isinstance(c, ActionDeleteTrigger):
                actionType = "trigger"
                
            if isinstance(c, ActionChangeSectorAttributes):
                actionType = "sector"
                self.refreshSector(c.sector.coords)
                
            if isinstance(c, ActionPlaceEnemyTile):
                actionType = "enemy"
                self.refreshEnemyTile(c.enemytile.coords)
                
            if isinstance(c, ActionUpdateEnemyMapGroup):
                actionType = "enemy"
                self.refreshEnemyMapGroup(c.group.groupID)
                
            if isinstance(c, ActionChangeHotspotColour) or isinstance(c, ActionChangeHotspotLocation) or isinstance(c, ActionChangeHotspotComment):
                actionType = "hotspot"
                self.refreshHotspot(c.hotspot.id)
                
            if isinstance(c, ActionMoveWarp) or isinstance(c, ActionUpdateWarp):
                actionType = "warp"
                self.refreshWarp(c.warp.id)
                
            if isinstance(c, ActionMoveTeleport) or isinstance(c, ActionUpdateTeleport):
                actionType = "warp"
                self.refreshTeleport(c.teleport.id)
            
            if isinstance(c, ActionAddPalette) or isinstance(c, ActionRemovePalette):
                self.parent().sidebarTile.fromSector(self.state.currentSectors[-1])
                self.parent().sidebarSector.fromSectors()
                
            if isinstance(c, ActionChangeCollision):
                actionType = "collision"
            
            if isinstance(c, ActionChangeMapChangeEvent):
                actionType = "mapchange"
                self.parent().sidebarChanges.selectEvent(c.event)
            
            if isinstance(c, ActionChangeTileChange) or isinstance(c, ActionAddTileChange) or isinstance(c, ActionRemoveTileChange) \
                or isinstance(c, ActionMoveTileChange):
                actionType = "mapchange"
                self.parent().sidebarChanges.refreshEvent(c.event)
                self.calculateMapEventTileMappings()
                
            # dont forget to update the enabled map changes!
            if isinstance(c, ActionAddMapChangeEvent) or isinstance(c, ActionRemoveMapChangeEvent) \
                or isinstance(c, ActionMoveMapChangeEvent):
                actionType = "mapchange"
                self.parent().sidebarChanges.fromTileset(c.event.tileset)
                self.calculateMapEventTileMappings()
            
            if isinstance(c, ActionAddSectorUserDataField) or isinstance(c, ActionRemoveSectorUserDataField) or isinstance(c, ActionImportSectorUserData):
                actionType = "userdata"
                self.parent().sidebarSector.fromSectors()
            
            if isinstance(c, ActionReplaceTileset):
                actionType = "tile"
                self.parent().sidebarTile.tilesetSelect.setCurrentIndex(c.index)
                self.parent().sidebarTile.scene.update()
            
            if isinstance(c, ActionSwapTiles):
                actionType = "tile"
                self.parent().sidebarTile.scene.update()

        match actionType:
            case "tile":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.TILE)
            case "npc":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.NPC)
                if self.state.currentNPCInstances != []:
                    self.parent().sidebarNPC.fromNPCInstances()
            case "trigger":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.TRIGGER)
                if self.state.currentTriggers != []:
                    self.parent().sidebarTrigger.fromTriggers()
            case "sector":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.SECTOR)
                if self.state.currentSectors != []:
                    self.parent().sidebarSector.fromSectors()   
            case "enemy":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.ENEMY)
                self.parent().sidebarEnemy.selectEnemyTile(self.state.currentEnemyTile)
            case "hotspot":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.HOTSPOT)
                self.parent().sidebarHotspot.fromHotspot()
            case "warp":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.WARP)
                self.parent().sidebarWarp.fromWarp()
            case "collision":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.COLLISION)
                self.parent().sidebarCollision.display.update()
                if self.parent().sidebarCollision.presets._lastTile:
                    self.parent().sidebarCollision.presets.verifyTileCollision(self.parent().sidebarCollision.presets._lastTile)
            case "mapchange":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.CHANGES)
                # self.parent().sidebarChanges.refreshCurrent()
            case "userdata":
                if not self.dontUpdateModeNextAction:
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.SECTOR)
                    self.parent().sidebarSector.setShowUserData(True)
    
        self.update()
        self.dontUpdateModeNextAction = False # unset after action is pushed

    def onCopy(self):
        match self.state.mode:
            case common.MODEINDEX.TILE:
                self.copySelectedSectors()
            case common.MODEINDEX.SECTOR:
                self.copySelectedSectors()
            case common.MODEINDEX.NPC:
                self.copySelectedNPCInstancess()
            case common.MODEINDEX.TRIGGER:
                self.copySelectedTriggers()
                
    def onCut(self):
        match self.state.mode:
            case common.MODEINDEX.NPC:
                self.copySelectedNPCInstancess()
                self.deleteSelectedNPCInstances()
            case common.MODEINDEX.TRIGGER:
                self.copySelectedTriggers()
                self.deleteSelectedTriggers()
        
    def onPaste(self):
        inMacro = False
        try:
            text = json.loads(QApplication.clipboard().text())
            match text["Type"]:
                case "Sector":
                    self.undoStack.beginMacro("Paste sectors")
                    inMacro = True
                    
                    root = self.state.currentSectors[0].coords.coordsSector()
                    for i in text["Data"]:
                        coords = EBCoords.fromSector(i["Offset"][0]+root[0], i["Offset"][1]+root[1])
                        if coords.x < 0 or coords.y < 0: continue
                        try:
                            sector = self.projectData.getSector(coords)
                        except IndexError: continue                        
                        try:
                            palette = i["Palette"]
                            action = ActionChangeSectorAttributes(sector, palette["tileset"], palette["palettegroup"], palette["palette"],
                                                                  sector.item, sector.music, sector.setting, sector.teleport, sector.townmap,
                                                                  sector.townmaparrow, sector.townmapimage, sector.townmapx, sector.townmapy, sector.userdata)
                            self.undoStack.push(action)
                        except KeyError: pass
                        
                        try: # do tiles in middle so undo AND redo don't see the tile action as the final one (and thus set to tile mode)
                            tiles = i["Tiles"]
                            for j, t in enumerate(tiles):
                                action = ActionPlaceTile(self.projectData.getTile(EBCoords.fromTile(j%8, j//8)+coords), t)
                                self.undoStack.push(action)
                        except KeyError: pass
                        
                        try:
                            attributes = i["Attributes"]
                            action = ActionChangeSectorAttributes(sector, sector.tileset, sector.palettegroup, sector.palette,
                                                                    attributes["item"], attributes["music"], attributes["setting"], attributes["teleport"],
                                                                    attributes["townmap"], attributes["townmaparrow"], attributes["townmapimage"],
                                                                    attributes["townmapx"], attributes["townmapy"], attributes["userdata"])
                            self.undoStack.push(action)
                        except KeyError: pass
                        
                    self.undoStack.endMacro()
                    inMacro = False
                    
                case "NPC":
                    absolute = QSettings().value("main/absolutePaste", False, type=bool)
                    if not absolute:
                        
                        #1. get top-left-most NPC
                        root = EBCoords(text["Data"][0]["coords"][0], text["Data"][0]["coords"][1])
                        for i in text["Data"]:
                            coords = EBCoords(i["coords"][0], i["coords"][1])
                            if coords <= root:
                                root = coords
                                
                        #2. calculate relative offsets
                        for i in text["Data"]:
                            i["coords"][0] -= root.x
                            i["coords"][1] -= root.y
                    
                    self.clearSelection()
                    self.undoStack.beginMacro("Paste NPCs")
                    
                    inMacro = True
                    for i in text["Data"]:
                        inst = NPCInstance(i["id"], EBCoords(i["coords"][0], i["coords"][1]))
                        
                        if inst.npcID >= len(self.projectData.npcs):
                            raise ValueError(f"NPC ID for instance to paste is out of range. Got {inst.npcID}, max is {len(self.projectData.npcs)-1}.")
                        
                        if not absolute: # then add the mouse pos
                            inst.coords += EBCoords(*self.parent().view.mapToScene(
                                self.parent().view._lastMousePos).toTuple())
                            inst.coords.restrictToMap()
                            
                        self.addNPCInstance(inst)
                    self.undoStack.endMacro()
                    inMacro = False
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.NPC)
                    
                case "Trigger":
                    absolute = QSettings().value("main/absolutePaste", False, type=bool)
                    if not absolute:
                        
                        #1. get top-left-most trigger
                        root = EBCoords(text["Data"][0]["coords"][0], text["Data"][0]["coords"][1])
                        for i in text["Data"]:
                            coords = EBCoords(i["coords"][0], i["coords"][1])
                            if coords <= root:
                                root = coords
                                
                        #2. calculate relative offsets
                        for i in text["Data"]:
                            i["coords"][0] -= root.x
                            i["coords"][1] -= root.y
                            
                    self.clearSelection()
                    self.undoStack.beginMacro("Paste triggers")
                    inMacro = True
                    for i in text["Data"]:
                        match i["data"]["type"]:
                            case "door":
                                typeData = trigger.TriggerDoor(EBCoords(i["data"]["dest"][0], i["data"]["dest"][1]),
                                                               i["data"]["dir"],
                                                               i["data"]["flag"],
                                                               i["data"]["style"],
                                                               i["data"]["text"])
                            case "escalator":
                                typeData = trigger.TriggerEscalator(i["data"]["dir"])
                            case "ladder":
                                typeData = trigger.TriggerLadder()
                            case "object":
                                typeData = trigger.TriggerObject(i["data"]["text"])
                            case "person":
                                typeData = trigger.TriggerPerson(i["data"]["text"])
                            case "rope":
                                typeData = trigger.TriggerRope()
                            case "stairway":
                                typeData = trigger.TriggerStairway(i["data"]["dir"])
                            case "switch":
                                typeData = trigger.TriggerSwitch(i["data"]["text"],
                                                                 i["data"]["flag"])
                            case _:
                                logging.warning(f"Unknown trigger type {i['data']['type']}")
                                continue
                        trigger_ = trigger.Trigger(EBCoords(i["coords"][0], i["coords"][1]), typeData)
                        
                        if not absolute:
                            trigger_.coords += EBCoords(*self.parent().view.mapToScene(
                                self.parent().view._lastMousePos).toTuple())
                            trigger_.coords.restrictToMap()
                            trigger_.coords = EBCoords(*trigger_.coords.roundToWarp())
                            trigger_.coords.restrictToMap()
                        
                        self.addTrigger(trigger_)
                    self.undoStack.endMacro()
                    inMacro = False
                    self.parent().sidebar.setCurrentIndex(common.MODEINDEX.TRIGGER)
        except json.decoder.JSONDecodeError:
            if inMacro:
                self.undoStack.endMacro()
            logging.warning("Clipboard data is not valid for pasting.")
        except Exception as e:
            if inMacro:
                self.undoStack.endMacro()
            logging.warning(f"Failed to paste possibly valid data: {e}")
            raise
        
    def onDelete(self):
        match self.state.mode:
            case common.MODEINDEX.NPC:
                self.deleteSelectedNPCInstances()
            case common.MODEINDEX.TRIGGER:
                self.deleteSelectedTriggers()       
                
    def onCancel(self):
        grabber = self.mouseGrabberItem()
        if grabber: grabber.mouseReleaseEvent(QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease))
        
        self.mouseReleaseEvent(QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease))
        self.clearSelection()
        match self.state.tempMode:
            case common.TEMPMODEINDEX.IMPORTMAP:
                self.cancelImportMap()
            case common.TEMPMODEINDEX.SETDOORDEST:
                self.cancelDoorDest()
        
    def setTemporaryMode(self, index: int):
        """Initialise a temporary mode (eg. for door target placement).

        Temporary modes do not affect the sidebar, for instance, but affect user controls on the map.

        Args:
            index (int): the mode to initialise
        """
        self.state.tempMode = index

    def onChangeMode(self, index: int):
        event = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.MouseButtonRelease)
        event.setScenePos(QPoint(*self._lastCoords.coords()))
        self.mouseReleaseEvent(event)
        for i in self.selectedItems():
            i.mouseReleaseEvent(event)
                   
        if index == common.MODEINDEX.SECTOR:
            self.sectorSelect.show()
        else:
            if index != common.MODEINDEX.TILE:
                self.sectorSelect.hide()
            else: self.sectorSelect.show()
        
        if index == common.MODEINDEX.NPC:
            MapEditorNPC.showNPCs()
        else:
            MapEditorNPC.hideNPCs()
            self.parent().sidebarNPC.deselectNPC()

        if index == common.MODEINDEX.TRIGGER:
            trigger.MapEditorTrigger.showTriggers()
        else:
            trigger.MapEditorTrigger.hideTriggers()
            self.parent().sidebarTrigger.deselectTrigger()

        if index == common.MODEINDEX.ENEMY:
            if self.parent().enemyLinesAction.isChecked():
                self.hoverSpawnLines.show()
            else:
                self.hoverSpawnLines.hide()
        else:
            self.hoverSpawnLines.hide()
            
        if index == common.MODEINDEX.HOTSPOT:
            MapEditorHotspot.showHotspots()
        else:
            MapEditorHotspot.hideHotspots()
        
        if index == common.MODEINDEX.WARP:
            MapEditorWarp.showWarps()
        else:
            MapEditorWarp.hideWarps()
            
        if index == common.MODEINDEX.ALL:
            if self.parent().sidebarAll.showNPCs.isChecked():
                MapEditorNPC.showNPCs()
            else: MapEditorNPC.hideNPCs()
            if self.parent().sidebarAll.showTriggers.isChecked():
                trigger.MapEditorTrigger.showTriggers()
            else: trigger.MapEditorTrigger.hideTriggers()
            if self.parent().sidebarAll.showEnemyLines.isChecked():
                    self.hoverSpawnLines.show()
            else:
                self.hoverSpawnLines.hide()
            if self.parent().sidebarAll.showHotspots.isChecked():
                MapEditorHotspot.showHotspots()
            else: MapEditorHotspot.hideHotspots()
            if self.parent().sidebarAll.showWarps.isChecked():
                MapEditorWarp.showWarps()
            else:
                MapEditorWarp.hideWarps()
            
        if index == common.MODEINDEX.GAME:
            if self.grid.isVisible():
                self.grid.hide()
            if self.parent().sidebarGame.showPreviewNPC.isChecked(): self.previewNPC.show()
            else: self.previewNPC.hide()
            view = self.parent().view
            center = view.mapToScene(view.viewport().rect().center())
            if not self.state.previewLocked:
                self.moveGameModeMask(EBCoords(center.x(), center.y()), True) # TODO grabs this before sidebar updates size
            MapEditorNPC.hideVisualBounds()
            MapEditorNPC.hideCollisionBounds()
            MapEditorNPC.hideNPCIDs()
            MapEditorNPC.showNPCs()
            
        else:
            try:
                if self.parent().gridAction.isChecked():
                    self.grid.show()
            except AttributeError:
                pass # this happens on init
                
            self.previewNPC.hide()
            if QSettings().value("mapeditor/ShowNPCVisualBounds", type=bool):
                MapEditorNPC.showVisualBounds()
            else: MapEditorNPC.hideVisualBounds()
            if QSettings().value("mapeditor/ShowNPCCollisionBounds", type=bool):
                MapEditorNPC.showCollisionBounds()
            else: MapEditorNPC.hideCollisionBounds
            if QSettings().value("mapeditor/ShowNPCIDs", type=bool):
                MapEditorNPC.showNPCIDs()
            else: MapEditorNPC.hideNPCIDs()
            
        # fix grid
        self.setGrid(self._currentGrid, index)
        
        self.update()
                
    def collisionAt(self, coords: EBCoords) -> int:
        tile = self.projectData.getTile(coords)
        
        tileset = self.projectData.getTileset(tile.tileset)
        collisionMap = tileset.tiles[tile.tile].collision
        
        x, y = coords.coordsWarp()
        x = x % 4
        y = y % 4
        return collisionMap[x + y * 4]
    
    def sampleCollisionRegion(self, topleft: EBCoords, bottomright: EBCoords) -> int:
        collision = 0
        for x in range(topleft.coordsWarp()[0], bottomright.coordsWarp()[0]+1):
            for y in range(topleft.coordsWarp()[1], bottomright.coordsWarp()[1]+1):
                collision |= self.collisionAt(EBCoords.fromWarp(x, y))
        return collision

    def placeTile(self, coords: EBCoords):
        """Place a tile (id determined by tile selector active tile).

        Args:
            coords (EBCoords): location to place the tile
        """

        # item = self.tileAt(coords)
        # if item:
        coords.restrictToMap()
        toPlace = self.state.currentTile 
        tile = self.projectData.getTile(coords)
        if tile.tile != toPlace:
            if not self.state.placingTiles:
                self.state.placingTiles = True
                self.undoStack.beginMacro("Place tiles")

            tilesetID = tile.tileset
            paletteGroupID = tile.palettegroup
            paletteID = tile.palette
            tileGraphic = self.projectData.getTileGraphic(tilesetID, paletteGroupID, paletteID, toPlace)

            if not tileGraphic.hasRendered:
                palette = self.projectData.getPaletteGroup(paletteGroupID).palettes[paletteID]
                tileGraphic.render(self.projectData.getTileset(tilesetID), palette)

            # item.setPixmap(tileGraphic.rendered)
            # item.setText(str(toPlace).zfill(3))

            action = ActionPlaceTile(tile, toPlace)
            self.undoStack.push(action)
            self.update(QRect(*coords.roundToTile(), 32, 32)) # manual update here becase we don't in onAction for performance reasons on batch pushes
    
    def endPlacingTiles(self):
        if self.state.placingTiles:
            self.state.placingTiles = False
            self.undoStack.endMacro()

    def pickTile(self, coords: EBCoords):
        """Pick a tile at this location and load it into the sidebar

        Args:
            x (int): x pos (tiles)
            y (int): y pos (tiles)
        """
        coords.restrictToMap()

        # placement = self.tileAt(coords)
        # if placement:
        tile = self.projectData.getTile(coords)
        self.state.currentTile = tile.tile
        self.parent().sidebarTile.selectTile(tile.tile)

        sector = self.projectData.getSector(coords)
        self.parent().sidebarTile.fromSector(sector)
    
    def tileScratchSpacePicked(self, tile: int, tileset: int, palettegroup: int, palette: int):
        self.state.currentTile = tile
        self.parent().sidebarTile.selectTile(tile)
        
        # i honestly do not care
        self.parent().sidebarTile.fromSector(Sector(-1, -1, -1, palette, palettegroup, tileset,
                                                    "", "", "", "", "", -1, -1))

    def refreshTile(self, coords: EBCoords):
        """refresh a tile at this location.

        Args:
            coords (EBCoords): location of the tile
        """
        tile = self.projectData.getTile(coords)
        sector = self.projectData.getSector(coords)
        tile.tileset = sector.tileset
        tile.palettegroup = sector.palettegroup
        tile.palette = sector.palette

        # item = self.tileAt(coords)
        # if item:
        try:
            tileGraphic = self.projectData.getTileGraphic(tile.tileset, tile.palettegroup, tile.palette, tile.tile)
        except KeyError as e:
            raise KeyError(f"No such tile with tileset {tile.tileset}, palette group {tile.palettegroup}, palette {tile.palette}, tile {tile.tile}.") from e
        if not tileGraphic.hasRendered:
            palette = self.projectData.getPaletteGroup(tile.palettegroup).palettes[tile.palette]
            tileGraphic.render(self.projectData.getTileset(tile.tileset), palette)
        
        self.update(*tile.coords.coords(), 32, 32)
            
    def placeEnemyTile(self, coords: EBCoords):
        coords.restrictToMap()
        toPlace = self.state.currentEnemyTile
        tile = self.projectData.getEnemyTile(coords)
        if tile.groupID != toPlace:
            if not self.state.placingEnemyTiles:
                self.state.placingEnemyTiles = True
                self.undoStack.beginMacro("Place enemy tiles")
                
            action = ActionPlaceEnemyTile(tile, toPlace)
            self.undoStack.push(action)  

            self.update(*tile.coords.coords(), 64, 64)         
                
    def endPlacingEnemyTiles(self):
        if self.state.placingEnemyTiles:
            self.state.placingEnemyTiles = False
            self.undoStack.endMacro()
            
    def placeCollision(self, coords: EBCoords):
        coords.restrictToMap()
        maptile = self.projectData.getTile(coords)
        tileset = self.projectData.getTileset(maptile.tileset)
        palette = tileset.getPalette(maptile.palettegroup, maptile.palette)
        tile = self.projectData.getTileset(maptile.tileset).tiles[maptile.tile]
        
        self.parent().sidebarCollision.display.currentTile = tile
        self.parent().sidebarCollision.display.currentPalette = palette
        self.parent().sidebarCollision.display.currentTileset = tileset
        self.parent().sidebarCollision.presets.verifyTileCollision(tile)
        
        if self.collisionAt(coords) != self.state.currentCollision:
            if not self.state.placingCollision:
                self.undoStack.beginMacro("Place collision")
                self.state.placingCollision = True
            x, y = coords.coordsWarp()
            x = x % 4
            y = y % 4
            index = x + y * 4
            action = ActionChangeCollision(tile, self.state.currentCollision, index)
            self.undoStack.push(action)
            self.update()
    
    def endPlacingCollision(self):
        if self.state.placingCollision:
            self.state.placingCollision = False
            self.undoStack.endMacro()
            
    def pickCollision(self, coords: EBCoords):
        coords.restrictToMap()
        collision = self.collisionAt(coords)
        self.state.currentCollision = collision
        
        maptile = self.projectData.getTile(coords)
        tileset = self.projectData.getTileset(maptile.tileset)
        palette = tileset.getPalette(maptile.palettegroup, maptile.palette)
        tile = self.projectData.getTileset(maptile.tileset).tiles[maptile.tile]
        self.parent().sidebarCollision.display.currentTile = tile
        self.parent().sidebarCollision.display.currentPalette = palette
        self.parent().sidebarCollision.display.currentTileset = tileset
        self.parent().sidebarCollision.display.update()
        self.parent().sidebarCollision.presets.verifyTileCollision(tile)
        
        item = self.parent().sidebarCollision.presets.getPreset(collision)
        if item:
            self.parent().sidebarCollision.presets.list.setCurrentItem(item)
            
    def pickMapChanges(self, coords: EBCoords):
        coords.restrictToMap()
        tileset = self.projectData.getTile(coords).tileset
        # Pick the tileset if we are not currently on it
        if tileset != self.parent().sidebarChanges.tilesetSelect.currentIndex():
            self.parent().sidebarChanges.fromTileset(tileset)
        # Otherwise/then, try to pick the tile in question
        self.parent().sidebarChanges.selectFromTileID(self.projectData.getTile(coords).tile)
            
    def pickEnemyTile(self, coords: EBCoords):
        """Pick an enemy tile at this location and load it into the sidebar

        Args:
            x (int): x pos (tiles)
            y (int): y pos (tiles)
        """
        coords.restrictToMap()
        tile = self.projectData.getEnemyTile(coords)
        self.state.currentEnemyTile = tile.groupID
        self.parent().sidebarEnemy.selectEnemyTile(tile.groupID)
                
    def refreshEnemyTile(self, coords: EBCoords):
        coords.restrictToMap()
        tile = self.projectData.getEnemyTile(coords)
        self.refreshEnemyMapGroup(tile.groupID)
            
    def refreshEnemyMapGroup(self, group: int):
        self.parent().sidebarEnemy.view.ensureCorrectColour(group)
        groupObj = self.projectData.enemyMapGroups[group]
        groupObj.renderBg()
        groupObj.renderEnemiesOverworld(self.projectData)
        groupObj.prepareEnemiesBattle(self.projectData)
        groupObj.renderFg(self.projectData)
        self.update()

    def changeSectorBrush(self):
        current = self.sectorSelect.brush().color().toTuple()
        alpha = current[3]
        
        if alpha % 2 == 0: # going up
            alpha += 2
                    
        elif alpha % 2 == 1: # going down
            alpha -= 2
        
        if alpha > 64:
            alpha = 63
        elif alpha < 0:
            alpha = 0
            
        self.sectorSelect.setBrush(QColor(current[0], current[1], current[2], alpha))
        
    def selectSector(self, coords: EBCoords, add: bool = False, onlyAdd: bool = False):
        """Select a sector at this location (load sidebar data, etc)

        Args:
            coords (EBCoords): location of the sector
            add (bool): if this is multi-select (default False)
            onlyAdd (bool): if this is multi-select drag (default False)
        """
        coords.restrictToMap()
        sectors = []
        sectors.extend(self.state.currentSectors)

        sector = self.projectData.getSector(coords)
        if add:
            if sector in sectors:
                if len(sectors) > 1 and not onlyAdd:
                    sectors.remove(sector)
            else:
                sectors.append(sector)
        else:
            sectors = [sector,]
        
        if sectors != self.state.currentSectors:
            self.state.currentSectors = sectors
            self.parent().sidebarTile.fromSector(sector)
            self.parent().sidebarSector.fromSectors()

        rects = []
        for i in self.state.currentSectors:
            x, y = i.coords.roundToSector()
            rects.append(QRect(x, y, 256, 128))
        
        path = QPainterPath()
        for rect in rects:
            miniPath = QPainterPath()
            miniPath.addRect(rect)
            path = path.united(miniPath)
            # TODO not perfect, leaves lines between some rects on thin selections. QPolygon?
        
        self.sectorSelect.setPath(path)
        
    def selectMultipleSectors(self, coords: EBCoords):
        """Select multiple sectors in a flood-fill fashion. Sectors will be selected if palette data is identical.

        Args:
            coords (EBCoords): location of the first sector to select
        """
        coords.restrictToMap()
        sector = self.projectData.getSector(coords)    
        try: 
            matches = self.projectData.adjacentMatchingSectors(sector, [])
        except RecursionError:
            return common.showErrorMsg("Sector selection error",
                                "Too many matching adjacent sectors to select!",
                                f"Max recursion depth is {sys.getrecursionlimit()}.",
                                QMessageBox.Icon.Warning)
        
        rects = []
        for i in matches:
            x, y = i.coords.roundToSector()
            rects.append(QRect(x, y, 256, 128))
        
        path = QPainterPath()
        for rect in rects:
            miniPath = QPainterPath()
            miniPath.addRect(rect)
            path = path.united(miniPath)
            # TODO not perfect, leaves lines between some rects

        self.sectorSelect.setPath(path)
        
        self.state.currentSectors = matches
        self.parent().sidebarSector.fromSectors()
        #self.parent().sidebarTile.fromSectors(matches)


    def copySelectedSectors(self):
        copied = []
        
        rootCoords = self.state.currentSectors[0].coords
        for i in self.state.currentSectors:
            if i.coords <= rootCoords:
                rootCoords = i.coords
        
        for i in self.state.currentSectors:
            # get tile IDs from the map
            tiles = []
            for c in range(i.coords.coordsTile()[1], i.coords.coordsTile()[1]+4):
                for r in range(i.coords.coordsTile()[0], i.coords.coordsTile()[0]+8):
                    tile = self.projectData.getTile(EBCoords.fromTile(r, c))
                    tiles.append(tile.tile)
                    
            copied.append({"Offset" : (i.coords.coordsSector()[0] - rootCoords.coordsSector()[0], i.coords.coordsSector()[1] - rootCoords.coordsSector()[1]),
                           "Attributes" : i.attributesToDataDict(),
                           "Palette" : i.paletteToDataDict(),
                           "Tiles" : tiles})
        
        copied = json.dumps({"Type": "Sector", "Data": copied})
        QApplication.clipboard().setText(copied)
        
        
    def copySelectedSectorAttributes(self):
        # since this is called at any time, we need to ensure we're in the right mode
        if self.state.mode not in (common.MODEINDEX.SECTOR, common.MODEINDEX.TILE):
            return
        
        copied = []
        
        rootCoords = self.state.currentSectors[0].coords
        for i in self.state.currentSectors:
            if i.coords <= rootCoords:
                rootCoords = i.coords
                
        for i in self.state.currentSectors:
            copied.append({"Offset" : (i.coords.coordsSector()[0] - rootCoords.coordsSector()[0], i.coords.coordsSector()[1] - rootCoords.coordsSector()[1]),
                           "Attributes" : i.attributesToDataDict(),
                           "Palette" : i.paletteToDataDict()})
        
        copied = json.dumps({"Type": "Sector", "Data": copied})
        QApplication.clipboard().setText(copied)
        
    def copySelectedSectorPalettes(self):
        # ditto
        if self.state.mode not in (common.MODEINDEX.SECTOR, common.MODEINDEX.TILE):
            return
        
        copied = []
        
        rootCoords = self.state.currentSectors[0].coords
        for i in self.state.currentSectors:
            if i.coords <= rootCoords:
                rootCoords = i.coords
        
        for i in self.state.currentSectors:
            copied.append({"Offset" : (i.coords.coordsSector()[0] - rootCoords.coordsSector()[0], i.coords.coordsSector()[1] - rootCoords.coordsSector()[1]),
                           "Palette" : i.paletteToDataDict()})
            
        copied = json.dumps({"Type": "Sector", "Data": copied})
        QApplication.clipboard().setText(copied)
            
        
    def refreshSector(self, coords: EBCoords):
        """Refresh all tiles in a sector at this location.
        
        Args:
            coords (EBCoords): location of the sector
        """
        for r in range(coords.coordsTile()[0], coords.coordsTile()[0]+8):
            for c in range(coords.coordsTile()[1], coords.coordsTile()[1]+4):
                self.refreshTile(EBCoords.fromTile(r, c))

    def newNPCInstance(self, coords: EBCoords = EBCoords(0, 0), id: int = 0):
        """Create a new NPC instance and add it to the map

        Args:
            coords (EBCoords, optional): Location to add it at. Defaults to EBCoords(0, 0).
        """
        coords.restrictToMap()
        inst = NPCInstance(id, coords)
        self.clearSelection()
        self.addNPCInstance(inst)
    
    def deleteNPCInstance(self, instance: NPCInstance):
        """Remove an NPC instance from the map (and project data)

        Args:
            instance (NPCInstance): Instance to remove
        """
        action = ActionDeleteNPCInstance(instance, self)
        self.undoStack.push(action)
        
    def deleteSelectedNPCInstances(self):
        """Remove NPC instances based on selection"""
        if any(isinstance(x, MapEditorNPC) for x in self.selectedItems()):
            self.undoStack.beginMacro("Delete NPCs")
            for i in self.selectedItems():
                if isinstance(i, MapEditorNPC):
                    instance = self.projectData.npcInstanceFromUUID(i.uuid)
                    self.deleteNPCInstance(instance)
            self.undoStack.endMacro()
                    
    def addNPCInstance(self, instance: NPCInstance):
        """Add an NPC instance to the map (and project data)

        Args:
            instance (NPCInstance): Instance to add
        """
        action = ActionAddNPCInstance(instance, self)
        self.undoStack.push(action)
        
    def copySelectedNPCInstancess(self):
        copied = []
        for i in self.selectedItems():
            if isinstance(i, MapEditorNPC):
                copied.append(self.projectData.npcInstanceFromUUID(i.uuid).toDataDict())
                
        copied = json.dumps({"Type": "NPC", "Data": copied})
        QApplication.clipboard().setText(copied)
        
    def refreshNPC(self, id: int):
        """Refresh all instances of an NPC of id on the map

        Args:
            id (int): the ID of the NPC to refresh
        """

        npc = self.projectData.getNPC(id)
        spr = self.projectData.getSprite(npc.sprite)
        npc.render(spr)
        
        for i in self.placedNPCsByID[id]:
            i.setSprite(spr, common.DIRECTION8[npc.direction], 0)

    def refreshNPCInstance(self, uuid: UUID):
        """Refresh an NPC instance on the map

        Args:
            uuid (UUID): the UUID of the instance to refresh
        """
        inst = self.projectData.npcInstanceFromUUID(uuid)
        placement = self.placedNPCsByUUID[uuid]
        npc = self.projectData.getNPC(inst.npcID)
        spr = self.projectData.getSprite(npc.sprite)
        placement.setSprite(spr, common.DIRECTION8[npc.direction], 0)
        placement.setText(str(inst.npcID).zfill(4))
        placement.id = inst.uuid
        placement.setPos(inst.coords.x, inst.coords.y)

        # now fix placedNPCsByID
        for id, npcs in self.placedNPCsByID.items():
            if placement in npcs and id != inst.npcID:
                npcs.remove(placement)
                if not inst.npcID in self.placedNPCsByID:
                    self.placedNPCsByID[inst.npcID] = [placement,]
                else:
                    self.placedNPCsByID[inst.npcID].append(placement)
                break
            
    def createNPCAndInstance(self, coords: EBCoords):
        """Create a new NPC and add an instance of it to the map at the given location."""
        npc = NPC(len(self.projectData.npcs), "down", 0, 0, "always", 1, "$0", "$0", "person")
        action = ActionCreateNPC(self.projectData, npc)
        self.undoStack.push(action)
        self.newNPCInstance(coords, npc.id)
            
    def newTrigger(self, coords: EBCoords = EBCoords(0, 0)):
        """Create a new trigger at coords

        Args:
            coords (EBCoords, optional): Location to create the trigger at. Defaults to EBCoords(0, 0).
        """
        coords.restrictToMap()
        trigger_ = trigger.Trigger(coords, trigger.TriggerDoor())
        self.clearSelection()
        self.addTrigger(trigger_)
        
    def addTrigger(self, trigger_: trigger.Trigger):
        """Add a trigger to the map

        Args:
            trigger_ (trigger.Trigger): the trigger to add
        """
        action = ActionAddTrigger(trigger_, self)
        self.undoStack.push(action)
        
    def deleteTrigger(self, trigger_: trigger.Trigger):
        """Remove a trigger from the map

        Args:
            trigger_ (trigger.Trigger): the trigger to remove
        """
        action = ActionDeleteTrigger(trigger_, self)
        self.undoStack.push(action)
    
    def deleteSelectedTriggers(self):
        """Remove triggers based on selection"""
        if any(isinstance(i, trigger.MapEditorTrigger) for i in self.selectedItems()):
            self.undoStack.beginMacro("Delete triggers")
            for i in self.selectedItems():
                if isinstance(i, trigger.MapEditorTrigger):
                    trigger_ = self.projectData.triggerFromUUID(i.uuid)
                    self.deleteTrigger(trigger_)
            self.undoStack.endMacro()
            
    def copySelectedTriggers(self):
        copied = []
        for i in self.selectedItems():
            if isinstance(i, trigger.MapEditorTrigger):
                copied.append(self.projectData.triggerFromUUID(i.uuid).toDataDict())
        copied = json.dumps({"Type": "Trigger", "Data": copied})
        QApplication.clipboard().setText(copied)

    def refreshTrigger(self, uuid: UUID):
        """Refresh a trigger on the map

        Args:
            uuid (UUID): the UUID of the trigger to refresh
        """
        trigger_ = self.projectData.triggerFromUUID(uuid)
        placement = self.placedTriggersByUUID[uuid]
        placement.setPos(trigger_.coords.x, trigger_.coords.y)

        match type(trigger_.typeData):
            case trigger.TriggerDoor:
                placement.setPixmap(self.imgTriggerDoor)
            case trigger.TriggerEscalator:
                placement.setPixmap(self.imgTriggerEscalator)
            case trigger.TriggerLadder:
                placement.setPixmap(self.imgTriggerLadder)
            case trigger.TriggerObject:
                placement.setPixmap(self.imgTriggerObject)
            case trigger.TriggerPerson:
                placement.setPixmap(self.imgTriggerPerson)
            case trigger.TriggerRope:
                placement.setPixmap(self.imgTriggerRope)
            case trigger.TriggerStairway:
                placement.setPixmap(self.imgTriggerStairway)
            case trigger.TriggerSwitch:
                placement.setPixmap(self.imgTriggerSwitch)
            case _: # should never happen
                logging.warning(f"Unknown trigger type {trigger_.typeData}")
    
    def refreshHotspot(self, id: int):
        hotspot = self.projectData.hotspots[id]
        placement = self.placedHotspots[id]
        
        placement.setRect(hotspot.start.x, hotspot.start.y, hotspot.end.x-hotspot.start.x, hotspot.end.y-hotspot.start.y)
        placement.setBrush(QBrush(QColor.fromRgb(*hotspot.colour, 128)))
    
    def moveHotspot(self, coords: EBCoords):
        coords.restrictToMap()
        coords = EBCoords(*coords.roundToWarp())
        id = QInputDialog().getInt(self.parent(),
                                   "Move hotspot here",
                                   "Hotspot ID",
                                   0, 0, len(self.projectData.hotspots)-1)
        if id[1]:
            hotspot = self.projectData.hotspots[id[0]]
            # get the width and height
            width = hotspot.end.x - hotspot.start.x
            height = hotspot.end.y - hotspot.start.y
            # new endpoint based on this
            end = coords+EBCoords(width, height)
            end.restrictToMap()
            end = EBCoords(*end.roundToWarp())
            if end >= coords: # may happen at edge of map
                coords = end - EBCoords(8, 8)
            action = ActionChangeHotspotLocation(hotspot, coords, end)
            self.undoStack.push(action)
        
    def refreshWarp(self, id: int):
        warp = self.projectData.warps[id]
        placement = self.placedWarps[id]
        placement.setPos(warp.dest.x, warp.dest.y)
    
    def refreshTeleport(self, id: int):
        teleport = self.projectData.teleports[id]
        placement = self.placedTeleports[id]
        placement.setPos(teleport.dest.x, teleport.dest.y)
        
    def moveWarp(self, coords: EBCoords):
        coords.restrictToMap()
        coords = EBCoords(*coords.roundToWarp())
        id = QInputDialog().getInt(self.parent(),
                                   "Move warp here",
                                   "Warp ID",
                                   0, 0, len(self.projectData.warps)-1)
        if id[1]:
            warp = self.projectData.warps[id[0]]
            action = ActionMoveWarp(warp, coords)
            self.undoStack.push(action)
            self.refreshWarp(id[0])
    
    def moveTeleport(self, coords: EBCoords):
        coords.restrictToMap()
        coords = EBCoords(*coords.roundToWarp())
        id = QInputDialog().getInt(self.parent(),
                                   "Move teleport here",
                                   "Teleport ID",
                                   0, 0, len(self.projectData.teleports)-1)
        if id[1]:
            teleport = self.projectData.teleports[id[0]]
            action = ActionMoveTeleport(teleport, coords)
            self.undoStack.push(action)
    
    def calculateMapEventTileMappings(self):
        """This should be called after all changes to `enabledMapEvents`."""
        self.mapEventTileMappings = {}
        for i in self.enabledMapEvents:
            if i.tileset not in self.mapEventTileMappings: self.mapEventTileMappings[i.tileset] = {}
            relevantTileChanges = [change for event in [relevantEvent for relevantEvent in self.enabledMapEvents if relevantEvent.tileset == i.tileset] for change in event.changes]
            for j in relevantTileChanges:
                checking = j.after
                endLoop = False
                while not endLoop:
                    for k in relevantTileChanges:
                        if k == j:
                            # We hit the same one as ourself,
                            # so nothing beyond here applies.
                            # Break and terminate the while loop.
                            endLoop = True
                            break
                        if checking == k.before:
                            # Then get the next one and check again.
                            # Break, but don't terminate the while loop.
                            checking = k.after
                            break
                    else:
                        # We hit the end of the loop naturally (should never happen?)
                        break
                self.mapEventTileMappings[i.tileset][j.before] = checking
        
    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        start = EBCoords(*rect.topLeft().toTuple())
        end = EBCoords(*rect.bottomRight().toTuple())
        
        tint = False # Tinting for tile changes
        
        start.restrictToMap()
        end.restrictToMap()
        x0, y0 = start.coordsTile()
        x1, y1 = end.coordsTile()
        
        presets = QSettings().value("presets/presets", defaultValue=common.DEFAULTCOLLISIONPRESETS)
        presetColours: dict[int, int] = {}
        for _, value, colour in json.loads(presets):
            presetColours[value] = colour
            
        previewing = self.state.isPreviewingPalette()
        
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                coords = EBCoords.fromTile(x, y)
                try:
                    tile = self.projectData.getTile(coords)
                    overrideTileID = self.mapEventTileMappings.get(tile.tileset, {}).get(tile.tile, tile.tile)
                    if tile.tile != overrideTileID:
                        tint = QSettings().value("mapeditor/TileChangesTint", type=bool, defaultValue=False)
                                    
                    if not previewing:
                        graphic = self.projectData.getTileGraphic(tile.tileset,
                                                                    tile.palettegroup,
                                                                    tile.palette,
                                                                    overrideTileID)
                        if not graphic.hasRendered:
                            palette = self.projectData.getPaletteGroup(tile.palettegroup).palettes[tile.palette]
                            graphic.render(self.projectData.getTileset(tile.tileset), palette)
                    else:
                        graphic = self.projectData.getTileGraphic(tile.tileset,
                                                                  self.state.previewingPaletteGroup,
                                                                  self.state.previewingPalette,
                                                                  overrideTileID)
                        if not graphic.hasRendered:
                            palette = self.projectData.getPaletteGroup(
                                self.state.previewingPaletteGroup).palettes[self.state.previewingPalette]
                            graphic.render(self.projectData.getTileset(tile.tileset), palette)
                        
                    painter.drawPixmap(QPoint(x*32, y*32), graphic.rendered)
                    
                    # Draw tint for map changes if enabled
                    if tint:
                        painter.setOpacity(0.5)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(Qt.GlobalColor.red)
                        painter.drawRect(x*32, y*32, 32, 32)
                        # reset in preparation for the next tile
                        painter.setOpacity(1)
                        tint = False 
                    
                    # Draw collision
                    if self.state.mode == common.MODEINDEX.COLLISION or (self.state.mode == common.MODEINDEX.ALL and self.state.allModeShowsCollision):
                        painter.setOpacity(0.7)
                        painter.setPen(Qt.PenStyle.NoPen)
                        
                        tileset = self.projectData.getTileset(tile.tileset)
                        collisionMap = tileset.tiles[overrideTileID].collision
                        if len(set(collisionMap)) > 1: # special-casing for if all the collision is the same
                            for cx in range(0, 4):
                                for cy in range(0, 4):
                                    collision = collisionMap[cx + cy * 4] # slightly more performant to do it manually instead of collisionAt
                                    if collision:
                                        try:
                                            colour = presetColours[collision]
                                        except KeyError:
                                            colour = 0x303030
                                        painter.setBrush(QColor.fromRgb(colour))
                                        painter.drawRect((x*32)+(cx*8), (y*32)+(cy*8), 8, 8)
                        else: # all is the same - just draw 1 rect instead of 16
                            try:
                                colour = presetColours[collisionMap[0]]
                            except KeyError:
                                colour = 0x303030
                            if colour:
                                painter.setBrush(QColor.fromRgb(colour))
                                painter.drawRect(x*32, y*32, 32, 32)
                            
                        painter.setOpacity(1)
                    
                except Exception:
                    painter.drawPixmap(QPoint(x*32, y*32), QPixmap(":/ui/errorTile.png"))
                    logging.warning(traceback.format_exc())
                
        painter.setFont("EBMain")
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)
        if QSettings().value("mapeditor/ShowTileIDs", False, bool) and self.state.mode in (common.MODEINDEX.TILE, common.MODEINDEX.CHANGES, common.MODEINDEX.ALL):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 128))
            painter.drawRect(rect)
            
            for y in range(y0, y1+1):
                for x in range(x0, x1+1):
                    try:
                        coords = EBCoords.fromTile(x, y)
                        tile = self.projectData.getTile(coords)
                        overrideTileID = self.mapEventTileMappings.get(tile.tileset, {}).get(tile.tile, tile.tile)
                        if tile.tile != overrideTileID:
                                painter.setPen(Qt.GlobalColor.gray)
                                painter.drawText((x*32)+7, (y*32)+32, str(tile.tile).zfill(3))   

                        painter.setPen(Qt.GlobalColor.black)
                        painter.drawText((x*32)+8, (y*32)+23, str(overrideTileID).zfill(3))
                        painter.setPen(Qt.GlobalColor.white)
                        painter.drawText((x*32)+7, (y*32)+22, str(overrideTileID).zfill(3))           
                    except Exception:
                        logging.warning(traceback.format_exc())
        
        # Draw enemies
        if self.state.mode == common.MODEINDEX.ENEMY or (self.state.mode == common.MODEINDEX.ALL and self.state.allModeShowsEnemyTiles):
            x = start.coordsEnemy()[0]
            y = start.coordsEnemy()[1]
            for r in range(x, end.coordsEnemy()[0]+1):
                for c in range(y, end.coordsEnemy()[1]+1):
                    try:
                        coords = EBCoords.fromEnemy(r, c)
                        tile = self.projectData.getEnemyTile(coords)
                        group = self.projectData.enemyMapGroups[tile.groupID]
                        if group.groupID == 0:
                            continue
                        if group.renderedBg is None:
                            group.renderBg()
                        if group.renderedEnemiesOverworld is None:
                            group.renderEnemiesOverworld(self.projectData)
                        if group.preparedEnemiesBattle is None:
                            group.prepareEnemiesBattle(self.projectData)
                        if group.renderedFg is None:
                            group.renderFg(self.projectData)
                        
                        # Draw the BG. This is the colour
                        # TODO - would it be better if we drew the colour here..?
                        painter.drawPixmap(r*64, c*64, group.renderedBg)
                        
                        # Draw the sprites.
                        if QSettings().value("mapeditor/UseBattleSprites", type=bool, defaultValue=True):
                            # Lots of tricky things here to enable drawing battle sprites that interact with zoom nicely
                            # First, set clipping to this enemy tile. Do it before we scale, so it's correct.
                            painter.setClipRect(r*64, c*64, 64, 64, Qt.ClipOperation.ReplaceClip)
                            # Find the current scale. They're at m11 and m22 on the matrix.
                            transform = painter.transform()
                            sX = transform.m11()
                            sY = transform.m22()
                            # Undo the scaling for now.
                            # Scales less than one will act as normal (they look bad if the sprite size is maintained)
                            if sX > 1:
                                painter.scale(1/sX, 1/sY)
                            else:
                                sX = sY = 1
                            # Basically we just need to pick the right things to multiply by the scale.
                            # This is more or less everything except to do with the size of the pixmap.
                            for pixmap, dX, dY in group.preparedEnemiesBattle:
                                drawX = (r*64*sX)+(dX*sX) - pixmap.width()//2
                                drawY = (c*64*sY)+(dY*sY) - pixmap.height()
                                painter.drawPixmap(drawX, drawY, pixmap)
                            # And now just undo what we messed around with
                            painter.setClipping(False)
                            if sX > 1:
                                painter.scale(sX, sY)
                        # We're drawing overworld sprites without special treatment.
                        else:
                            painter.drawPixmap(r*64, c*64, group.renderedEnemiesOverworld)
                        # Draw the FG, which is the header with info
                        painter.drawPixmap(r*64, c*64, group.renderedFg)
                    except Exception:
                        logging.warning(traceback.format_exc())

        # draw locked spawn lines
        if self.state.mode == common.MODEINDEX.ENEMY and self.parent().enemyLinesAction.isChecked():
            # BG
            painter.setOpacity(0.5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(Qt.GlobalColor.blue)
            for i in self.state.lockedSpawnLines:
                painter.drawRect(*EBCoords.fromEnemy(*i).roundToEnemy(), 64, 64)
            painter.setOpacity(1)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # outline
            painter.setPen(QPen(Qt.GlobalColor.white, 6))
            for i in self.state.lockedSpawnLines:
                self.drawSpawnLineSet(EBCoords.fromEnemy(*i), painter)
            # main colour
            painter.setPen(QPen(Qt.GlobalColor.blue, 4))
            for i in self.state.lockedSpawnLines:
                self.drawSpawnLineSet(EBCoords.fromEnemy(*i), painter)
            
    def drawForeground(self, painter: QPainter, rect: QRectF):
        if self.state.mode == common.MODEINDEX.GAME:
            painter.setPen(Qt.PenStyle.NoPen)
            # draw bg
            if self.state.showPreviewMap:
                painter.setBrush(QBrush(self._lastTileGraphic.rendered))
                polygon = QPolygon(rect.toRect())
                for i in self._lastMatchingSectorRects:
                    polygon = polygon.subtracted(QPolygon(i))
                painter.drawPolygon(polygon)
            
            # draw screen overlay
            if self.state.showPreviewScreen:
                painter.setBrush(QBrush(QColor.fromRgb(0, 0, 0, 255*self.state.previewScreenOpacity)))
                x, y = self.previewNPC.pos().toTuple()
                y += 1 # this seems to make it match the game
                painter.drawPolygon(QPolygon(rect.toRect()).subtracted(QRect(x, y, 256, 224).adjusted(-128, -112, -128, -112)))
    
    def drawSpawnLineSet(self, coords: EBCoords, painter: QPainter):
        x, y = coords.roundToEnemy()
        if self.parent().enemyLinesTopAction.isChecked():
            painter.drawLine(x-64,  y-192, x+256, y-192)
        if self.parent().enemyLinesRightAction.isChecked():
            painter.drawLine(x+192, y-64,  x+192, y+256)
        if self.parent().enemyLinesBottomAction.isChecked():
            painter.drawLine(x-64,  y+192, x+256, y+192)
        if self.parent().enemyLinesLeftAction.isChecked():
            painter.drawLine(x-192, y-64,  x-192, y+256)
                
    def resetPreviewNPCAnim(self):
        self.previewNPCAnimTimer = self.PREVIEWNPCANIMDELAY
        self.previewNPCAnimState = 0
        sprite, forceDir = self.getPreviewNPCSprite()
        dir = forceDir if forceDir is not None else self.previewNPCCurrentDir
        self.previewNPC.setSprite(sprite, dir, 0, False)
    
    def getPreviewNPCSprite(self) -> tuple[Sprite, None|common.DIRECTION8]:
        sector = self.projectData.getSector(EBCoords(self.previewNPC.x(), self.previewNPC.y()))
        if sector.setting == "magicant sprites":
            return self.projectData.getSprite(self.projectData.playerSprites[common.PLAYERSPRITES.MAGICANT]), None
        if sector.setting == "lost underworld sprites":
            return self.projectData.getSprite(self.projectData.playerSprites[common.PLAYERSPRITES.TINY]), None
        if sector.setting == "robot sprites":
            return self.projectData.getSprite(self.projectData.playerSprites[common.PLAYERSPRITES.ROBOT]), None

        # not the best solution for trigger checking here.
        # the items need to be visible for self.items() to find them...
        triggersShown = list(self.placedTriggersByUUID.values())[0].isVisible()
        trigger.MapEditorTrigger.showTriggers()
        for i in self.items(self.previewNPC.collisionBounds.mapRectToScene(self.previewNPC.collisionBounds.rect())):
            if isinstance(i, trigger.MapEditorTrigger):
                if not triggersShown: trigger.MapEditorTrigger.hideTriggers()
                t = self.projectData.triggerFromUUID(i.uuid)
                if isinstance(t.typeData, trigger.TriggerLadder):
                    return self.projectData.getSprite(self.projectData.playerSprites[common.PLAYERSPRITES.LADDER]), common.DIRECTION8.up
                if isinstance(t.typeData, trigger.TriggerRope):
                    return self.projectData.getSprite(self.projectData.playerSprites[common.PLAYERSPRITES.ROPE]), common.DIRECTION8.up
        if not triggersShown: trigger.MapEditorTrigger.hideTriggers()
        
        return self.projectData.getSprite(self.projectData.playerSprites[common.PLAYERSPRITES.NORMAL]), None
        
    def moveGameModeMask(self, coords: EBCoords, forceRefreshSector: bool=False):
        coords.restrictToMap()
        self._lastCoords = coords
        
        # janky little fun thing to do direction and animation
        if coords == EBCoords(self.previewNPC.x(), self.previewNPC.y()):
            return
        
        old = self.previewNPC.pos()
        self.previewNPC.setPos(coords.x, coords.y)
        collidesWithTerrain = (self.previewNPC.sampleCollision() & (common.COLLISIONBITS.SOLID | common.COLLISIONBITS.VERYSOLID))
        collidingItems = self.previewNPC.collidingItems()
        collidesWithNPC = False
        for i in collidingItems:
            if isinstance(i, MapEditorNPC):
                
                # recreation of some of the logic in $C05FF6 playerEntityCollisionCheck
                subjectRect = self.previewNPC.collisionBounds.rect()
                subjectRect.setHeight(subjectRect.height())
                
                targetRect = i.collisionBounds.rect()
                targetRect.setHeight(targetRect.height())
                
                entityPos = i.pos() - i.collisionBounds.pos()*2 + QPoint(0, 8) # 8 is the manually-added offset
                playerPos = self.previewNPC.pos() - self.previewNPC.collisionBounds.pos()*2
                
                if entityPos.y() - targetRect.height() - subjectRect.height() >= playerPos.y():
                    continue
                if targetRect.height() + entityPos.y() - targetRect.height() <= playerPos.y():
                    continue
                if entityPos.x() - targetRect.width() - subjectRect.width() * 2 >= playerPos.x():
                    continue
                if entityPos.x() - targetRect.width() + targetRect.width() * 2 <= playerPos.x():
                    continue

                collidesWithNPC = True
                break
        
        # TODO some sort of system that lets you move along walls
        # best way to do this would probably be to mimic the movement rewrite
        
        if not (collidesWithTerrain or collidesWithNPC) or not self.state.previewCollides:
            self.previewNPCPositionSamples.insert(0, coords)
            if len(self.previewNPCPositionSamples) > self.PREVIEWNPCMAXSAMPLES:
                last = self.previewNPCPositionSamples.pop()
                delta = coords - last 
            else:
                while len(self.previewNPCPositionSamples) < self.PREVIEWNPCMAXSAMPLES:
                    self.previewNPCPositionSamples.append(coords)
                    delta = EBCoords(0, 0)
            
            self.previewNPCStillTimer.start()
            self.previewNPCAnimTimer -= 1
            if self.previewNPCAnimTimer < 0:
                self.previewNPCAnimTimer = self.PREVIEWNPCANIMDELAY
                self.previewNPCAnimState = int(not self.previewNPCAnimState)        
            
            angle = math.atan2(delta.y, delta.x)
            angle = math.degrees(angle)
            angle += 90
            if angle >=  360:
                angle -= 360
            if angle < 0:
                angle += 360
                
            facing = round(angle/45)
            if facing > 7: facing = 0
            
            sprite, forcedDir = self.getPreviewNPCSprite()
            facing = forcedDir if forcedDir is not None else common.DIRECTION8(facing)
            self.previewNPCCurrentDir = facing
            self.previewNPC.setSprite(sprite, facing, self.previewNPCAnimState, False)
            
            self.previewNPC.setPos(coords.x, coords.y)
        else:
            self.previewNPC.setPos(old)
            
        sector = self.projectData.getSector(coords)
            
        if (self._lastSector.tileset != sector.tileset or
            self._lastSector.palettegroup != sector.palettegroup or
            self._lastSector.palette != sector.palette or
            forceRefreshSector):
            
            # get new bg graphic
            tilegraphic = self.projectData.getTileGraphic(
                sector.tileset, sector.palettegroup, sector.palette, 0)
            
            if not tilegraphic.hasRendered:
                palette = self.projectData.getPaletteGroup(sector.palettegroup).palettes[sector.palette]
                tilegraphic.render(self.projectData.getTileset(sector.tileset), palette)
                
            # get the rects of each sector that matches the current one
            rects = []
            for y in self.projectData.sectors:
                for s in y:
                    if s.tileset == sector.tileset and s.palettegroup == sector.palettegroup and s.palette == sector.palette:
                        rects.append(QRect(s.coords.x, s.coords.y, 256, 128))    
            
            self._lastSector = sector
            self._lastMatchingSectorRects = rects
            self._lastTileGraphic = tilegraphic
        
        self.update()
           
    def importpng2ftsMap(self, png: QGraphicsPixmapItem, tiles: numpy.array, tileset: int):
        """Import a png2fts map into the map editor

        Args:
            png (QGraphicsPixmapItem): the pixmap of the map
            tiles (numpy.array): the array of tiles
        """

        self.importedMap = png
        self.importedTiles = tiles
        self.importedTileset = tileset

        self.importedMap.setZValue(common.MAPZVALUES.IMPORTEDMAP)
        self.setTemporaryMode(common.TEMPMODEINDEX.IMPORTMAP)

        self.addItem(self.importedMap)
        self.update()
    
    def moveImportMap(self, coords: EBCoords):
        coords.x = common.cap(coords.x, 0, common.EBMAPWIDTH-(self.importedTiles.shape[1]*32))
        coords.y = common.cap(coords.y, 0, common.EBMAPHEIGHT-(self.importedTiles.shape[0]*32))
        self.importedMap.setPos(coords.roundToTile()[0], coords.roundToTile()[1])

    def finaliseImportMap(self, coords: EBCoords):
        """Finalise the import of a map, placing tiles and updating sectors

        Args:
            coords (EBCoords): location to place the map
        """
        
        coords = EBCoords(coords.roundToTile()[0], coords.roundToTile()[1])

        max = self.importedTiles.shape[0]*self.importedTiles.shape[1]
        max += common.tileToSecX(self.importedTiles.shape[0])*common.tileToSecY(self.importedTiles.shape[1])

        progressDialog = QProgressDialog("Pasting tiles...", "NONCANELLABLE", 0, max, self.parent())
        progressDialog.setCancelButton(None) # no cancel button
        progressDialog.setWindowFlag(Qt.WindowCloseButtonHint, False) # no system close button, either
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumDuration(0)

        coords.x = common.cap(coords.x, 0, common.EBMAPWIDTH-(self.importedTiles.shape[1]*32))
        coords.y = common.cap(coords.y, 0, common.EBMAPHEIGHT-(self.importedTiles.shape[0]*32))

        # TODO known issue: maps smaller than a sector dont update the map correctly
        # but why would you waste a tileset on that? ;3

        # first pass: update sectors and fill with blank tiles
        # bunch of math here that i arrived at after lots of messing around
        # it works but
        # yeah let's just leave it at "it works"
        sectorSizeX = ceil((self.importedTiles.shape[1])/8) # how many sectors the image itself covers
        sectorSizeY = ceil((self.importedTiles.shape[0])/4) # (regardless of pos)

        sectorPosX = coords.coordsSector()[0] # where the placement starts
        sectorPosY = coords.coordsSector()[1]

        sectorEndX = sectorPosX+sectorSizeX # where the placement ends
        sectorEndY = sectorPosY+sectorSizeY

        if (self.importedTiles.shape[1] + coords.coordsTile()[0]) % 8 == 0: # perfect fit - remove the extra bit
            sectorEndX -= 1
        if (self.importedTiles.shape[0] + coords.coordsTile()[1]) % 4 == 0:
            sectorEndY -= 1
            
        self.undoStack.beginMacro("Import map")
        
        # a) update sectors
        for r in range(sectorPosX, sectorEndX+1):
            for c in range(sectorPosY, sectorEndY+1):
                sector = self.projectData.getSector(EBCoords.fromSector(r, c))
                action = ActionChangeSectorAttributes(sector,
                                                      self.importedTileset,
                                                      self.projectData.getTileset(self.importedTileset).palettes[0].groupID,
                                                      self.projectData.getTileset(self.importedTileset).palettes[0].paletteID,
                                                      sector.item, sector.music, sector.setting, sector.townmapimage,
                                                      sector.townmap, sector.townmaparrow, sector.townmapimage,
                                                      sector.townmapx, sector.townmapy, sector.userdata)
                self.undoStack.push(action)

                progressDialog.setValue(progressDialog.value()+1)
        
        # b) update tiles in sectors (the end effect is to not have junk tiles around the edges)
        for r in range(common.secXToTile(sectorPosX), common.secXToTile(sectorEndX+1)):
            for c in range(common.secYToTile(sectorPosY), common.secYToTile(sectorEndY+1)):
                action = ActionPlaceTile(self.projectData.getTile(EBCoords.fromTile(r, c)), 0)
                self.undoStack.push(action)

        # second pass: place new tiles
        # ignore the for-var names here lol
        for r in range(0, self.importedTiles.shape[1]):
            for c in range(0, self.importedTiles.shape[0]):
                action = ActionPlaceTile(self.projectData.getTile(coords.fromTile(
                    coords.coordsTile()[0]+r, coords.coordsTile()[1]+c)), int(self.importedTiles[c, r], 16))
                self.undoStack.push(action)
                progressDialog.setValue(progressDialog.value()+1)

        progressDialog.setValue(progressDialog.maximum())
        self.removeItem(self.importedMap)
        self.setTemporaryMode(common.TEMPMODEINDEX.NONE)
        self.undoStack.endMacro()
        self.update()
        
    def cancelImportMap(self):
        self.removeItem(self.importedMap)
        self.setTemporaryMode(common.TEMPMODEINDEX.NONE)

    def startSetDoorDest(self, coords: EBCoords):
        self.setTemporaryMode(common.TEMPMODEINDEX.SETDOORDEST)
        self.doorDestPlacer.setPos(coords.x, coords.y)
        self.doorDestLineStart = coords
        self.doorDestLine.setLine(coords.x+4, coords.y+4, coords.x+4, coords.y+4)

        self.doorDestPlacer.show()
        self.doorDestLine.show()

    def moveDoorDest(self, coords: EBCoords):
        coords.restrictToMap()
        
        coords = EBCoords(coords.roundToWarp()[0], coords.roundToWarp()[1])

        self.doorDestPlacer.setPos(coords.x, coords.y)
        self.doorDestLine.setLine(self.doorDestLineStart.x+4, self.doorDestLineStart.y+4, coords.x+4, coords.y+4)

    def finaliseDoorDest(self, coords: EBCoords):
        coords.restrictToMap()

        self.doorDestPlacer.hide()
        self.doorDestLine.hide()
        self.parent().sidebarTrigger.setDoorDest(coords)
        self.setTemporaryMode(common.TEMPMODEINDEX.NONE)
        
    def cancelDoorDest(self):
        self.doorDestPlacer.hide()
        self.doorDestLine.hide()
        self.setTemporaryMode(common.TEMPMODEINDEX.NONE)
        
    def onClear(self):
        result = ClearDialog.clearMap(self.parent())
        if result:
            self.undoStack.beginMacro("Clear map")
            try:
                if result["tiles"]:
                    self.clearTiles()
                if result["sectors"]:
                    self.clearSectors()
                if result["npcs"]:
                    self.clearNPCs()
                if result["triggers"]:
                    self.clearTriggers()
                if result["enemies"]:
                    self.clearEnemies()
            except Exception:
                self.undoStack.endMacro()
                raise
            else:
                self.undoStack.endMacro()
        self.update()
    
    def clearTiles(self):
        progressDialog = QProgressDialog("Clearing tiles...", "NONCANELLABLE", 0,
                                         common.EBMAPWIDTH//32//8, # updating once per tile or even once per row isn't performant
                                         self.parent()) # you spend more time updating the progress bar than the tiles!
        progressDialog.setCancelButton(None)
        progressDialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumDuration(0)
        
        for r in range(common.EBMAPWIDTH//32):
            for c in range(common.EBMAPHEIGHT//32):
                tile = self.projectData.getTile(EBCoords.fromTile(r, c))
                action = ActionPlaceTile(tile, 0)
                self.undoStack.push(action)
            if r % 8 == 0: # only once every 8 rows (compromise between speed & user clarity)
                progressDialog.setValue(progressDialog.value()+1)
        
        progressDialog.setValue(progressDialog.maximum())
    
    def clearSectors(self):
        progressDialog = QProgressDialog("Clearing sectors...", "NONCANELLABLE", 0,
                                         (common.EBMAPWIDTH//32//8)*(common.EBMAPHEIGHT//32//4),
                                         self.parent())
        progressDialog.setCancelButton(None)
        progressDialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumDuration(0)
        for r in range(common.EBMAPWIDTH//32//8):
            for c in range(common.EBMAPHEIGHT//32//4):
                sector = self.projectData.getSector(EBCoords.fromSector(r, c))
                action = ActionChangeSectorAttributes(sector, 0, 0, 0,
                                                      0, 0, "none", "disabled",
                                                      "none", "none", "none",
                                                      0, 0, {})
                self.undoStack.push(action)
                self.refreshSector(EBCoords.fromSector(r, c))
                progressDialog.setValue(progressDialog.value()+1)
        
        progressDialog.setValue(progressDialog.maximum())
    
    def clearNPCs(self):
        progressDialog = QProgressDialog("Clearing NPCs...", "NONCANELLABLE", 0,
                                         len(self.projectData.npcinstances),
                                         self.parent())
        progressDialog.setCancelButton(None)
        progressDialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumDuration(0)
        npcinstances = copy.copy(self.projectData.npcinstances) # local copy as it changes size during iteration
        for i in npcinstances:
            self.deleteNPCInstance(i)
            progressDialog.setValue(progressDialog.value()+1)
    
        progressDialog.setValue(progressDialog.maximum())
            
    def clearTriggers(self):
        progressDialog = QProgressDialog("Clearing triggers...", "NONCANELLABLE", 0,
                                         len(self.projectData.triggers),
                                         self.parent())
        progressDialog.setCancelButton(None)
        progressDialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumDuration(0)
        triggers = copy.copy(self.projectData.triggers) # ditto
        for i in triggers:
            self.deleteTrigger(i)
            progressDialog.setValue(progressDialog.value()+1)
        
        progressDialog.setValue(progressDialog.maximum())
    
    def clearEnemies(self):
        progressDialog = QProgressDialog("Clearing enemies...", "NONCANELLABLE", 0,
                                         (common.EBMAPWIDTH//64)*(common.EBMAPHEIGHT//64),
                                         self.parent())
        progressDialog.setCancelButton(None)
        progressDialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setMinimumDuration(0)
        for r in range(common.EBMAPWIDTH//64):
            for c in range(common.EBMAPHEIGHT//64):
                tile = self.projectData.getEnemyTile(EBCoords.fromEnemy(r, c))
                action = ActionPlaceEnemyTile(tile, 0)
                self.undoStack.push(action)
                progressDialog.setValue(progressDialog.value()+1)
        
        progressDialog.setValue(progressDialog.maximum())
                

    def toggleGrid(self):
        if not self.parent().gridAction.isChecked(): # checked state is updated afterwards # <-- some waffle, dont listen
            if self.state.mode != common.MODEINDEX.GAME:
                self.grid.hide()
        else: 
            if self.state.mode != common.MODEINDEX.GAME:
                self.grid.show()
    
    def toggleTileIDs(self):
        self.update()
        self.parent().sidebarTile.scene.update()

    def toggleNPCIDs(self):
        settings = QSettings()
        if MapEditorNPC.NPCIDsEnabled:
            if self.state.mode != common.MODEINDEX.GAME:
                MapEditorNPC.hideNPCIDs()
            settings.setValue("mapeditor/ShowNPCIDs", False)
        else:
            if self.state.mode != common.MODEINDEX.GAME:
                MapEditorNPC.showNPCIDs()
            settings.setValue("mapeditor/ShowNPCIDs", True)
    
    def toggleNPCVisualBounds(self):
        settings = QSettings()
        if MapEditorNPC.visualBoundsEnabled:
            if self.state.mode != common.MODEINDEX.GAME:
                MapEditorNPC.hideVisualBounds()
            settings.setValue("mapeditor/ShowNPCVisualBounds", False)
        else: 
            if self.state.mode != common.MODEINDEX.GAME:
                MapEditorNPC.showVisualBounds()
            settings.setValue("mapeditor/ShowNPCVisualBounds", True)
    
    def toggleNPCCollisionBounds(self):
        settings = QSettings()
        if MapEditorNPC.collisionBoundsEnabled:
            if self.state.mode != common.MODEINDEX.GAME:
                MapEditorNPC.hideCollisionBounds()
            settings.setValue("mapeditor/ShowNPCCollisionBounds", False)
        else: 
            if self.state.mode != common.MODEINDEX.GAME:
                MapEditorNPC.showCollisionBounds()
            settings.setValue("mapeditor/ShowNPCCollisionBounds", True)
    
    def toggleNPCForegroundMask(self):
        settings = QSettings()
        if self.parent().npcForegroundMaskAction.isChecked():
            settings.setValue("mapeditor/MaskNPCsWithForeground", True)
        else:
            settings.setValue("mapeditor/MaskNPCsWithForeground", False)
            
        self.update()
    
    def toggleEnemySpawnLines(self):
        settings = QSettings()
        if checked := self.parent().enemyLinesAction.isChecked():
            settings.setValue("mapeditor/ShowEnemyLines", True)
        else:
            settings.setValue("mapeditor/ShowEnemyLines", False)
        if self.state.mode == common.MODEINDEX.ENEMY:
            if checked:
                self.hoverSpawnLines.show()
            else:
                self.hoverSpawnLines.hide()
        self.update()
    
    def toggleWarpIDs(self):
        settings = QSettings()
        if MapEditorWarp.warpIDsEnabled:
            MapEditorWarp.hideWarpIDs()
            settings.setValue("mapeditor/ShowWarpIDs", False)
        else:
            MapEditorWarp.showWarpIDs()
            settings.setValue("mapeditor/ShowWarpIDs", True)
        
    def setGrid(self, id: int, indexOverride: int = -1):
        settings = QSettings()
        
        if indexOverride == -1:
            mode = self.state.mode
        else:
            mode = indexOverride
            
        type = "32"
        if mode in [common.MODEINDEX.TILE, common.MODEINDEX.GAME]:
            type = "32"
        elif mode in [common.MODEINDEX.WARP, common.MODEINDEX.TRIGGER, common.MODEINDEX.HOTSPOT]:
            type = "8"
        elif mode in [common.MODEINDEX.SECTOR]:
            type = "256128"
        elif mode in [common.MODEINDEX.ENEMY]:
            type = "64"
    
        self.grid.setBrush(QBrush(QPixmap(f":/grids/{type}grid{id}.png")))
        settings.setValue("mapeditor/GridStyle", id)
        self._currentGrid = id
    
    def toggleSpawnLineDir(self, dir: common.DIRECTION4):
        match dir:
            case common.DIRECTION4.up:
                self.hoverSpawnLines.topLine.setVisible(not self.hoverSpawnLines.topLine.isVisible())
                self.hoverSpawnLines.BGTopLine.setVisible(not self.hoverSpawnLines.BGTopLine.isVisible())
            case common.DIRECTION4.down:
                self.hoverSpawnLines.bottomLine.setVisible(not self.hoverSpawnLines.bottomLine.isVisible())
                self.hoverSpawnLines.BGBottomLine.setVisible(not self.hoverSpawnLines.BGBottomLine.isVisible())
            case common.DIRECTION4.left:
                self.hoverSpawnLines.leftLine.setVisible(not self.hoverSpawnLines.leftLine.isVisible())
                self.hoverSpawnLines.BGLeftLine.setVisible(not self.hoverSpawnLines.BGLeftLine.isVisible())
            case common.DIRECTION4.right:
                self.hoverSpawnLines.rightLine.setVisible(not self.hoverSpawnLines.rightLine.isVisible())
                self.hoverSpawnLines.BGRightLine.setVisible(not self.hoverSpawnLines.BGRightLine.isVisible())
        self.update()

    def populateNPCs(self):
        for i in self.projectData.npcinstances:
            npc = self.projectData.getNPC(i.npcID)
            spr = self.projectData.getSprite(npc.sprite)
            inst = MapEditorNPC(i.coords, i.npcID, i.uuid, spr)
            inst.setSprite(spr, common.DIRECTION8[npc.direction], 0)
            
            if not i.npcID in self.placedNPCsByID:
                self.placedNPCsByID[i.npcID] = [inst,]
            else:
                self.placedNPCsByID[i.npcID].append(inst)

            if not i.uuid in self.placedNPCsByUUID:
                self.placedNPCsByUUID[i.uuid] = inst
                self.addItem(inst)
            else:
                logging.warning(f"Can't add an NPC twice! id: {i.uuid}")
            
            QApplication.processEvents()

    def populateTriggers(self):
        self.imgTriggerDoor = QPixmap(":/triggers/triggerDoor.png")
        self.imgTriggerEscalator = QPixmap(":/triggers/triggerEscalator.png")
        self.imgTriggerLadder = QPixmap(":/triggers/triggerLadder.png")
        self.imgTriggerObject = QPixmap(":/triggers/triggerObject.png")
        self.imgTriggerPerson = QPixmap(":/triggers/triggerPerson.png")
        self.imgTriggerRope = QPixmap(":/triggers/triggerRope.png")
        self.imgTriggerStairway = QPixmap(":/triggers/triggerStairway.png")
        self.imgTriggerSwitch = QPixmap(":/triggers/triggerSwitch.png")
        self.imgTriggerDest = QPixmap(":/triggers/triggerDestination.png")

        for i in self.projectData.triggers:
            trigger_ = trigger.MapEditorTrigger(i.coords, i.uuid)

            match type(i.typeData):
                case trigger.TriggerDoor:
                    trigger_.setPixmap(self.imgTriggerDoor)
                case trigger.TriggerEscalator:
                    trigger_.setPixmap(self.imgTriggerEscalator)
                case trigger.TriggerLadder:
                    trigger_.setPixmap(self.imgTriggerLadder)
                case trigger.TriggerObject:
                    trigger_.setPixmap(self.imgTriggerObject)
                case trigger.TriggerPerson:
                    trigger_.setPixmap(self.imgTriggerPerson)
                case trigger.TriggerRope:
                    trigger_.setPixmap(self.imgTriggerRope)
                case trigger.TriggerStairway:
                    trigger_.setPixmap(self.imgTriggerStairway)
                case trigger.TriggerSwitch:
                    trigger_.setPixmap(self.imgTriggerSwitch)
                case _: # should never happen
                    logging.warning(f"Unknown trigger type {i.typeData}")

            self.addItem(trigger_)
            self.placedTriggersByUUID[i.uuid] = trigger_

            QApplication.processEvents()
            
    def populateHotspots(self):
        for i in self.projectData.hotspots:
            hotspot = MapEditorHotspot(i.id, i.start, i.end, i.colour)
            self.placedHotspots.append(hotspot)
            self.addItem(hotspot)
            
    def populateWarps(self):
        self.warpPixmap = QPixmap(":/ui/warp.png")
        self.teleportPixmap = QPixmap(":/ui/teleport.png")
        for i in self.projectData.warps:
            warp = MapEditorWarp(i.dest, i.id, self.warpPixmap, "warp")
            warp.setText("W"+str(i.id).zfill(3))
            self.addItem(warp)
            self.placedWarps.append(warp)
            
        for i in self.projectData.teleports:
            teleport = MapEditorWarp(i.dest, i.id, self.teleportPixmap, "teleport")
            teleport.setText("TP`"+str(i.id).zfill(2))
            self.addItem(teleport)
            self.placedTeleports.append(teleport)
            
    def parent(self) -> "MapEditor": # for typing
        return super().parent()
    