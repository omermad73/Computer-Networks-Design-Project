class GNO: #Generic Networking Object
    Count_Objects = 0

    def __init__(self, type):
        self.id = GNO.Count_Objects
        self.type = type
        GNO.Count_Objects +=1

        @property
        def id(self):
            return self._id

        @property
        def type(self):
            return self._type