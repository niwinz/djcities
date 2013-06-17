from setuptools import setup

description = """
A full database of contry/state/city/timezone for django. Based on django-cities but
with more clean codebase.
"""

setup(
    name = "djcities",
    url = "https://github.com/niwibe/djcities",
    author = "Andrey Antukh",
    author_email = "niwi@niwi.be",
    version='0.1',
    packages = [
        "djcities",
        "djcities.management",
        "djcities.management.commands",
    ],
    description = description.strip(),
    zip_safe=False,
    include_package_data = True,
    classifiers = [
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        #"Programming Language :: Python :: 3",
        #"Programming Language :: Python :: 3.2",
        #"Programming Language :: Python :: 3.3",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
)
