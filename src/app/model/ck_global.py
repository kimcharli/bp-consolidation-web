


class GlobalStore:
    apstra_server = None  #  ApstaServer
    main_bp = None  # ApstaBlueprint
    tor_bp = None  # ApstaBlueprint
    
    data = {
    }

    @classmethod
    def get_blueprints(cls):
        return [cls.main_bp, cls.tor_bp]

    @classmethod
    def set_data(cls, key, value):
        cls.data[key] = value

    @classmethod
    def get_data(cls, key):
        return cls.data.get(key)


