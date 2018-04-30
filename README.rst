json-separated-values
=====================

A compact way to represent a stream of similar json objects

motivation
----------

JSON is an excellent universal represention for dictionaries, arrays and basic primitives. When representing records that are identical or nearly identical in schema, however, it is extremely verbose, as the same dictionary keys must be repeated for every record. The json lines format (which is just a sequence of json objects, each on a separate line of a file) therefore acheives great generality, but sacrifices compactness.

Other formats, notably csv, are non-standardized, and can become leaky abstractions. In addition, they are usually confined to representing flat data, whereas json objects are rich with nested arrays and dictionaries.

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

    ("template":{"key_1","key_2","key_3"})
    {1,2,:"three"}
    {:"four",true,6}
    {7,:"eight",null}
    
The first line is simply a list of keys, embedded into a simple dictionary. We use parentheses instead of curly braces to distinguish it from a record. The next three lines are the values, but devoid of keys. This is where the jsv format gets its compactness, and the resemblence to both csv and json is clear. Nevertheless it is neither: all four lines are unparsable either as json or csv.

We also add a colon before string values to distinguish strings as *values* from strings as *keys*. This is important, because full json objects are always acceptable as values. For example, in the last record from the previous example, we need a way to distinguish

    {7,:"eight",null} => {"key_1":7,"key_2":"eight","key_3":null}
    
from

    {7,"eight":8,:"some other string",null} => {"key_1":7,"eight":8,"key_2":"eight","key_3":null}

Both of these are valid records under the template in the previous example. In keeping with the simplicity-first approach of json parsing, we must know from the first character whether something is a key or a value. The colon allows this.

nested objects
++++++++++++++

Let's consider some basic nested objects: ::

    {"key_1":{"subkey_1":1,"subkey_2":2},"key_2":["a","b","c"]}
    {"key_1":{"subkey_1":3,"subkey_2":4},"key_2":["d","e","f"]}
    {"key_1":{"subkey_1":5,"subkey_2":{"subsubkey_1":"vvv"}},"key_2":["g","h",["i","j","k"]]}
    
This becomes: ::

    ("template":{"key_1":{"subkey_1","subkey"2},"key_2"})
    {{1,2},["a","b","c"]}
    {{3,4},["d","e","f"]}
    {{5,{"subsubkey_1":"vvv"}},["g","h",["i","j","k"]]}
    
The template, again, is a representation of the key structure, this time with nesting. Notice that the value objects (the last three lines) also have the nesting structure, but *without* the keys that are represented in the template. Notice also that there are some non-primitive values in the data. This is fine, as long as the key structure is honored. Also, arrays are left as-is, since they are already compact.

nested arrays
+++++++++++++

Here are some objects with nested arrays: ::

    [{"arrival_time":"8:00","guests":[{"name":"Alice","age":37},{"name":"Bob","age":73}]},{"arrival_time":"8:30","guests":[{"name":"Cookie Monster","age":49}]}]

Here is the jsv file: ::

    ("template": [{"arrival_time","guests":[{"name","age"}])
    [{:"8:00",[{:"Alice",37},{:"Bob",73}]},{:"8:30",[{:"Cookie Monster",49}]}]

Note in this case that the file is actually shorter than the original for only 1 record.

multiple record types
+++++++++++++++++++++

When there is a need to represent multiple record types in the same file or stream, we must include more metadata in the object that defines the template. For the following example, we consider a stream with two record types:

#. A transaction on an account, such as a purchase.
#. A change of address on an account.

Here is the initial json lines file: ::

    {"account_number":111111111,"transaction_type":"sale","merchant_id":987654321,"amount":123.45}
    {"account_number":111111111,"new_address":{"street":"123 main st.","city":"San Francisco","state":"CA","zip":"94103"}
    {"account_number":222222222,"transaction_type":"sale","merchant_id":848757678,"amount":5974.29}
    
Here is the jsv file: ::

    ("name":"transaction","template":{"account_number","transaction_type","merchant_id","amount"})
    {111111111,:"sale",987654321,123.45}
    ("id":"A","name":"address change","template":{"account_number","new_address":{"street","city","state","zip"}})
    A{111111111,{:"123 main st.",:"San Francisco",:"CA",:"94103"}}
    {222222222,:"sale",848757678,5974.29}
    
Note that the ``id`` field in the metadata becomes the first character of any line of that record type. Without an ``id`` field specified, the *transaction* record type is the default. In addition, new record types can be defined at any time, provided they appear before any records of that type appear.

definitions
-----------

Here are some terms specific to this project:

template (t)
  A data structure which contains only they keys for a json-like object, along with the nesting structure of the dictionaries of that object.

record (r)
  A data structure which contains only the values for a json-like object, fully nested in both dictionaries and arrays.
  
object (o)
  An ordinary json object, or its equivalent representation in a given language.
  
In effect, we are converting dictionaries to lists in the values object, but we are careful to distinguish between a list that will be converted back to a dictionary. The same goes for the keys object, except that the primitives are all strings. Any library that implements the jsv format must therefore define list-like data structures to handle these cases.

operations
----------

There are a number of operations on these objects, both unary and binary. We discuss them here.

extract_template (o -> t)
  Creates a template from a json object.
  
compress (t, o -> r)
  Creates a record from a json object and a template.
  
decompress (t, r -> o)
  Creates a json object from a values object and a keys object.
  
is_compressable (t, o -> bool)
  Can a given json object be compressed using a given key structure?
  
is_decompressible (t, r -> bool)
  Can a given values object be decompressed using a given key structure?
  
is_finer (t1, t2 -> bool)
  Does t1 contain all the keys & nesting structure of t2? Another way to put this is that t2 should decompress every values object that t1 decompresses.

is_coarser (t1, t2 -> bool)
  Just ``is_finer`` with the argument order reversed.

future features
---------------

boolean collapse
++++++++++++++++

store boolean values as ``t`` and ``f`` instead of ``true`` and ``false``. Also store null as ``n`` instead of ``null``.

string enumerations
+++++++++++++++++++

For a given [json path](http://goessner.net/articles/JsonPath/), support automatically replacing strings with placeholders.
