"""
Multi-part collection of polygons.
"""

from ctypes import byref, c_double, c_int, c_void_p, cast, POINTER, pointer

from shapely.geos import lgeos
from shapely.geometry.base import BaseGeometry, GeometrySequence
from shapely.geometry.polygon import Polygon, geos_polygon_from_py


def geos_multipolygon_from_py(ob):
    """ob must be either a sequence or array of sequences or arrays."""
    L = len(ob)
    N = len(ob[0][0][0])
    assert L >= 1
    assert N == 2 or N == 3

    subs = (c_void_p * L)()
    for l in xrange(L):
        geom, ndims = geos_polygon_from_py(ob[l][0], ob[l][1])
        subs[l] = cast(geom, c_void_p)
            
    return (lgeos.GEOSGeom_createCollection(6, subs, L), N)


class MultiPolygon(BaseGeometry):

    """a multiple polygon geometry.
    """

    def __init__(self, polygons=None):
        """Initialize.

        Parameters
        ----------
        
        polygons : sequence
            A sequence of (shell, holes) tuples where shell is the sequence
            representation of a linear ring (see linearring.py) and holes is
            a sequence of such linear rings.

        Example
        -------
        >>> geom = MultiPolygon( [
        ...     (
        ...     ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)), 
        ...     [((0.1,0.1), (0.1,0.2), (0.2,0.2), (0.2,0.1))]
        ...     )
        ... ] )
        """
        BaseGeometry.__init__(self)

        if polygons is None:
            # allow creation of null collections, to support unpickling
            pass
        else:
            self._geom, self._ndim = geos_multipolygon_from_py(polygons)

    @property
    def __geo_interface__(self):
        allcoords = []
        for geom in self.geoms:
            coords = tuple(geom.exterior.coords)
            hole_coords = []
            for hole in geom.interiors:
                hole_coords.append(tuple(hole.coords))
            allcoords.append((coords, hole_coords))
        return {
            'type': 'MultiPolygon',
            'coordinates': allcoords
            }

    @property
    def ctypes(self):
        raise NotImplementedError, \
        "Multi-part geometries have no ctypes representations"

    @property
    def __array_interface__(self):
        """Provide the Numpy array protocol."""
        raise NotImplementedError, \
        "Multi-part geometries do not themselves provide the array interface"

    @property
    def coords(self):
        raise NotImplementedError, \
        "Multi-part geometries do not provide a coordinate sequence"

    @property
    def geoms(self):
        return GeometrySequence(self, Polygon)


class MultiPolygonAdapter(MultiPolygon):

    """Adapts sequences of sequences or numpy arrays to the multipolygon
    interface.
    """
    
    context = None

    def __init__(self, context):
        self.context = context

    # Override base class __del__
    def __del__(self):
        pass

    @property
    def _ndim(self):
        try:
            # From array protocol
            array = self.context[0][0].__array_interface__
            n = array['shape'][1]
            assert n == 2 or n == 3
            return n
        except AttributeError:
            # Fall back on list
            return len(self.context[0][0][0])

    @property
    def _geom(self):
        """Keeps the GEOS geometry in synch with the context."""
        return geos_multipolygon_from_py(self.context)[0]       


def asMultiPolygon(context):
    """Factory for MultiLineStringAdapter instances."""
    return MultiPolygonAdapter(context)


# Test runner
def _test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    _test()

