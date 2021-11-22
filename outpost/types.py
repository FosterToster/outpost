from typing import Iterable
from dataclasses import fields
from typing import Any, Union

from .type_validators import TypingModuleValidator

from .rules import AND, Rule, Require, NoRequirements
from .utils import ModelField


from .abc import GenericValidatorProvider, TOriginalModel, ABCOutpost, RWConfiguration, Validator, Combinator, _EXCLUDE_MISSING

from .exceptions import AbstractError, FieldRequirementException, NativeValidationError, UnexpectedError, ValidationError, NotNoneError


class OutpostProvider(GenericValidatorProvider):
    
    def require(self, expression: Union[Rule, ModelField]):
        if issubclass(type(expression), Rule):
            new_rule = expression
        elif issubclass(type(expression), ModelField):
            new_rule = Require(expression)

        if isinstance(self.requirements, NoRequirements):
            self.requirements = new_rule
        elif not isinstance(self.requirements, AND):
            self.requirements = AND(self.requirements, new_rule)
        else:
            self.requirements.append_rules(new_rule)

    def validator(self, field: ModelField, validator: 'Outpost' = None, check_result_type: bool = True):
        if validator is not None:
            self.validators[field] = Validator(validator=validator, check_result_type=check_result_type)
        else:
            def decorator(func):
                self.validators[field] = Validator(method=func, check_result_type=check_result_type)
                return func

            return decorator
    
    def combine(self, *fields: ModelField):
        def decorator(func):
            self.combinators.append(Combinator(fields=fields, method = func))
            return func

        return decorator
        
    @staticmethod
    def __generate_model_proxy__(model: TOriginalModel):
        #idk why Enum metaclass dont likes common dicts. _member_names field is needed for it, and there is nothing i can do
        class MemberDict(dict):
            _member_names = ()

        members = MemberDict()
 
        members.update(dict((field_.name, field_.name) for field_ in fields(model)))
        members._member_names = [key for key in members.keys()]
        # return type(f"{model.__name__}FieldsProxy", (Enum,), members)
        return type(f"{model.__name__}", (ModelField,), members)

    # def __init__(self, model: TOriginalModel):
    #     super().__init__(model)
    #     self.clear()

    def clear(self):
        self.missing_value = _EXCLUDE_MISSING
        self.raise_readonly = False
        self.raise_unnecessary = False
        self.readonly = list()
        self.defaults = dict()
        self.validators = dict()
        self.combinators = dict()
        self.requirements = NoRequirements()

    def __str__(self):
        return f'<{self.__class__.__qualname__} object>\n'+\
            f'\traise unnecessary: {self.raise_unnecessary}\n'+\
            f'\traise readonly: {self.raise_readonly}\n'+\
            f'\tmissing value: {self.missing_value}\n'+\
            f'\treadonly: {[f"{x}" for x in self.readonly]}\n'+\
            f'\tdefaults: {[f"{x[0]}: {x[1]}" for x in self.defaults.items()]}\n'+\
            f'\tvalidators: {[f"{x}" for x in self.validators]}\n'+\
            f'\tcombinators: {[f"{x}" for x in self.combinators]}\n'+\
            f'\trequirements: {self.requirements.text_rule()}'

    @classmethod
    def from_model(class_, model:TOriginalModel) -> GenericValidatorProvider[TOriginalModel]:
        return class_(model)




