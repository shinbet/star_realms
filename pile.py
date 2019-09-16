class Pile(list):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
    def copy(self):
        return Pile(self.name, self)
    def __str__(self):
        return f'{self.name}: {super().__str__()}'
    def __repr__(self):
        return f'Pile<{self.name}, {super().__repr__()}>'