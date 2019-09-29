#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway Constants and Definitions."""

import os

from pkg_resources import Requirement, resource_filename


def data_resource_filename(filename):
    """Return the filename of a data resource."""
    return resource_filename(
        Requirement.parse("liftaway"), os.path.join("liftaway/data", filename)
    )
