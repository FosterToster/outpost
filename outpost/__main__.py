from outpost.exceptions import ValidationError
from .types import Outpost, OutpostProvider
from typing import Iterable
from dataclasses import dataclass


@dataclass
class Phone:
    number: int


@dataclass
class User:
    id: int
    name: str
    hash: str
    phone: Iterable[Phone]

class PhoneValidator(Outpost):
    config = OutpostProvider.from_model(Phone)
    config.requirements = config.fields.number
    # config.require(config.fields.number)

    @config.validator(config.fields.number)
    def number(value):
        st = str(value).strip()
        if st.startswith('+'):
            st = st.replace('+', '')

        if not st.isnumeric():
            raise ValidationError('phone number can`t contain letters')

        if st.startswith('7'):
            st = st.replace('7', '8')
        
        if len(st) < 11:
            raise ValidationError('phone number is too small. 11 symbols required.')

        return int(st)

class CreatePhoneValidator(PhoneValidator):
    config = PhoneValidator.config
    
    @config.validator(config.fields.number)
    def number(value):
        raise ValidationError('Потом создашь')

class UserValidator(Outpost):
    config = OutpostProvider.from_model(User)
    config.validator(config.fields.phone, PhoneValidator)
    config.missing_value = None

class UpdateUserValidator(UserValidator):
    config = UserValidator.config
    config.raise_readonly = True
    config.require(config.fields.id & (
        config.fields.hash |
        config.fields.name |
        config.fields.phone
    ))

class SomeUserValidator(UpdateUserValidator):
    config = UpdateUserValidator.config
    
class CreateUserValidator(UserValidator):
    config = UserValidator.config
    config.validator(config.fields.phone, CreatePhoneValidator)

    config.require(
        config.fields.name &
        (config.fields.hash |
        config.fields.id) &
        config.fields.phone
        )

    config.defaults[config.fields.name] = "Default user"

    
    ...

print(UserValidator.raise_readonly)
print(UpdateUserValidator.raise_readonly)
print(SomeUserValidator.raise_readonly)

create_dataset = {
    'id': 1,
    'name': 'Sadric',
    'phone': [{
        
    },{
        'number': 89639499629
    }]
}

update_dataset = {
    'id': 1,
    'name': 'Vigor',
    'phone': [
        {'number': '+79639499629'}
    ]

}

try:
    a = CreateUserValidator.create_model(create_dataset)
except ValidationError as e:
    a = e

print('create:', a)

try:
    a = UpdateUserValidator.create_model(update_dataset)
except ValidationError as e:
    a = e

print('update:', a)