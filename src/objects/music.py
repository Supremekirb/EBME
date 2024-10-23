from PySide6.QtWidgets import QTreeWidgetItem

from src.misc import icons


class MapMusicEntry:
    """Flag + Music ID combo for MapMusicHierarchy"""
    def __init__(self, flag: int, music: int):
        self.flag = flag
        self.music = music

class MapMusicHierarchy:
    """Map music priority hierarchy"""
    def __init__(self, id: int):
        self.id = id
        self.entries: list[MapMusicEntry] = []
    
    def addEntry(self, entry: MapMusicEntry):
        self.entries.append(entry)
        
    def removeEntry(self, entry: MapMusicEntry):
        self.entries.remove(entry)
        
    def moveEntryUp(self, entry: MapMusicEntry|int):
        """Shift an entry up in the hierachy by one

        Args:
            entry (MapMusicEntry | int): The entry to move. Can be an entry object or an index.
        """
        if isinstance(entry, MapMusicEntry):
            index = self.entries.index(entry)
        else:
            index = entry
            
        self.moveEntryTo(index, index+1)
    
    def moveEntryDown(self, entry: MapMusicEntry|int):
        """Shift an entry down in the hierachy by one

        Args:
            entry (MapMusicEntry | int): The entry to move. Can be an entry object or an index.
        """
        if isinstance(entry, MapMusicEntry):
            index = self.entries.index(entry)
        else:
            index = entry
        
        self.moveEntryTo(index, index-1)
    
    def moveEntryTo(self, entry: MapMusicEntry|int, target: int):
        """Shift an entry to a specified index. It will be inserted to the left of the item at this index.

        Args:
            entry (MapMusicEntry | int): The entry to move. Can be an entry object or an index.
            target (int): The target location.
        """
        if isinstance(entry, MapMusicEntry):
            index = self.entries.index(entry)
        else:
            index = entry
        
        # if the target is greater than the entry, we need to insert it before the target otherwise it's to the right
        if target > index:
            target -= 1
        
        self.entries.insert(target, self.entires.pop(index))
        
class MapMusicHierarchyListItem(QTreeWidgetItem):
    def __init__(self, id: int):
        super().__init__([f"Entry {id}"])
        self.id = id
        
        self.setIcon(0, icons.ICON_MUSIC_LIST)

class MapMusicEntryListItem(QTreeWidgetItem):
    def __init__(self, flag: int, music: int):
        super().__init__([f"{music} Unknown", str(flag) if flag < 0x8000 else f"{flag - 0x8000} (Inverted)"])
        self.flag = flag
        self.music = music
        
        self.setIcon(0, icons.ICON_MUSIC)