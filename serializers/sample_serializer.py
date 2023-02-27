class SampleSerializer(object):
    def __init__(self, *initial_data, **kwargs):
        # for IDE completion
        self.email = None
        self.password = None
        self.is_verified = None

        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])