class ValidationContext:
    

    def __init__(self, config: RWConfiguration, parent_validator_name:str = "") -> None:
        self.parent_validator_name = parent_validator_name
        self.config: RWConfiguration = config
        self.fields_annotations = dict((field, self.get_annotation(field)) for field in self.config.fields)
        self.__dataset__ = None

    @property
    def dataset(self):
        if self.__dataset__ is None:
            raise NativeValidationError(f'value required')
        else:
            return self.__dataset__
    
    @dataset.setter
    def dataset(self, value):
        if not isinstance(value, dict):
            raise NativeValidationError('Invalid typecast. Object required.')
        else:
            self.__dataset__ = value


    def __enter__(self):
        return self

    def __exit__(self, *_):
        ...

    def _deep_execute_on_dataset(self, *, method=None, replace_field=False):
        result = dict()
        method = method if method is not None else lambda x: x
        for field in self.config.fields:
            result_field = field.name if replace_field else field
            if field in self.dataset:    
                if isinstance(self.dataset[field], ValidationContext):
                    result[result_field] = method(self.dataset[field])
                elif (isinstance(self.dataset[field], Iterable)) and not(isinstance(self.dataset[field], dict) or isinstance(self.dataset[field], str)):
                    result[result_field] = [method(tmp) if isinstance(tmp, ValidationContext) else tmp for tmp in self.dataset[field]]
                    if isinstance(self.dataset[field], tuple):
                        result[result_field] = tuple(result[result_field])
                else:
                    result[result_field] = self.dataset[field]
            else:
                if self.config.missing_value is _EXCLUDE_MISSING:
                    continue
                else:
                    result[result_field] = self.config.missing_value
        
        return result

    def current_dataset(self) -> dict:
        return self._deep_execute_on_dataset(method=lambda x: x.current_dataset(), replace_field=False)

    def export_dataset(self) -> dict:
        return self._deep_execute_on_dataset(method=lambda x: x.export_dataset(), replace_field=True)

    def enumerize_dataset(self, dataset: dict):
        if not isinstance(dataset, dict):
            raise NativeValidationError('Invalid typecast. Object required.')
        
        self.dataset = {**dataset}

        result = dict()
        
        for field in self.config.fields:
            if field in self.config.defaults:
                result[field] = self.config.defaults[field]

            if field.value in self.dataset:
                result[field] = self.dataset.pop(field.value)
            elif field in self.dataset:
                result[field] = self.dataset.pop(field)

        if self.config.raise_unnecessary and (len(self.dataset) > 0):
            raise ValidationError(f'Given dataset contains unnecessary fields: {[str(x) for x in self.dataset.keys()]}') 

        self.dataset = result
        return self

    def filter_readonly(self, dataset:dict = None,*, raise_readonly = False):
        if dataset is not None:
            self.enumerize_dataset(dataset)

        result = dict()

        for field in self.config.fields:
            if field in self.dataset:
                if field in self.config.readonly:
                    if raise_readonly:
                        raise ValidationError(f'Given dataset contains read-only field: {field.value}')
                    else:
                        continue
                else:
                    result[field] = self.dataset.pop(field)
                

        self.dataset = result
        return self

    def check_requirements(self, dataset:dict = None):
        if dataset is not None:
            self.filter_readonly(dataset)

        try:
            self.config.requirements.resolve([x for x in self.dataset.keys()])
        except FieldRequirementException:
            raise ValidationError(f'Given dataset does not satisfying the requirements: {self.config.requirements.text_rule()}')
        return self

    def get_annotation(self, field:ModelField):
        for model_field in fields(self.config.model):
            if model_field.name == field.value:
                return model_field.type or Any
        else:
            return Any

    def any_iterable(self, annotation:type):
        if str(annotation).startswith('typing.Iterable') or \
            str(annotation).startswith('typing.List') or \
            str(annotation).startswith('typing.Tuple') or \
            annotation is tuple or \
            annotation is list:
            return True
        else:
            return False

    def any_union(self, annotation:type):
        return str(annotation).startswith('typing.Union')

    def find_validator(self, field: ModelField):
        return self.config.validators.get(field)

    @staticmethod
    def getname(obj):
        try:
            return obj._name
        except AttributeError:
            try:
                return obj.__name__
            except AttributeError:
                return str(obj)

            
    def resolve_annotations(self, field:ModelField, annotation:type, value:Any, validator:Validator):
        tp = TypingModuleValidator()
        errors = list()
        native_error = None
        notnone_error = None
        if self.any_union(annotation):
            args = annotation.__args__
            for arg in args:
                try:
                    if arg is type(None) or arg is None:
                        if value is None:
                            return None
                        else:
                            raise NotNoneError('Value is not None')
                    else:
                        return self.resolve_annotations(field, arg, value, validator)
                except NotNoneError as e:
                    notnone_error = e
                    continue
                except NativeValidationError as e:
                    native_error = e
                    continue
                except ValidationError as e:
                    errors.append((arg,e))
                    continue
            else:
                if len(errors) > 0:
                    raise ValidationError(f'{", ".join(f"{self.getname(arg)}({err})" for arg,err in errors)}')
                else:
                    raise native_error or notnone_error

        elif self.any_iterable(annotation):
            if (not isinstance(value, Iterable)) or (isinstance(value, dict)) or (isinstance(value, str)):
                raise NativeValidationError(f'Invalid typecast. Array required.')

            if tp._is_typing_alias(str(annotation)):
                result = list()
                args = annotation.__args__
                for i, subvalue in enumerate(value):
                    for arg in args:
                        try:
                            result.append(self.resolve_annotations(field, arg, subvalue, validator))
                            break
                        except NotNoneError as e:
                            notnone_error = e
                            continue
                        except NativeValidationError as e:
                            native_error = e
                            continue
                        except ValidationError as e:
                            errors.append((arg,e))
                            continue
                    else:
                        if len(errors) > 0:
                            raise ValidationError(f'[{i}]: {", ".join(f"({err})" for _, err in errors)}')
                        else:
                            raise native_error or notnone_error
                
                if str(annotation).startswith('typing.Tuple'):
                    return tuple(result)
                else:
                    return result
            else: # we does not know about items types
                return annotation(value)
        else:
            if validator:
                result = validator.validate(value)
                
                if validator.check_result_type:
                    if isinstance(result, ValidationContext):
                        if annotation != validator.validator.model:
                            raise AbstractError(f'Field annotation and validator model are different')
                    elif not tp._is_instance(result, annotation):
                        raise RuntimeError(f'Invalid typecast after user-defined validation: validator returned {type(result)}, but {str(annotation)} required.')
                
                return result
            else:
                try:
                    if value is None:
                        raise NativeValidationError('value required')
                    elif (annotation is bool) and isinstance(value, str):
                        if value.strip().lower() == 'true':
                            return True
                        elif value.strip().lower() == 'false':
                            return False
                        else:
                            raise ValueError(f'invalid literal for Boolean: "{value}"')
                    else:
                        return annotation(value)
                except (ValueError, TypeError) as e:
                    raise ValidationError(f'Invalid typecast: {str(e)}')

                    
    def validate(self, dataset:dict = None):
        if dataset is not None:
            self.check_requirements(dataset)

        result = dict()
        for field, value in self.dataset.items():
            try:
                annotation = self.fields_annotations[field]
                validator = self.find_validator(field)
                result[field] = self.resolve_annotations(field, annotation, value, validator)
            except (ValidationError, NativeValidationError) as e:
                raise ValidationError(f'{self.parent_validator_name}({field}) -> {str(e)}')
            except UnexpectedError as e:
                raise UnexpectedError(f'{self.parent_validator_name}({field}) -> {str(e)}')
            except Exception as e:
                raise UnexpectedError(f'{self.parent_validator_name}({field}): Unexpected error with value {value}: {str(e)}') from e
            
        self.dataset = result
        return self


    def validated_dataset(self, dataset:dict = None):
        if dataset is not None:
            self.validate(dataset)

        return self.export_dataset()

    def map(self, dataset:dict = None):
        if dataset is not None:
            self.validate(dataset)
        return self.config.model(**self._deep_execute_on_dataset(method=lambda x: x.map(), replace_field=True))
 

class Outpost(ABCOutpost):
    ...
    @classmethod
    def context(class_) -> ValidationContext:
        return ValidationContext(class_.__config__.to_RW(), class_.__name__)

    @classmethod
    def validate(class_, dataset: dict) -> ValidationContext:
        return class_.context().validate(dataset=dataset)

    @classmethod
    def validation_results(class_, dataset: dict):
        return class_.validate(dataset).validated_dataset()

    @classmethod
    def create_model(class_, dataset:dict) -> Any:
        return class_.validate(dataset).map()

    def __call__(self, *_: Any, **__: Any) -> Any:
        raise AbstractError(f'{self.__class__.__name__} is for static usage only')
