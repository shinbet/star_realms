class Pile(list):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
    def __copy__(self):
        return Pile(self.name, self)
    def copy(self):
        return Pile(self.name, self)
    def __str__(self):
        return f'{self.name}: {super().__str__()}'
    def __repr__(self):
        return f'Pile<{self.name}, {super().__repr__()}>'

    def __hash__(self):
        return hash(tuple(sorted(self)))

    # TODO: add draw and support ontop