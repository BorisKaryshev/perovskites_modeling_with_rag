class ClassWithCreator:
    __creator = None

    @classmethod
    def _set_creator(cls, creator):
        cls.__creator = creator

    @classmethod
    def _create(cls, *args, **kwargs):
        if cls.__creator is None:
            raise ValueError("Tryied to create class with empty creator")
        return cls.__creator(*args, **kwargs)
