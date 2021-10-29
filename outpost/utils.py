from .types import OutpostMeta, Outpost

def validatable(class_):
    class_.validator = create_validator(class_)
    return class_

def create_validator(class_) -> Outpost:
    return OutpostMeta(f'{class_.__name__}BasicValidator', (Outpost, ), {}, model=class_)