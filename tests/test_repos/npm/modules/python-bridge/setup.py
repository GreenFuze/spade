from setuptools import setup, Extension

setup(
    name="python-bridge",
    version="1.0.0",
    ext_modules=[
        Extension("bridge", ["bridge.c"])
    ]
)
