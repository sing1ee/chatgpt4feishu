#!/usr/bin/env python3.8
import json
class Obj:
    # constructor
    def __init__(self, d):
        self.__dict__.update(d)
        
def dict2obj(d):
    return json.loads(json.dumps(d), object_hook=Obj)


def obj2dict(obj):
    if isinstance(obj, dict):
        return { k: obj2dict(v) for k, v in obj.items() }
    elif hasattr(obj, "_ast"):
        return obj2dict(obj._ast())
    elif not isinstance(obj, str) and hasattr(obj, "__iter__"):
        return [ obj2dict(v) for v in obj ]
    elif hasattr(obj, "__dict__"):
        return {
            k: obj2dict(v)
            for k, v in obj.__dict__.items()
            if not callable(v) and not k.startswith('_')
        }
    else:
        return obj