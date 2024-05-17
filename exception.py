class Interruption(Exception):
    pass


class OutOfBoundsError(IndexError, Interruption):
    def __init__(self, message):
        super().__init__(message)