json-separated-values
=====================

A compact way to represent a stream of similar json objects

motivation
----------

JSON is an excellent universal represention for dictionaries, arrays and basic primitives. When representing records that are identical or nearly identical in schema, however, it is extremely verbose, as the same dictionary keys must be repeated for every record. The json lines format (which is just a sequence of json objects, each on a separate line of a file) therefore acheives great generality, but sacrifices compactness.

Other formats, notably csv, are non-standardized, and can become leaky abstractions. In addition, they are usually confined to representing flat data, whereas json object are rich with nested arrays and objects.

This project replaces the json lines format with a rich, flexible, and compact representation of similar json objects. It aims to stay true to the simplicity and generality of json, and can represent any json object regardless of nesting. In addition, it provides for multiple record types in a single file or stream.

examples
--------

simple objects
++++++++++++++

Let's start with the simplest example. Suppose we have a list of three json objects with identical keys: ::

    {"key_1":1,"key_2":2,"key_3":"three"}
    {"key_1":"four","key_2":true,"key_3":6}
    {"key_1":7,"key_2":"eight","key_3":null}
    
We transform this into: ::

    (){"key_1","key_2","key_3"}
    {1,2,"three"}
    {"four",true,6}
    {7,"eight",null}
    
The first line is simply a list of keys. We know it is a list of keys (rather than an array) it is surrounded by curly braces instead of brackets. Further, the parentheses at the beginning of the line indicate that it is not data, but metadata. This will be explained more fully as we go along.

The next three lines are the values, but devoid of keys. This is where the jsv format gets its compactness, and the resemblence to both csv and json is clear. Nevertheless it is neither: all four lines are unparsable either as json or csv.

nested objects
++++++++++++++

Let's consider some basic nested objects: ::

    {"key_1":{"subkey_1":1,"subkey_2":2},"key_2":["a","b","c"]}
    {"key_1":{"subkey_1":3,"subkey_2":4},"key_2":["d","e","f"]}
    {"key_1":{"subkey_1":5,"subkey_2":{"subsubkey_1":"vvv"}},"key_2":["g","h",["i","j","k"]]}
    
This becomes: ::

    (){"key_1":{"subkey_1","subkey"2},"key_2"}
    {{1,2},["a","b","c"]}
    {{3,4},["d","e","f"]}
    {{5,{"subsubkey_1":"vvv"}},["g","h",["i","j","k"]]}
    
The first line, again, is a representation of the key structure, this time with nesting. Notice that the value objects (the last three lines) also have the nesting structure, but *withouth* the keys that are represented in the key structure.

Notice also that there are some non-primitive values in the data. This is fine, as long as the key structure is honored. Also, arrays are left as-is, since they are already compact.

multiple record types
+++++++++++++++++++++

When there is a need to represent multiple record types in the same file or stream, we must use the metadata section to define each type. The metadata section is just a json object, but with the outermost container consisting of parentheses, not curly braces. For the following example, we consider a stream with two record types:

#. A transaction on an account, such as a purchase.
#. A change of address on an account.

Here is the initial json lines file: ::

    {"account_number":111111111,"transaction_type":"sale","merchant_id":987654321,"amount":123.45}
    {"account_number":111111111,"new_address":{"street":"123 main st.","city":"San Francisco","state":"CA","zip":"94103"}
    {"account_number":222222222,"transaction_type":"sale","merchant_id":848757678,"amount":5974.29}
    
Here is the jsv file: ::

    ("name":"transaction"){"account_number","transaction_type","merchant_id","amount"}
    {111111111,"sale",987654321,123.45}
    ("id":"A","name":"address change"){"account_number","new_address":{"street","city","state","zip"}}
    A{111111111,{"123 main st.","San Francisco","CA","94103"}}
    {222222222,"sale",848757678,5974.29}
    
Note that the ``id`` field in the metadata becomes the first character of any line of that record type. Without an ``id`` field specified, the *transaction* record type is the default.
