class SpatialDiscretizer(object):
    def discretize(self, latlng: tuple[float, float]) -> int:
        raise NotImplementedError()


class GridDiscretizer(object):
    def __init__(self, min, max):
        pass
