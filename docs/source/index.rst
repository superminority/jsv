.. jsv documentation master file, created by
   sphinx-quickstart on Tue Dec 11 15:41:42 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

JSON Separated Values (jsv)
===========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   index

Installation
============

``pip install jsv``

Motivation
==========

JSON is an excellent universal represention for dictionaries, arrays and basic primitives. When representing records that are identical or nearly identical in schema, however, it is extremely verbose, as the same dictionary keys must be repeated for every record. The json lines format (which is just a sequence of json objects, each on a separate line of a file) therefore acheives great generality, but sacrifices compactness.

Other formats, notably csv, are not standardized, and can become leaky abstractions. In addition, they are usually confined to representing flat data, whereas json objects are rich with nested arrays and dictionaries.

This project replaces the json lines and csv formats with a rich, flexible, and compact representation of similar json objects. It aims to stay true to the simplicity and generality of json, and can represent any json object regardless of nesting. In addition, it provides for multiple record types in a single file or stream.

Basic Usage
===========

.. automodule:: jsv

Developer Reference
===================

.. toctree::
   :maxdepth: 2

   api
