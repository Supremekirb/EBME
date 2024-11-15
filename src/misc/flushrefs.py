# a few classes I have (probably stupidly) kept a list of instances
# this is so I can apply operations to all of them at once, such as hex input spinners.
# buuuuuuuuuuut that is kinda sorta a little memory leak I think
# so, let's do it this way 

# (P.S. I don't think weakref's tools will do what I need..)

# I don't even know that this will work, or even if there is a problem in the first place
# as usual... better safe than sorry, right?

from src.objects import enemy, npc, trigger, warp
from src.widgets import input

def flush():
    npc.MapEditorNPC.instances = []
    enemy.MapEditorEnemyTile.instances = []
    enemy.MapEditorEnemyTile.brushes = {} # yes this is a dict
    enemy.EnemyMapGroup.colours = [] # this is probably patching a normal bug
    trigger.MapEditorTrigger.instances = []
    warp.MapEditorWarp.instances = []
    input.BaseChangerSpinbox.instances = []
