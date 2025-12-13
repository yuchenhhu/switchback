cdef class Waypoint:
    cdef public (float, float) latlng


cdef class TripWaypoint(Waypoint):
    cdef public str rider_id
    cdef public float deadline
