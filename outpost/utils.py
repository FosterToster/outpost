from enum import EnumMeta, Enum
class ModelFieldMeta(EnumMeta):
    def __getattr__(class_, name: str):
        try:
            return super().__getattr__(name)
        except AttributeError:
            raise AttributeError(f'Model "{class_.__name__}" does not have field "{name}"')
    
        

class ModelField(Enum, metaclass=ModelFieldMeta):
    ...
