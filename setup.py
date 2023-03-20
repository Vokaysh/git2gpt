from setuptools import setup, find_packages
from git2gpt.version import version

setup(
    name='git2gpt',
    version=version,
    packages=find_packages(),
    install_requires=[
        'openai>=0.27.2',
        'tiktoken',
        'python-dotenv'
    ],
    entry_points={
        'console_scripts': [
            'git2gpt=git2gpt.main:main'
        ]
    }
)