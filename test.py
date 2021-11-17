class CompareRule:
    def __init__(self, mode, members) -> None:
        self.mode = mode
        self.members = members

    def __str__(self):
        return '(' + f' {self.mode} '.join(str(x) for x in self.members) + ')'


class ComparerMeta(type):
    def __or__(self, other):
        print(self, other)
        return True


class SomeComparer(metaclass=ComparerMeta):
    ...
    def __or__(self, other):
        return CompareRule('OR', (self, other))

    def __and__(self, other):
        return CompareRule('AND', (self, other))

    def __neg__(self):
        return CompareRule('NOT', (self,))

    def __invert__(self):
        return CompareRule('NOT', (self,))

def some(a: bool):
    print(a)


some(SomeComparer())
