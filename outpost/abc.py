from typing import Tuple, TypeVar, Union, List, Dict, Any, Iterable, Callable
from typing import Generic
from dataclasses import dataclass

from .rules import AND, _RequireMany, NoRequirements, Require, Rule
from .utils import ModelField
from .classproperty import classproperty
from .exceptions import AbstractError, NativeValidationError, ValidationError


@dataclass
class Combinator:
    fields: Iterable[ModelField]
    method: Callable[[Any], None]

    def combine(self, dataset):
        values = list()
        for field in self.fields:
            if not (field in dataset.keys()):
                break
            else:
                values.append(dataset[field])
        else:
            self.method(*values)


@dataclass
class Validator:
    field: ModelField
    method: Callable[[Any], Any] = None
    validator: 'ABCOutpost' = None
    check_result_type: bool = True

    def validate(self, value):
        if self.method:
            return self.method(value)
        else:
            if isinstance(value, dict):
                return self.validator.validate(value)
            else:
                raise NativeValidationError('Invalid typecast. Object required.')


TOriginalModel = TypeVar('TOriginalModel')

class ValidationFields:
    __fields__: ModelField = None
    __original_model__: Any = None
    __readonly__: List[ModelField] = None
    __defaults__: Dict[ModelField, Any] = None
    __validators__: List['Validator'] = None
    __combinators__: List['Combinator'] = None
    __requirements__: Rule = None


class ValidationProps:
    @property
    def fields(self) -> ModelField:
        return self.__fields__

    @property
    def model(self) -> Any:
        return self.__original_model__

    @property
    def readonly(self) -> List[ModelField]:
        return self.__readonly__

    @readonly.setter
    def __set_readonly__(self, value: List[ModelField]):
        self.__readonly__ = value

    @property
    def defaults(self) -> Dict[ModelField, Any]:
        return self.__defaults__
    
    @defaults.setter
    def __set_defaults__(self, value: Dict[ModelField, Any]):
        self.__defaults__ = value

    @property
    def requirements(self) -> Rule:
        return self.__requirements__

    @requirements.setter
    def __set_requirements__(self, value: Union[Rule, ModelField]):
        if isinstance(value, ModelField):
            self.__requirements__ = Require(value)
        elif isinstance(value, Rule):
            self.__requirements__ = value
        else:
            raise TypeError(f'{type(value)} is not Rule or ModelField')

    @property
    def combinators(self) -> List['Combinator']:
        return self.__combinators__

    @property
    def validators(self) -> List['Validator']:
        return self.__validators__


class ValidationConfig(ValidationProps, ValidationFields):

    @property
    def readonly(self) -> Tuple[ModelField]:
        return tuple(super().readonly)

    @readonly.setter
    def __set_readonly__(self, value: List[ModelField]):
        raise AbstractError('Config is immutable')

    @property
    def defaults(self) -> Dict[ModelField, Any]:
        return {**super().defaults}

    @defaults.setter
    def __set_defaults__(self, value: Dict[ModelField, Any]):
        raise AbstractError('Config is immutable')

    @property
    def requirements(self) -> Rule:
        return super().requirements

    @requirements.setter
    def __set_requirements(self, _):
        raise AbstractError('Config is immutable')

    @property
    def combinators(self) -> Tuple['Combinator']:
        return tuple(super().combinators)
    
    @property
    def validators(self) -> Tuple['Validator']:
        return tuple(super().validators)

    @classmethod
    def from_child(class_, child:'ValidationConfig') -> 'ValidationConfig':
        result = class_()

        result.__fields__ = child.__fields__
        result.__original_model__ = child.__original_model__
        result.__readonly__ = child.__readonly__
        result.__defaults__ = child.__defaults__
        result.__validators__ = child.__validators__
        result.__combinators__ = child.__combinators__
        result.__requirements__ = child.__requirements__

        return result

    @classmethod
    def inherit_config(class_, parent: 'ValidationConfig', child: 'ValidationConfig') -> 'ValidationConfig':
        result = class_()

        result.__fields__ = parent.fields
        result.__original_model__ = parent.model
        result.__readonly__ = [*parent.readonly, *child.readonly]
        result.__defaults__ = {**parent.defaults, **child.defaults}
        result.__validators__ = [*parent.validators, *child.validators]
        result.__combinators__ = [*parent.combinators, *child.combinators]

        all_rules = list()

        if not isinstance(parent.requirements, NoRequirements):
            if isinstance(parent.requirements, AND):
                all_rules.extend(parent.requirements.rules)
            else:
                all_rules.append(parent.requirements)

        if not isinstance(child.requirements, NoRequirements):
            if isinstance(child.requirements, AND):
                all_rules.extend(child.requirements.rules)
            else:
                all_rules.append(child.requirements)

        if len(all_rules) > 0:
            result.__requirements__ = AND(*all_rules)
        else:
            result.__requirements__ = NoRequirements()
        
        return result



class GenericValidatorProvider(ValidationProps, ValidationFields, Generic[TOriginalModel]):
    __fields__: TOriginalModel
    __original_model__: TOriginalModel

    @property
    def fields(self) -> TOriginalModel:
        return self.__fields__

    def __init__(self, model:TOriginalModel):
        self.__original_model__ = model
        self.__fields__ = self.__generate_model_proxy__(self.__original_model__)

    @staticmethod
    def __generate_model_proxy__(model:TOriginalModel):
        ...

    def require(self, expression:Union[Rule, ModelField]):
        ...

    def validator(self, field:ModelField, validator:'ABCOutpost' = None, check_result_type:bool = True):
        ...

    def combine(self, *fields:ModelField):
        ...

    def clear(self):
        ...


class OutpostMeta(type):

    def __new__(class_, name_:str, superclasses_:list, dict_:dict):
        # just create abc classes
        if name_ in ('ABCOutpost', 'Outpost'):
            return super().__new__(class_, name_, superclasses_, dict_)

        # new_dict = dict()

        config:GenericValidatorProvider = None
        for field in dict_.values():
            if isinstance(field, GenericValidatorProvider):
                config = field
                break
            
        result_class = super().__new__(class_, name_, superclasses_, dict_)

        if result_class.__config__ is None:
            if config is None:
                raise AbstractError(f'Outpost validator class "{name_}" does not have any validation provider. Define any static as: config = OutpostProvider.from_model(model: dataclass)')
            else:
                result_class.__config__ = ValidationConfig.from_child(config)
                config.clear()
        else:
            if config is not None:
                if config.fields != result_class.__config__.__fields__:
                    raise AbstractError(f'Inherited outpost validator "{name_}" have own validation provider. Use OutpostProvider from superclass.')
                result_class.__config__ = ValidationConfig.inherit_config(result_class.__config__, config)
                config.clear()

        return result_class


class ABCOutpost(metaclass=OutpostMeta):
    __config__: ValidationConfig = None


    @classproperty
    def fields(class_):
        return class_.__config__.fields
    
    @classproperty
    def model(class_):
        return class_.__config__.model

    @classproperty
    def readonly(class_) -> Tuple[ModelField]:
        return class_.__config__.readonly

    @classproperty
    def defaults(class_) -> Dict[ModelField, Any]:
        return class_.__config__.defaults
    
    @classproperty
    def requirements(class_) -> Rule:
        return class_.__config__.requirements

    @classproperty
    def combinators(class_) -> Tuple['Combinator']:
        return class_.__config__.combinators

    @classproperty
    def validators(class_) -> Tuple['Validator']:
        return class_.__config__.validators
