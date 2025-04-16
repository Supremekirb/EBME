from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule

class EnemySpriteModule(YMLCoilsnakeResourceLoadModule):
    NAME = "enemy sprites"
    MODULE = "eb.EnemyModule"
    RESOURCE = "enemy_configuration_table"
    
    def _resourceLoad(data, enemy_configuration_table):
        enemySprites = []
        for enemy in enemy_configuration_table.values():       
            enemySprites.append(int(enemy["Overworld Sprite"]))

        data.enemySprites = enemySprites