from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

import src.misc.common as common
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor


class MapEditorStatus(QWidget):
    """Status bar displaying mouse coords and other basic info"""
    def __init__(self, parent: "MapEditor"):
        super().__init__(parent)

        self.pixelCoords = QLabel("Pixel: ----", self)
        self.warpCoords = QLabel("Warp: ----", self)
        self.tileCoords = QLabel("Tile: ----", self)
        self.tileID = QLabel("Tile ID: ----", self)
        self.sectorCoords = QLabel("Sector: ----", self)
        self.sectorID = QLabel("Sector ID: ----", self)
        self.enemyCoords = QLabel("Enemy: ----", self)
        self.zoom = QLabel("Zoom: 100%", self)

        self.contentLayout = QGridLayout(self)
        self.contentLayout.addWidget(self.pixelCoords, 0, 0, alignment=Qt.AlignLeft)
        self.contentLayout.addWidget(self.warpCoords, 0, 1, alignment=Qt.AlignLeft)
        self.contentLayout.addWidget(self.tileCoords, 0, 2, alignment=Qt.AlignLeft)
        self.contentLayout.addWidget(self.tileID, 0, 3, alignment=Qt.AlignLeft)
        self.contentLayout.addWidget(self.sectorCoords, 0, 4, alignment=Qt.AlignLeft)
        self.contentLayout.addWidget(self.sectorID, 0, 5, alignment=Qt.AlignLeft)
        self.contentLayout.addWidget(self.enemyCoords, 0, 6, alignment=Qt.AlignLeft)
        self.contentLayout.addWidget(self.zoom, 0, 7, alignment=Qt.AlignRight)

        self.contentLayout.setColumnStretch(6, 1)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)

        self.contentLayout.setColumnMinimumWidth(0, 110)
        self.contentLayout.setColumnMinimumWidth(1, 110)
        self.contentLayout.setColumnMinimumWidth(2, 110)
        self.contentLayout.setColumnMinimumWidth(3, 110)
        self.contentLayout.setColumnMinimumWidth(4, 110)
        self.contentLayout.setColumnMinimumWidth(5, 110)
        self.contentLayout.setColumnMinimumWidth(6, 110)

        self.setLayout(self.contentLayout)

        self.setFixedHeight(self.sizeHint().height())

    def updateCoords(self, coords = EBCoords):
        """Update labels for coordinates

        Args:
            x (int): X position (pixels)
            y (int): Y position (pixels)
        """
        x = coords.x
        y = coords.y

        if x < 0 or y < 0 or x > common.EBMAPWIDTH-1 or y > common.EBMAPHEIGHT-1:
            self.pixelCoords.setText("Pixel: ----")
            self.warpCoords.setText("Warp: ----")
            self.tileCoords.setText("Tile: ----")
            self.tileID.setText("Tile ID: ----")
            self.sectorCoords.setText("Sector: ----")
            self.sectorID.setText("Sector ID: ----")
            self.enemyCoords.setText("Enemy: ----")

        else:
            self.pixelCoords.setText(f"Pixel: {coords.coords()}")
            self.warpCoords.setText(f"Warp: {coords.coordsWarp()}")
            self.tileCoords.setText(f"Tile: {coords.coordsTile()}")
            self.tileID.setText(f"Tile ID: {self.parent().projectData.getTile(coords).tile}")
            self.sectorCoords.setText(f"Sector: {coords.coordsSector()}")
            self.sectorID.setText(f"Sector ID: {self.parent().projectData.getSector(coords).id}")
            self.enemyCoords.setText(f"Enemy: {coords.coordsEnemy()}")


    def setZoom(self, zoom: int):
        """Update label for zoom level

        Args:
            zoom (int): Zoom level (%)
        """
        self.zoom.setText(f"Zoom: {zoom}%")

    # for type checking
    def parent(self) -> "MapEditor":
        return super().parent()