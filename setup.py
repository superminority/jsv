import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'jsv', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=open(os.path.join(here, 'README.rst')).read(),
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=find_packages(),
    package_dir={'jsv': 'jsv'},
    include_package_data=False,
    zip_safe=True,
    python_requires=">=3.4",
    tests_require=[
        'pytest'
    ],
    license=about['__license__'],
    data_files=[("", ["LICENSE"])],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Topic :: Text Processing'
    ]
)
