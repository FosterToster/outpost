from uuid import uuid4
from .exceptions import ValidationError
from .types import Outpost, OutpostProvider
from .alchemy import AlchemyFieldGenerator
from typing import Iterable, Optional
from dataclasses import dataclass
from datetime import datetime
from models import Phone, User



class PhoneValidator(Outpost):
    op = OutpostProvider.from_model(Phone)
    op.validator(op.fields.user, Outpost['UserValidator']) # promised validator
    

class UserValidator(Outpost):
    op = OutpostProvider.from_model(User)
    op.validator(op.fields.phones, PhoneValidator)
    op.require(op.fields.id)
    

user_dataset = {
    'id': "10",
    'name': 'Иванидзе',
    'hash': 51235345,
    'gender': 'MALE',
    # 'phones': [dataset]
}

dataset = {
    'id': "1",
    'deleted': 'False',
    'number': '9634343434',
    'user': user_dataset
}

def pretty_print_model(instance, tabs=1):
    print(f'{instance.__class__.__name__}(')
    for field in AlchemyFieldGenerator(instance.__class__).all_fields():
        f = getattr(instance, field)

        if isinstance(f, User) or isinstance(f, Phone):
            print('\t'*tabs + f'{field}=', end="")
            pretty_print_model(f, tabs + 1)
        else:
            print('\t'*tabs + f'{field}={f} ({type(f)})')

    print(( '\t'*(tabs - 1) ) + ')')


try:
    b = PhoneValidator.create_model(dataset)
    # b = UserValidator.create_model(user_dataset)
except ValidationError as e:
    print(f'({e.__class__.__name__}) {e}')
else:
    # pretty_print_model(a)
    pretty_print_model(b)



# @dataclass
# class Phone:
#     number: int


# @dataclass
# class User:
#     id: int
#     name: Optional[str]
#     hash: Optional[str]
#     phone: Phone

# class PhoneValidator(Outpost):
#     config = OutpostProvider.from_model(Phone)
#     config.requirements = config.fields.number
#     # config.require(config.fields.number)

#     @config.validator(config.fields.number)
#     def number(value):
#         st = str(value).strip()
#         if st.startswith('+'):
#             st = st.replace('+', '')

#         if not st.isnumeric():
#             raise ValidationError('phone number can`t contain letters')

#         if st.startswith('7'):
#             st = st.replace('7', '8')
        
#         if len(st) < 11:
#             raise ValidationError('phone number is too small. 11 symbols required.')

#         return int(st)

# class CreatePhoneValidator(PhoneValidator):
#     config = PhoneValidator.config
    
    

# class UserValidator(Outpost):
#     config = OutpostProvider.from_model(User)
#     config.validator(config.fields.phone, PhoneValidator)
#     config.missing_value = None

# class UpdateUserValidator(UserValidator):
#     config = UserValidator.config
#     config.raise_readonly = True
#     config.require(config.fields.id & (
#         config.fields.hash |
#         config.fields.name |
#         config.fields.phone
#     ))

# class SomeUserValidator(UpdateUserValidator):
#     config = UpdateUserValidator.config
    
# class CreateUserValidator(UserValidator):
#     config = UserValidator.config
#     config.validator(config.fields.phone, CreatePhoneValidator)

#     # config.readonly = [config.fields.id]

#     config.require(
#         config.fields.name &
#         (config.fields.hash |
#         config.fields.id) &
#         config.fields.phone
#         )

#     config.defaults[config.fields.name] = "Default user"

    
#     ...

# create_dataset = {
#     'id': '12',
#     'name': True,
#     'phone': {
#         "number": "+79639499629"
#     }
# }

# update_dataset = {
#     'id': 'vigor',
#     'name': 'Vigor',
#     'phone': [
#         {'number': '+79639499629'}
#     ]

# }

# try:
#     start = datetime.now()
#     a = CreateUserValidator.defaults({CreateUserValidator.fields.hash: str(uuid4()) }).validate(create_dataset).map()
# except ValidationError as e:
#     a = e

# print(datetime.now() - start)
# print('create:', a)

# # try:
# #     print(CreateUserValidator.validation_results(create_dataset))
# #     a = CreateUserValidator.create_model(create_dataset)
# # except ValidationError as e:
# #     a = e

# # print('create:', a)

# # try:
# #     a = UpdateUserValidator.create_model(update_dataset)
# # except ValidationError as e:
# #     a = e

# # print('update:', a)