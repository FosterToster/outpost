from enum import EnumMeta, Enum
from .rules import AND, OR

class ModelFieldMeta(EnumMeta):
    def __getattr__(class_, name: str):
        try:
            return super().__getattr__(name)
        except AttributeError:
            raise AttributeError(f'Model "{class_.__name__}" does not have field "{name}"')
    
        

class ModelField(Enum, metaclass=ModelFieldMeta):

    def __or__(self, other):
        if isinstance(other, OR):
            return OR(self, *other.rules)
        else:
            return OR(self, other)

    def __and__(self, other):
        if isinstance(other, AND):
            return AND(self, *other.rules)
        else:
            return AND(self, other)
    ...

