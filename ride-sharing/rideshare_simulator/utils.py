import math
from typing import Tuple

import numpy as np


def lag(x, n=1, fill=0.):
    """
        Replacing the last n elements of x by the constant fill
    """
    return np.concatenate((np.ones(n) * fill, x[:-n]))


def clip(x, minx, maxx):
    return max(min(x, maxx), minx)


def isalatlng(x):
    return len(x) == 2 and isinstance(x[0], float) and isinstance(x[1], float)


def point_to_box(pt: Tuple[float, float]) -> Tuple[float, float, float, float]:
    return pt + pt


def id_to_treatment(id, p: float, salt: str=""):
    thresh = int(p * 100)
    return hash(str(id) + salt) % 100 < thresh


def interpolate_latlng(a, b, p, plng=None):
    """
        Generate a point in a box.

        Return a point (x, y) where 
            x = a[0]*(1-p) + b[0]*p
            y = a[1]*(1-plng) + b[1]*plng
        in the case plng=None, plng := p
    """
    plat = p
    plng = p if plng is None else plng
    lata, lnga = a
    latb, lngb = b
    return ((lata * (1 - plat) + latb * plat),
            (lnga * (1 - plng) + lngb * plng))


def truncated_normal_2d(mean, cov_matrix, lower_bound, upper_bound, size=2):
    num_samples = 0
    samples = np.empty((0, 2))

    while num_samples < size:
        # Generate samples for each dimension separately
        x = np.random.multivariate_normal(mean, cov_matrix, size=size)
        
        # Filter out samples outside the desired range
        valid_samples = x[(x[:, 0] >= lower_bound) & (x[:, 0] <= upper_bound) &
                           (x[:, 1] >= lower_bound) & (x[:, 1] <= upper_bound)]

        # Append valid samples to the result array
        samples = np.vstack((samples, valid_samples))
        num_samples = len(samples)

    return samples[:size]

def take_until(pred, seq, strict=False):
    """
    Yields elements from seq, up to and including the first element
    satisfying pred. If strict, raises an exception if no element
    satisfies pred.
    """
    for item in seq:
        if pred(item):
            return item
        else:
            yield item
    if strict:
        raise Exception("Predicate never satisfied.")
