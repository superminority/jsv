JSV - JSON separated values
===========================

.. image:: https://travis-ci.org/akovner/jsv.svg?branch=master
    :target: https://travis-ci.org/akovner/jsv
.. image:: https://coveralls.io/repos/github/akovner/jsv/badge.svg?branch=master
    :target: https://coveralls.io/github/akovner/jsv?branch=master
.. image:: https://readthedocs.org/projects/jsv/badge/?version=latest
    :target: https://jsv.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

A compact way to represent a stream of similar json objects

documentation
-------------

See `<https://jsv.readthedocs.io/>`_

installation
------------

``pip install jsv``

motivation
----------

JSON is an excellent universal represention for dictionaries, arrays and basic primitives. When representing records that are identical or nearly identical in schema, however, it is extremely verbose, as the same dictionary keys must be repeated for every record. The json lines format (which is just a sequence of json objects, each on a separate line of a file) therefore acheives great generality, but sacrifices compactness.

Other formats, notably csv, are not standardized, and can become leaky abstractions. In addition, they are usually confined to representing flat data, whereas json objects are rich with nested arrays and dictionaries.

This project replaces the json lines and csv formats with a rich, flexible, and compact representation of similar json objects. It aims to stay true to the simplicity and generality of json, and can represent any json object regardless of nesting. In addition, it provides for multiple record types in a single file or stream.

examples
--------

simple objects
++++++++++++++

Let's start with a simple example. Suppose we have a list of three json objects with identical keys: ::

    {"key_1":1,"key_2":2,"key_3":"three"}
    {"key_1":"four","key_2":true,"key_3":6}
    {"key_1":7,"key_2":"eight","key_3":null}
    
We transform this into: ::

    #_ {"key_1","key_2","key_3"}
    {1,2,"three"}
    {"four",true,6}
    {7,"eight",null}
    
The first line is simply a list of keys, embedded into a simple dictionary. The ``#`` indicates that a template is being defined, and ``_`` is the reserved id for the default template. The next three lines are the values, but devoid of keys. This is where the jsv format gets its compactness, and the resemblence to both csv and json is clear. Nevertheless it is neither: all four lines are unparsable either as json or csv.

nested objects
++++++++++++++

Let's consider some basic nested objects: ::

    {"key_1":{"subkey_1":1,"subkey_2":2},"key_2":["a","b","c"]}
    {"key_1":{"subkey_1":3,"subkey_2":4},"key_2":["d","e","f"]}
    {"key_1":{"subkey_1":5,"subkey_2":{"subsubkey_1":"vvv"}},"key_2":["g","h",["i","j","k"]]}
    
This becomes: ::

    #_ {"key_1":{"subkey_1","subkey"2},"key_2"}
    {{1,2},["a","b","c"]}
    {{3,4},["d","e","f"]}
    {{5,{"subsubkey_1":"vvv"}},["g","h",["i","j","k"]]}
    
The template, again, is a representation of the key structure, this time with nesting. The records (the last three lines) also have the nesting structure, but *without* the keys that are represented in the template. Notice also that there are some non-primitive values in the data. This is fine, as long as the key structure is honored. Also, arrays are left as-is, since they are already compact.

arrays
++++++

Here are some objects with arrays that contain dictionaries: ::

    {"arrival_time":"8:00","guests":[{"name":"Alice","age":37},{"name":"Bob","age":73}]}
    {"arrival_time":"8:30","guests":[{"name":"Cookie Monster","age":49}]}]

Here is the jsv file: ::

    #_ [{"arrival_time","guests":[{"name","age"}]
    {"8:00",[{"Alice",37},{"Bob",73}]}
    {"8:30",[{"Cookie Monster",49}]}

For arrays, a key structure can be given for multiple array entries. They are applied in order, and the last one is applied to all subsequent values found in the record. There is no requirement that the array contain any entries, however if there is an entry, it must conform to the template.

multiple record types
+++++++++++++++++++++

When there is a need to represent multiple record types in the same file or stream, we must include more metadata in the object that defines the template. For the following example, we consider a stream with two record types:

#. A transaction on an account, such as a purchase.
#. A change of address on an account.

Here is the initial json lines file: ::

    {"account_number":111111111,"transaction_type":"sale","merchant_id":987654321,"amount":123.45}
    {"account_number":111111111,"new_address":{"street":"123 main st.","city":"San Francisco","state":"CA","zip":"94103"}
    {"account_number":222222222,"transaction_type":"sale","merchant_id":848757678,"amount":5974.29}
    
Here is the ``.jsv`` file: ::

    #trns {"account_number","transaction_type","merchant_id","amount"}
    @trns {111111111,"sale",987654321,123.45}
    #addr {"id":"A","name":"address change","template":{"account_number","new_address":{"street","city","state","zip"}}}
    @addr {111111111,{"123 main st.","San Francisco","CA","94103"}}
    @trns {222222222,:"sale",848757678,5974.29}
    
The ``@`` followed by the template name indicates a record. New record types can be defined (and redefined) at any point in the stream, provided they appear before any records of that type appear. We can also mix this with using a default template. For example, if we make ``trns`` the default, we end up with the following: ::

    #_ {"account_number","transaction_type","merchant_id","amount"}
    {111111111,"sale",987654321,123.45}
    #addr {"id":"A","name":"address change","template":{"account_number","new_address":{"street","city","state","zip"}}}
    @addr {111111111,{"123 main st.","San Francisco","CA","94103"}}
    {222222222,:"sale",848757678,5974.29}

split template and record files
+++++++++++++++++++++++++++++++

We can also store the templates in a separate file. By convention, we use the ``.jsvt`` extension for the template file, and the ``.jsvr`` extension for the record file. Using the example from the previous section, here is the template file: ::

    #trns {"account_number","transaction_type","merchant_id","amount"}
    #addr {"id":"A","name":"address change","template":{"account_number","new_address":{"street","city","state","zip"}}}

and here is the record file: ::

    @trns {111111111,"sale",987654321,123.45}
    @addr {111111111,{"123 main st.","San Francisco","CA","94103"}}
    @trns {222222222,:"sale",848757678,5974.29}

This feature is intended to facilitate analysis on a cluster device, where the record file can be split among nodes, and the template file can be put in the global cache.

definitions
-----------

Here are some terms specific to this project:

template
  A data structure which contains only they keys for a json-like object, along with the nesting structure of the dictionaries of that object.

record
  A data structure which contains only the values for a json-like object, fully nested in both dictionaries and arrays.
  
object
  An ordinary json object, or its equivalent representation in a given language.

future features
---------------

abbreviations
+++++++++++++

Specify that certain repeated values be replaced with a token in the file or stream.

nested templates
++++++++++++++++

Allow templates to be specified within a record.

integration with JSON schema
++++++++++++++++++++++++++++

The ability to define a template from a `JSON Schema <https://json-schema.org/>`_ definition.
