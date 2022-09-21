from typing import Tuple, TypeVar, Union, List, Dict, Any, Iterable, Callable
from typing import Generic, Type
from dataclasses import dataclass

from .rules import AND, NoRequirements, Require, Rule
from .utils import ModelField
from .classproperty import classproperty
from .exceptions import AbstractError, NoPromisedValidator


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
    method: Callable[[Any], Any] = None
    validator: 'ABCOutpost' = None
    check_result_type: bool = True

    def validate(self, value):
        if self.method:
            return self.method(value)
        else:
            return self.validator.validate(value)


TOriginalModel = TypeVar('TOriginalModel')

# constant class to help exclude missing fields
class _EXCLUDE_MISSING:
        ...

class ConfigurationFieldset:
    def __init__(self, fields: ModelField = None, original_model: Any = None) -> None:
        self.__fields = fields
        self.__original_model = original_model
        self.__missing_value = _EXCLUDE_MISSING
        self.__raise_readonly = None
        self.__raise_unnecessary = None
        self.__readonly = list()
        self.__defaults = dict()
        self.__validators = dict()
        self.__combinators = list()
        self.__requirements = NoRequirements()


    __fields: ModelField = None
    __original_model: Any = None
    __missing_value: Any = _EXCLUDE_MISSING
    __raise_readonly:bool = None
    __raise_unnecessary:bool = None
    __readonly: List[ModelField] = None
    __defaults: Dict[ModelField, Any] = None
    __validators: Dict[ModelField, 'Validator'] = None
    __combinators: List['Combinator'] = None
    __requirements: Rule = None
    __field_generator__: 'IFieldGenerator'
    __annotation_generator__: 'IAnnotationGenerator'

    @property
    def fields(self) -> ModelField:
        return self.__fields

    @property
    def model(self) -> Any:
        return self.__original_model

    @property
    def missing_value(self) -> Union[Any, _EXCLUDE_MISSING]:
        return self.__missing_value
    
    @missing_value.setter
    def missing_value(self, value):
        self.__missing_value = value

    @property
    def raise_readonly(self) -> bool:
        return self.__raise_readonly

    @raise_readonly.setter
    def raise_readonly(self, value:bool):
        self.__raise_readonly = value

    @property
    def raise_unnecessary(self) -> bool:
        return self.__raise_unnecessary
    
    @raise_unnecessary.setter
    def raise_unnecessary(self, value:bool):
        self.__raise_unnecessary = value    

    @property
    def readonly(self) -> List[ModelField]:
        return self.__readonly

    @readonly.setter
    def readonly(self, value: List[ModelField]):
        self.__readonly = value

    @property
    def defaults(self) -> Dict[ModelField, Any]:
        return self.__defaults
    
    @defaults.setter
    def defaults(self, value: Dict[ModelField, Any]):
        self.__defaults = value

    @property
    def requirements(self) -> Rule:
        return self.__requirements

    @requirements.setter
    def requirements(self, value: Union[Rule, ModelField]):
        if isinstance(value, ModelField):
            self.__requirements = Require(value)
        elif isinstance(value, Rule):
            self.__requirements = value
        else:
            raise TypeError(f'{type(value)} is not Rule or ModelField')

    @property
    def combinators(self) -> List['Combinator']:
        return self.__combinators

    @combinators.setter
    def combinators(self, value:List['Combinator']):
        self.__combinators = value

    @property
    def validators(self) -> Dict[ModelField, 'Validator']:
        return self.__validators

    @validators.setter
    def validators(self, value: Dict[ModelField, 'Validator']):
        self.__validators = value

    def inherit(self, child:'ConfigurationFieldset'):
        if self.fields is not None:
            if self.fields != child.fields:
                raise AbstractError('OutpostValidators can`t be inherited from different hierarchies.')
        else:
            self.__fields = child.fields
            self.__original_model = child.model
        
        self.__raise_readonly = child.raise_readonly or self.raise_readonly or False
        self.__raise_unnecessary = child.raise_unnecessary or self.raise_unnecessary or False
        self.__missing_value = child.missing_value if not (child.missing_value is _EXCLUDE_MISSING) else self.missing_value
        self.__readonly = [*self.__readonly, *child.readonly]
        self.__defaults = {**self.__defaults, **child.defaults}
        self.__validators = {**self.__validators, **child.validators}
        self.__combinators = [*self.combinators, *child.combinators]
        self.__field_generator__ = child.__field_generator__
        self.__annotation_generator__ = child.__annotation_generator__

        all_rules = list()

        if not isinstance(self.__requirements, NoRequirements):
            if isinstance(self.__requirements, AND):
                all_rules.extend(self.__requirements.rules)
            else:
                all_rules.append(self.__requirements)

        if not isinstance(child.requirements, NoRequirements):
            if isinstance(child.requirements, AND):
                all_rules.extend(child.requirements.rules)
            else:
                all_rules.append(child.requirements)

        if len(all_rules) > 0:
            self.__requirements = AND(*all_rules)
        else:
            self.__requirements = NoRequirements()
        
        return self


