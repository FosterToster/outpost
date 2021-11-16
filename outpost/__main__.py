from outpost.exceptions import ValidationError
from .types import Outpost, OutpostProvider
from dataclasses import dataclass
from .rules import AND, OR, NOT, Require

@dataclass
class Phone:
    number: int


@dataclass
class User:
    id: int
    name: str
    hash: str
    phone: Phone


class UserValidator:
    
    config = OutpostProvider.from_model(User)

    config.model.

    config.require(config.model.id)
    config.require(config.model.hash)

    @config.validator(config.model.name, check_result_type=False)
    def name_validator(value):
        return str(value)

    config.readonly.append(config.model.id)
    config.readonly.append(config.model.hash)

    config.defaults[config.model.name] = 'Federico Felini'

    @config.combine(config.model.name, config.model.id)
    def name_id_combination(name, id):
        print('fuck')

print(UserValidator.config)