import os
import re
from io import open
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open('README.md', 'r', encoding='utf-8').read()

def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

version = get_version('yex')

setup(
        name='yex',
        version=version,
        url='https://kepi.org.uk',
        license='GPL-2',
        description="Typeset beautifully. TeX workalike.",
        long_description=README,
        long_description_content_type='text/markdown',
        author='Marnanel Thurman',
        author_email='marnanel@thurman.org.uk',
        packages=[
            'yex',
            'yex.control',
            'yex.font',
            'yex.output',
            'yex.parse',
            'yex.value',
            ],
        include_package_data=True,
        install_requires=[],
        python_requires=">=3.0",
        zip_safe=False, # for now, anyway
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Education',
            'Intended Audience :: Other',
            'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
            'Topic :: Text Processing :: Markup :: LaTeX',
            ],
        entry_points={
            'console_scripts': ['yex=yex.__main__:main'],
            },
        )