class RWConfiguration(ConfigurationFieldset):
    
    def to_RO(self):
        return ROConfiguration().inherit(self)


class ROConfiguration(ConfigurationFieldset):
    
    @property
    def missing_value(self) -> Union[Any, _EXCLUDE_MISSING]:
        return super().missing_value
    
    @missing_value.setter
    def missing_value(self, _):
        raise AttributeError('can`t set attribute')
        
    @property
    def raise_readonly(self) -> bool:
        return super().raise_readonly

    @raise_readonly.setter
    def raise_readonly(self, _):
        raise AttributeError('can`t set attribute')

    @property
    def raise_unnecessary(self) -> bool:
        return super().raise_unnecessary
    
    @raise_unnecessary.setter
    def raise_unnecessary(self, _):
        raise AttributeError('can`t set attribute')

    @property
    def readonly(self) -> Tuple[ModelField]:
        return tuple(super().readonly)

    @readonly.setter
    def readonly(self, _):
        raise AttributeError('can`t set attribute')

    @property
    def defaults(self) -> Dict[ModelField, Any]:
        return {**super().defaults}
    
    @defaults.setter
    def defaults(self, _):
        raise AttributeError('can`t set attribute')

    @property
    def requirements(self) -> Rule:
        return super().requirements

    @requirements.setter
    def requirements(self, _):
        raise AttributeError('can`t set attribute')

    @property
    def combinators(self) -> Tuple['Combinator']:
        return tuple(super().combinators)

    @combinators.setter
    def combinators(self, _):
        raise AttributeError('can`t set attribute')

    @property
    def validators(self) -> Dict[ModelField, 'Validator']:
        return {**super().validators}

    @validators.setter
    def validators(self, _):
        raise AttributeError('can`t set attribute')

    def to_RW(self):
        return RWConfiguration().inherit(self)
    

