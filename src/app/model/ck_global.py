


class GlobalStore:
    apstra_server = None  #  ApstaServer
    data = {
    }

    @classmethod
    def set_data(cls, key, value):
        cls.data[key] = value

    @classmethod
    def get_data(cls, key):
        return cls.data.get(key)


