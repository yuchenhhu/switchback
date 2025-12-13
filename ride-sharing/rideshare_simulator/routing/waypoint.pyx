import cython


cdef class Waypoint(object):
    """
        a point with (latitude, longitude)
    """
    def __init__(self, latlng):
        self.latlng = latlng


cdef class TripWaypoint(Waypoint):
    def __init__(self, latlng, rider_id, deadline=float("Inf")):
        super(TripWaypoint, self).__init__(latlng)
        self.rider_id = rider_id
        self.deadline = deadline


cdef class PickupWaypoint(TripWaypoint):
    pass


cdef class DropoffWaypoint(TripWaypoint):
    pass
