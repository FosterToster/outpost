from outpost.exceptions import ExcludeValue, ValidationError
from outpost.rules import Require
from .types import Outpost, OutpostProvider
from dataclasses import dataclass


@dataclass
class Phone:
    number: int


@dataclass
class User:
    id: int
    name: str
    hash: str
    ro: str
    phone: Phone

class UserValidator(Outpost):
    config = OutpostProvider.from_model(User)

    
    @config.combine(config.fields.name, config.fields.hash)
    def combine_name_hash_(name, hash):
        raise Exception(f'WOW: {name}, {hash}')

    @config.validator(config.fields.id, check_result_type=False)
    def check_id(value):
        return int(value)

    config.readonly.append(config.fields.ro)

    config.defaults[config.fields.name] = "Default User"

    config.require(config.fields.name)


class CreateUserValidator(UserValidator):
    config = UserValidator.config

    config.readonly.append(config.fields.id)

    config.require(
        (config.fields.hash |
        config.fields.id) &
        config.fields.phone
        )
    # config.require(config.fields.name)

    
    ...


print(CreateUserValidator.model)