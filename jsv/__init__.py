"""
JSV is a simple library for representing many JSON objects with a similar structure. It is intended to replace json
lines, csv, and other similar formats.

Basic write usage

    >>> import jsv
    >>> data = [{'key_1': 1}, {'key_1': ['any','json','object'], 'other_key': None}]
    >>> with jsv.JSVWriter('out.jsv', 'at', {'_': '{"key_1"}'}) as w:
    ...     for rec in data:
    ...         w.write(rec)

The resulting file will be:

.. code-block:: text

    #_ {"key_1"}
    {1}
    {["any","json","object"],"other_key":null}

Basic read usage:

    >>> with jsv.JSVReader('out.jsv') as r:
    ...     for tid, obj in r.items():
    ...         print('{0}: {1}'.format(tid, obj))

The output will be:

.. code-block:: text

    _: {'key_1': 1}
    _: {'key_1': ['any', 'json', 'object'], 'other_key': None}

Usage with multiple templates:

    >>> data = [('t1', {'key_1': 1}),('t2', [{'key_2': 2}, {'key_2': None}])]
    >>> with jsv.JSVWriter('out.jsv', 'wt') as w:
    ...     w['t1'] = '{"key_1"}'
    ...     w['t2'] = '[{"key_2"}]'
    ...     for tid, rec in data:
    ...         w.write(rec, tid)

The resulting file will be:

.. code-block:: text

    #t1 {"key_1"}
    #t2 [{"key_2"}]
    @t1 {1}
    @t2 [{2},{null}]
"""

from .template import JSVTemplate, JSVRecordDecodeError, JSVTemplateDecodeError
from .template_io import JSVCollection, JSVReader, JSVWriter
from .__version__ import __description__, __url__, __version__, __commit_hash__, __author__, __author_email__
from .__version__ import __license__, __copyright__
