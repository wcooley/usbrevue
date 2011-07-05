#!/usr/bin/env python

"""Miscellaneous utilities"""

def reverse_update_dict(dictionary):
    """Update dictionary by adding val => key"""
    dictionary.update([ (val,key) for val,key in dictionary.items() ])
