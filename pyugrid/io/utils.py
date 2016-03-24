#!/usr/bin/env python

"""
utilities to help with io

NOTE: this isn't used yet, but should be useful for loading non
UGRID-compliant files
"""

from __future__ import (absolute_import, division, print_function)

import numpy as np
import netCDF4
import pyugrid


def load_from_varnames(filename, names_mapping, attribute_check=None):
    """
    load a UGrid from a netcdf file where the roles are defined by the
    names of the variables

    :param filename: the names of the file to load (or opendap url)

    :param names_mapping: dict that maps the variable names to the UGRid components

    :param attribute_check=None: list of global attributes that are expected
    :type attribute_check: list of tuples to check. Example:
                           [('grid_type','triangular'),] will check if the
                           grid_type attribute is set to "triangular"

    The names_mapping dict has to contain at least:

    'nodes_lon', 'nodes_lat'

    Optionally (and mostly required), it can contain:

    'faces', 'face_face_connectivity', 'face_coordinates_lon', 'face_coordinates_lat'


    """
    attribute_check = {} if attribute_check is None else attribute_check

    # open the file
    nc = netCDF4.Dataset(filename)

    # check if it's the file type we are looking for

    for name, value in attribute_check:
        if nc.getncattr(name).lower() != value:
            raise ValueError('This does not appear to be a valid file:\n'
                             'It does not have the "{}"="{}"'
                             'global attribute set'.format(name, value))
    # create an empty UGrid:
    ug = pyugrid.UGrid()

    # load the nodes -- this is required
    # nodes are usually stored in two different arrays
    lon = nc.variables[names_mapping['nodes_lon']]
    lat = nc.variables[names_mapping['nodes_lat']]

    num_nodes = lon.shape[0]
    ug.nodes = np.zeros((num_nodes, 2), dtype=lon.dtype)
    ug.nodes[:, 0] = lon[:]
    ug.nodes[:, 1] = lat[:]

    # load the faces
    faces = nc.variables[names_mapping['faces']]
    # does it need to be transposed?
    # assume there are more than three triangles...
    if faces.shape[0] <= faces.shape[1]:
        # Fortran order -- needs to be transposed
        faces = faces[:].T
    else:
        faces = faces[:]
    # is it one-indexed?
    if faces.min() == 1:
        one_indexed = True
        faces -= 1
        ug.faces = faces
    else:
        one_indexed = False

    # load the connectivity array: optional
    if 'face_face_connectivity' in names_mapping:
        face_face_connectivity = nc.variables[names_mapping['face_face_connectivity']]
        # does it need to be transposed?
        # assume there are more than three triangles...
        if face_face_connectivity.shape[0] <= face_face_connectivity.shape[1]:
            # Fortran order -- needs to be transposed
            face_face_connectivity = face_face_connectivity[:].T
        else:
            face_face_connectivity = face_face_connectivity[:]
        if one_indexed:
            face_face_connectivity -= 1
        ug.face_face_connectivity = face_face_connectivity[:]

    # load the center points of the faces: optional
    if ('face_coordinates_lon' in names_mapping and
            'face_coordinates_lat' in names_mapping):
        ug.face_coordinates = np.zeros((len(ug.faces), 2), dtype=lon.dtype)
        ug.face_coordinates[:, 0] = nc.variables[names_mapping['face_coordinates_lon']][:]
        ug.face_coordinates[:, 1] = nc.variables[names_mapping['face_coordinates_lat']][:]

    if 'boundaries' in names_mapping:  # optional
        # fixme --  this one is weird and non-conforming....
        boundaries = nc.variables[names_mapping['boundaries']][:, :2]
        if one_indexed:
            boundaries -= 1
        ug.boundaries = boundaries  # ignoring the second two fields -- what are they???

    return ug


if __name__ == "__main__":

    names_mapping = {'attribute_check': ('grid_type', 'triangular'),
                     'nodes_lon': 'lon',
                     'nodes_lat': 'lat',
                     'faces': 'nv',
                     'face_face_connectivity': 'nbe',
                     'face_coordinates_lon': 'lonc',
                     'face_coordinates_lat': 'latc',
                     'boundaries': 'bnd',
                     }

    ug = load_from_varnames("small_trigrid_example.nc", names_mapping)

    print(ug)