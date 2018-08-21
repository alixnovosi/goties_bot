"""Setup for goties_bot"""

from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

with open(path.join(HERE, "VERSION"), encoding="utf-8") as f:
    VERSION = f.read().strip()

setup(author="Andrew Michaud",
      author_email="bots+goties@mail.andrewmichaud.com",
      url="https://github.com/andrewmichaud/goties_bot",

      entry_points={"console_scripts": ["goties__bot = goties_bot.__main__:main"]},

      install_requires=["botskeleton>=3.0.1", "Pillow", "pyyaml>=3.13"],
      python_requires=">=3.6",

      license="BSD3",

      name="goties_bot",

      packages=find_packages(),

      version=VERSION)
