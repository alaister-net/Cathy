from setuptools import setup

setup(
    name='cathy',
    version='4.0.1',
    description='Discord chat bot using AIML artificial intelligence.',
    long_description="See https://github.com/DevDungeon/cathy",
    url='https://github.com/DevDungeon/ChattyCathy',
    author='DevDungeon',
    author_email='nanodano@devdungeon.com',
    license='GPL-3.0',
    packages=['cathy'],
    entry_points={
        'console_scripts': [
            'cathy = cathy.__main__:main',
        ],
    },
    package_data={
        'cathy': [
            'std-startup.xml',
            'aiml/alice/*.aiml',
            'aiml/custom/*.aiml'
        ],
    },
    zip_safe=False,
    install_requires=[
        'disnake~=2.2.1',
        'python-aiml~=0.9.3',
        'python-dotenv~=0.19.1',
    ],
    python_requires='>=3.8',
)
