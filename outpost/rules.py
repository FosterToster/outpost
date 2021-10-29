from typing import Iterable, Union
from enum import Enum
from .exceptions import RequiredException
from abc import ABC, abstractmethod


# class Enum(Enum):
#     ...


class RequirementBase(ABC):
    @abstractmethod
    def resolve(self, passed_fields: Iterable[str]):
        ...

    @abstractmethod
    def text_rule(self):
        ...


class Require(RequirementBase):
    def __init__(self, field:Enum) -> None:
        if not isinstance(field, Enum):
            raise RequiredException(f'Rule "{field}" is not model field')

        self._field = field

    @property
    def field(self):
        return self._field

    def resolve(self, passed_fields: Iterable[str]):
        if not (self.field.value in passed_fields):
            raise RequiredException(f"Field {self.text_rule()} required")

    def text_rule(self):
        return self.field.value


class _RequireMany(RequirementBase):
    
    def __init__(self, *rules:Union[Enum, RequirementBase]) -> None:
        self._rules = list()
        for rule in rules:
            if isinstance(rule, Enum):
                self._rules.append(Require(rule))
            elif isinstance(rule, RequirementBase):
                self._rules.append(rule)
            else:
                raise RequiredException(f'Rule {rule} is not Requirement')
        

    @property
    def rules(self) -> Iterable[RequirementBase]:
        return self._rules


class OR(_RequireMany):
    def resolve(self, passed_fields: Iterable[str]):
        for rule in self.rules:
            try:
                rule.resolve(passed_fields)
            except RequiredException as e:
                continue
            else:
                return None
        else:
            raise RequiredException(f'Required fields: {self.text_rule()}')

    def text_rule(self):
        return '(' + ' OR '.join(rule.text_rule() for rule in self.rules) + ')'

class AND(_RequireMany):
    def resolve(self, passed_fields: Iterable[str]):
        for rule in self.rules:
            try:
                rule.resolve(passed_fields)
            except RequiredException as e:
                raise RequiredException(f'Required fields: {self.text_rule()}')
            else:
                continue
        else:
            raise RequiredException(f'Required fields: {self.text_rule()}')

    def text_rule(self):
        return '(' + ' AND '.join(rule.text_rule() for rule in self.rules) + ')'


class NOT(RequirementBase):
    def __init__(self, rule: Union[Enum, RequirementBase]) -> None:
        if isinstance(rule, Enum):
            self._rule = Require(rule)
        elif isinstance(rule, RequirementBase):
            self._rule = rule
        else:
            raise RequiredException(f'Rule {rule} is not Requirement')

    @property
    def rule(self):
        return self._rule

    def resolve(self, passed_fields: Iterable[str]):
        try:
            self.rule.resolve(passed_fields)
        except RequiredException:
            pass
        else:
            raise RequiredException(f"Fields required: {self.text_rule()}")

    def text_rule(self):
        return f'NOT {self.rule.text_rule()}'
            



                    
        
    
