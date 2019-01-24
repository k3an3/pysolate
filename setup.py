from setuptools import setup, find_packages

setup(
    name='pysolate',
    version='0.1',
    packages=find_packages(),
    url='',
    license='MIT',
    author="Keane O'Kelley",
    author_email='keane.m.okelley@gmail.com',
    include_package_data=True,
    description='',
    entry_points={
        'console_scripts': [
            'c=pysolate:main',
            'contain=pysolate:main',
        ]
    },
)
