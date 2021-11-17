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

    config.require(
        (config.fields.hash |
        config.fields.id) &
        config.fields.phone
        )
    # config.require(config.fields.name)

    
    ...

dataset = {
    'id': 1,
    'name': 'Sadric',
    'phone': 7
}

try:
    with CreateUserValidator.context() as context:
        context.filter_readonly(dataset, raise_readonly=True)
        context.validate()
        print(context.export_dataset())
        print(context.map())
except ValidationError as e:
    print(e)