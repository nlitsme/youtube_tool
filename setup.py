from setuptools import setup
setup(
    name = "youtube_tool",
    version = "1.0.6",
    entry_points = {
        'console_scripts': ['yttool=yttool:main'],
    },
    py_modules=['yttool'],
    author = "Willem Hengeveld",
    author_email = "itsme@xs4all.nl",
    description = "Extract information from youtube video's",
    long_description="""
Commandline tool which can extract comments, subtitles or livechat
content from a youtube video. It can also list all video's
in a playlist, or from a search result.
""",

    license = "MIT",
    keywords = "youtube commandline",
    url = "https://github.com/nlitsme/youtube_tool/",
    classifiers = [
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    python_requires = '>=3.8',
)
