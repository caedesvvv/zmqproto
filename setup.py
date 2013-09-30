from distutils.core import setup
import sys

setup(
        name='zmqproto',
        version='0.1.0',
        packages=['zmqproto', 'txzmq.test'],
        license='AGPLv3',
        author='Pablo Martin',
        author_email='caedes@sindominio.net',
        url='https://github.com/caedesvvv/zmqproto',
        description='Pure python zmq protocol implementation',
        long_description=open('README.md').read(),
        install_requires=["Twisted>=10.0"],
        )
