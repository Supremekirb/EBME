from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.misc.coords import EBCoords
from src.objects.trigger import (Trigger, TriggerDoor, TriggerEscalator,
                                 TriggerLadder, TriggerObject, TriggerPerson,
                                 TriggerRope, TriggerStairway, TriggerSwitch)


class TriggerModule(YMLCoilsnakeResourceLoadModule):
    NAME = "triggers"
    MODULE = "eb.DoorModule"
    RESOURCE = "map_doors"
    
    def _resourceLoad(data, map_doors):
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