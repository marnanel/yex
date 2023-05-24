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
        url='https://gitlab.org/marnanel/yex',
        license='GPL-2',
        description="Typeset beautifully. TeX workalike.",
        long_description=README,
        long_description_content_type='text/markdown',
        author='Marnanel Thurman',
        author_email='marnanel@thurman.org.uk',
        packages=[
            'yex',
            'yex.box',
            'yex.control',
            'yex.font',
            'yex.mode',
            'yex.output',
            'yex.parse',
            'yex.value',
            ],
        include_package_data=True,
        install_requires=[
            'appdirs==1.4.4',
            'pytest==5.3.5',
            'pyfakefs==4.5.4',
            'Pillow==9.0.0',
            'pylint==2.4.4',
            'pytest==5.3.5',
            ],
        python_requires=">=3.0",
        zip_safe=False, # for now, anyway
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            ],
        entry_points={
            'console_scripts': [
                'yex=yex.__main__:main',
                'yex-show-font=yex.font.__main__:main',
                ],
            },
        )
