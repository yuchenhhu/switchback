from .waypoint cimport Waypoint
# cimport numpy as np


cdef class RouteLeg:
    cdef public Waypoint src, dest
    cdef public float kms, secs


cdef class Route:
    cdef public float start_ts
    cdef public list legs
    cdef public list waypoints
    cdef public float total_kms
    cdef public float total_secs
    cdef public list leg_end_ts

    cpdef int current_leg(self, float ts)
    cpdef float current_leg_progress(self, float ts)
    cpdef (float, float) latlng(self, float ts)
    cpdef float progress(self, float ts)
    cpdef list remaining_legs(self, float ts)
    cpdef float remaining_kms(self, float ts)
    cpdef float remaining_secs(self, float ts)
    cpdef bint is_complete(self, float ts)
    cpdef list remaining_trip_waypoints(self, float ts)
    cpdef list remaining_waypoints(self, float ts)
    cpdef set remaining_riders(self, float ts)
    cpdef float slack_time(self, float ts)
