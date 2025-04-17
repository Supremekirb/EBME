from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.trigger import (Trigger, TriggerDoor, TriggerEscalator,
                                 TriggerLadder, TriggerObject, TriggerPerson,
                                 TriggerRope, TriggerStairway, TriggerSwitch)


class TriggerModule(YMLResourceDataModule):
    NAME = "triggers"
    MODULE = "eb.DoorModule"
    RESOURCE = "map_doors"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, map_doors):
        triggerList = []
        for y, row in map_doors.items():
            for x, triggers in row.items():
                biscectorPos = EBCoords.fromBisector(x, y)
                if triggers != None:
                    for trigger in triggers:
                        match trigger["Type"]:
                            case "door":
                                triggerData = TriggerDoor(EBCoords.fromWarp(trigger["Destination X"], trigger["Destination Y"]), trigger["Direction"],
                                                                trigger["Event Flag"], trigger["Style"], trigger["Text Pointer"])
                            case "escalator":
                                triggerData = TriggerEscalator(trigger["Direction"])
                            case "ladder":
                                triggerData = TriggerLadder()
                            case "object":
                                triggerData = TriggerObject(trigger["Text Pointer"])
                            case "person":
                                triggerData = TriggerPerson(trigger["Text Pointer"])
                            case "rope":
                                triggerData = TriggerRope()
                            case "stairway":
                                triggerData = TriggerStairway(trigger["Direction"])
                            case "switch":
                                triggerData = TriggerSwitch(trigger["Text Pointer"], trigger["Event Flag"])
                            case _:
                                raise ValueError(f"Unknown trigger type {trigger['Type']}")

                        warpOffset = EBCoords.fromWarp(trigger["X"], trigger["Y"])
                        absolutePos = biscectorPos+warpOffset
                        triggerList.append(Trigger(absolutePos, triggerData))
        
        data.triggers = triggerList
    
    
    def _resourceSave(data: ProjectData):
        triggers_yml = {}
        for c in range(40):
            triggers_yml[c] = {}
            for r in range(32):
                triggers_yml[c][r] = []
        
        for i in data.triggers:
            buildDict = {}

            pos = i.posToMapDoorsFormat()

            buildDict["X"] = pos[2]
            buildDict["Y"] = pos[3]

            match i.typeData:
                case TriggerDoor():
                    buildDict["Type"] = "door"
                    buildDict["Destination X"] = i.typeData.destCoords.coordsWarp()[0]
                    buildDict["Destination Y"] = i.typeData.destCoords.coordsWarp()[1]
                    buildDict["Direction"] = i.typeData.dir
                    buildDict["Event Flag"] = i.typeData.flag
                    buildDict["Style"] = i.typeData.style
                    buildDict["Text Pointer"] = i.typeData.textPointer
                case TriggerEscalator():
                    buildDict["Type"] = "escalator"
                    buildDict["Direction"] = i.typeData.direction
                case TriggerLadder():
                    buildDict["Type"] = "ladder"
                case TriggerObject():
                    buildDict["Type"] = "object"
                    buildDict["Text Pointer"] = i.typeData.textPointer
                case TriggerPerson():
                    buildDict["Type"] = "person"
                    buildDict["Text Pointer"] = i.typeData.textPointer
                case TriggerRope():
                    buildDict["Type"] = "rope"
                case TriggerStairway():
                    buildDict["Type"] = "stairway"
                    buildDict["Direction"] = i.typeData.direction
                case TriggerSwitch():
                    buildDict["Type"] = "switch"
                    buildDict["Event Flag"] = i.typeData.flag
                    buildDict["Text Pointer"] = i.typeData.textPointer

            triggers_yml[pos[1]][pos[0]].append(buildDict)

        for c in range(40):
            for r in range(32):
                if triggers_yml[c][r] == []: triggers_yml[c][r] = None
        
        return triggers_yml