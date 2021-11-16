from typing import TypeVar, Union
try:
    from typing import Protocol
except ImportError:
    pass
    class ProtoMeta(type):
        def __getitem__(self, item):
            return item
        def __str__(self, _):
            return ''

    class Protocol(metaclass=ProtoMeta):
        ...
        
# from typing import Protocol

from .rules import Rule
from .utils import ModelField
# from .types import ABCOutpost

TOriginalModel = TypeVar('TOriginalModel')

class ValidatorProviderProtocol(Protocol[TOriginalModel]):
    __model__: TOriginalModel
    __original_model__ = None

    @property
    def model(self) -> TOriginalModel:
        return self.__model__

    @property
    def readonly(self) -> list:
        ...
    
    @readonly.setter
    def __set_readonly__(self, value:list):
        ...

    @property
    def defaults(self) -> dict:
        ...
    
    @defaults.setter
    def __set_defaults__(self, value: dict):
        ...

    def __init__(self, model:TOriginalModel):
        self.__model__ = model

    def require(class_, expression:Union[Rule, ModelField]):
        ...

    def validator(class_, field:ModelField, validator = None, check_result_type:bool = True):
        ...

    def combine(class_, *fields:ModelField):
        ...

