from enum import Enum


class InstanceTypeEnum(Enum):
    instance_type: type

    def __new__(cls, value, instance_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.instance_type = instance_type
        return obj