class GenericValidatorProvider(RWConfiguration, Generic[TOriginalModel]):
    __fields: TOriginalModel
    __original_model: TOriginalModel

    @property
    def fields(self) -> TOriginalModel:
        return super().fields

    def __init__(self, model:TOriginalModel, field_generator: 'IFieldGenerator', annotation_generator: 'IAnnotationGenerator'):
        self.__field_generator__ = field_generator(model)
        self.__annotation_generator__ = annotation_generator(model)
        super().__init__(self.__generate_model_proxy__(self.__field_generator__), model)

    @staticmethod
    def __generate_model_proxy__(field_generator: 'IFieldGenerator'):
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

    __validators__ = list()

    @staticmethod
    def inherit_configurations(superclasses:Iterable['ABCOutpost'], current: GenericValidatorProvider = None) -> RWConfiguration:
        result = RWConfiguration()

        for superclass in superclasses:
            if not issubclass(superclass, ABCOutpost):
                raise AbstractError('Outpost validator must be inherited only from other Outpost validator(s)')

            if superclass.__config__ is None:
                continue

            result.inherit(superclass.__config__)
        
        if current:
            result.inherit(current)
            current.clear()

        return result

    def __getitem__(class_, *args) -> '_PromisedValidator':
        if len(args) != 1:
            raise AbstractError(f'Usage: Outpost["ValidatorName"]')
        validator_name = args[0]
        if not isinstance(validator_name, str):
            raise AbstractError(f'Object {validator_name} can`t be used as validator name.')

        return _PromisedValidator(args[0])

    def __new__(class_, name_:str, superclasses_:list, dict_:dict):
        # just create abc classes
        if name_ in ('ABCOutpost', 'Outpost', '_PromisedValidator'):
            return super().__new__(class_, name_, superclasses_, dict_)

        if name_ in class_.__validators__:
            raise AbstractError(f'Name collision: validator named "{name_}" alredy defined.') 
        else:
            class_.__validators__.append(name_)
            
        result_class = super().__new__(class_, name_, superclasses_, dict_)
        
        current_config:GenericValidatorProvider = None
        for field in dict_.values():
            if isinstance(field, GenericValidatorProvider):
                current_config = field
                break

        result_class.__config__ = class_.inherit_configurations(superclasses_, current_config).to_RO()

        # if result_class.__config__ is None:
        #     if current_config is None:
        #         raise AbstractError(f'Outpost validator class "{name_}" does not have any validation provider. Define any static as: config = OutpostProvider.from_model(model: dataclass)')
        #     else:
        #         result_class.__config__ = ValidationConfig.from_child(current_config)
        #         current_config.clear()
        # else:
        #     if current_config is not None:
        #         if current_config.fields != result_class.__config__.__fields__:
        #             raise AbstractError(f'Inherited outpost validator "{name_}" have own validation provider. Use OutpostProvider from superclass.')
        #         result_class.__config__ = ValidationConfig.inherit_config(result_class.__config__, current_config)
        #         current_config.clear()

        return result_class


class ABCOutpost(metaclass=OutpostMeta):
    __config__: ROConfiguration = None

    @classproperty
    def fields(class_):
        return class_.__config__.fields
    
    @classproperty
    def model(class_):
        return class_.__config__.model

    @classproperty
    def missing_value(class_) -> Union[Any, _EXCLUDE_MISSING]:
        return class_.__config__.missing_value

    @classproperty
    def raise_readonly(class_) -> bool:
        return class_.__config__.raise_readonly

    @classproperty
    def raise_unnecessary(class_) -> bool:
        return class_.__config__.raise_unnecessary    

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
    def validators(class_) -> Dict[ModelField, 'Validator']:
        return class_.__config__.validators


class _PromisedValidator(ABCOutpost):
    def __init__(self, validator_name:str) -> None:
        self.name = validator_name
        self.__validator = None

    @staticmethod
    def __find_validator__(obj:Type[ABCOutpost], name:str):
        for subclass in obj.__subclasses__():
            if subclass.__name__ == name:
                return subclass
        else:
            raise NoPromisedValidator(f'Promised validator "{name}" is not found')

    @property
    def assigned_validator(self):
        if self.__validator is None:
            for subclass in ABCOutpost.__subclasses__():
                try:
                    self.__validator = self.__find_validator__(subclass, self.name)
                    break
                except NoPromisedValidator:
                    continue
            else:
                raise NoPromisedValidator(f'Promised validator "{self.name}" was never defined')

        return self.__validator

    def __getattr__(self, attr):
        return getattr(self.assigned_validator, attr)





class IAnnotationGenerator:
    def __init__(self, model:TOriginalModel) -> None:
        self.model = model
        pass

    def get_annotation(self, field: ModelField) -> type:
        pass


class IFieldGenerator:
    def __init__(self, model:TOriginalModel) -> None:
        self.model = model
        pass

    def all_fields(self) -> Iterable[str]:
        pass