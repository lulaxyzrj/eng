"""
Collection of code snippets, keywords, and dev memes for Dev Hero game.
"""

import random

# Python snippets
PYTHON_SNIPPETS = [
    "from pprint import pprint",
    "ValueError: invalid literal for int()",
    "try: except:",
    "lambda x: x * 2",
    "def __init__(self):",
    "import os, sys",
    "if __name__ == '__main__':",
    "raise NotImplementedError",
    "async def fetch_data():",
    "with open('file.txt') as f:",
    "list(map(lambda x: x**2, range(10)))",
    "[x for x in range(10) if x % 2 == 0]",
    "f'{name} is {age} years old'",
    "except Exception as e:",
    "yield from generator()",
    "from functools import reduce, lru_cache",
    "class Meta(type): pass",
    "async with aiohttp.ClientSession() as session:",
    "from dataclasses import dataclass, field",
    "from typing import List, Dict, Optional, Union",
    "contextlib.contextmanager",
    "from collections import defaultdict, Counter",
    "decorator = lambda f: lambda *args, **kwargs: f(*args, **kwargs)",
    "[(x, y) for x in range(5) for y in range(5) if x != y]",
    "next(filter(lambda x: x > 10, numbers), None)",
    "from pathlib import Path; Path('file.txt').read_text()",
    "globals()['variable_name'] = value",
    "exec('print(\"Hello\")')",
    "eval('2 + 2')",
    "import this  # The Zen of Python",
    "__import__('os').system('ls')",
    "from itertools import chain, combinations",
    "super().__init__(*args, **kwargs)",
    "raise ValueError('Invalid input') from original_error",
]

# JavaScript snippets
JAVASCRIPT_SNIPPETS = [
    "const arrowFunction = () => {}",
    "console.log('Hello World')",
    "async function fetchData() {}",
    "const [a, b] = array",
    "obj?.property?.nested",
    "Array.from(new Set(arr))",
    "Promise.all(promises)",
    "const { name, age } = user",
    "arr.map(x => x * 2)",
    "`${variable} template`",
    "const fn = (...args) => args.reduce((a, b) => a + b)",
    "Object.entries(obj).map(([k, v]) => `${k}: ${v}`)",
    "await Promise.allSettled(promises)",
    "const memoized = useMemo(() => compute(), [deps])",
    "const debounced = useCallback(debounce(fn, 300), [])",
    "arr.flatMap(x => x.map(y => y * 2))",
    "new Proxy(target, { get: (obj, prop) => obj[prop] })",
    "Symbol.iterator in obj",
    "const gen = function*() { yield 1; yield 2; }",
    "Object.assign({}, obj1, obj2)",
    "JSON.parse(JSON.stringify(obj))",
    "Array.from({ length: 10 }, (_, i) => i)",
    "const curry = fn => (...args) => fn.bind(null, ...args)",
    "Object.freeze(obj); Object.seal(obj)",
    "Reflect.get(obj, 'property')",
    "const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x)",
    "arr.reduce((acc, val) => ({ ...acc, [val.id]: val }), {})",
    "const compose = (...fns) => x => fns.reduceRight((v, f) => f(v), x)",
    "new Set([...arr1, ...arr2])",
    "Object.keys(obj).forEach(key => console.log(key, obj[key]))",
    "const deepClone = obj => JSON.parse(JSON.stringify(obj))",
    "Array.prototype.flat.call(nestedArray, Infinity)",
]

# Error messages that every dev hates
ERROR_MESSAGES = [
    "Merge conflict detected",
    "Unexpected token '<'",
    "NullPointerException",
    "404 Not Found",
    "500 Internal Server Error",
    "SyntaxError: unexpected EOF",
    "TypeError: Cannot read property",
    "ModuleNotFoundError: No module named",
    "IndentationError: expected an indented block",
    "ReferenceError: variable is not defined",
    "Maximum call stack size exceeded",
    "Cannot read property 'length' of undefined",
    "Uncaught TypeError: Cannot set property",
    "ERR_CONNECTION_REFUSED",
    "Segmentation fault (core dumped)",
    "OutOfMemoryError: Java heap space",
    "TypeError: 'NoneType' object is not iterable",
    "AttributeError: 'list' object has no attribute 'split'",
    "KeyError: 'key' not found in dictionary",
    "UnboundLocalError: local variable referenced before assignment",
    "ImportError: attempted relative import with no known parent package",
    "RecursionError: maximum recursion depth exceeded",
    "StopIteration: generator raised StopIteration",
    "AssertionError: assertion failed",
    "PermissionError: [Errno 13] Permission denied",
    "FileNotFoundError: [Errno 2] No such file or directory",
    "TimeoutError: The read operation timed out",
    "ConnectionResetError: [Errno 104] Connection reset by peer",
    "ValueError: too many values to unpack (expected 2)",
    "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
]

# Classic dev memes
DEV_MEMES = [
    "I have no idea why this works",
    "Works on my machine",
    "Rubber duck debugging",
    "It's not a bug, it's a feature",
    "Copy-paste from Stack Overflow",
    "Just ship it",
    "This should be quick",
    "I'll fix it later",
    "The code is self-documenting",
    "It works in production",
    "I tested it locally",
    "That's a hardware issue",
    "Works for me",
    "Can't reproduce",
    "It's a caching issue",
    "99 little bugs in the code, 99 bugs in the code",
    "Take one down, patch it around, 98 bugs in the code",
    "First rule of programming: if it works, don't touch it",
    "There are only 10 types of people: those who understand binary",
    "I don't always test my code, but when I do, I do it in production",
    "Real programmers count from zero",
    "Any fool can write code that a computer can understand",
    "Good programmers write code that humans can understand",
    "Premature optimization is the root of all evil",
    "Debugging is twice as hard as writing the code in the first place",
    "If debugging is the process of removing bugs, then programming must be",
    "The best code is no code at all",
    "Code is like humor. When you have to explain it, it's bad",
    "One man's constant is another man's variable",
    "There is no such thing as a bug-free program",
    "The only way to learn a new programming language is by writing programs",
    "Before software can be reusable, it first has to be usable",
    "Good code is its own best documentation",
    "The best thing about a boolean is even if you're wrong, you're only off by a bit",
    "There are two ways to write error-free programs; only the third one works",
    "The problem with troubleshooting is that trouble shoots back",
    "If at first you don't succeed, call it version 1.0",
    "A user interface is like a joke. If you have to explain it, it's not that good",
    "The best code is written so that the next developer can understand it",
    "Code never lies, comments sometimes do",
    "The fastest code is the code that doesn't run",
    "I'm not lazy, I'm just very relaxed",
    "Programmers don't die, they just go offline",
    "There are only two kinds of programming languages: those people complain about",
    "and those nobody uses",
    "The best error message is the one that never shows up",
    "I would love to change the world, but they won't give me the source code",
    "Real programmers don't comment their code. It was hard to write",
    "it should be hard to understand",
    "The computer is a moron",
    "Programs must be written for people to read, and only incidentally for machines",
    "The most disastrous thing that you can ever learn is your first programming language",
    "Walking on water and developing software from a specification are easy",
    "if both are frozen",
    "Measuring programming progress by lines of code is like measuring aircraft building",
    "progress by weight",
    "The best way to get a project done faster is to start sooner",
    "If builders built buildings the way programmers wrote programs",
    "then the first woodpecker that came along would destroy civilization",
    "Computers are good at following instructions, but not at reading your mind",
    "The only way to learn a new programming language is by writing programs in it",
    "The best code is no code",
    "Code is read much more often than it is written",
    "Make it work, make it right, make it fast",
    "Premature optimization is the root of all evil in programming",
    "The best error message is the one that never shows up",
    "I don't care if it works on your machine! We are not shipping your machine!",
    "The problem with troubleshooting is that trouble shoots back",
    "There are only 10 types of people in the world: those who understand binary",
    "and those who don't",
    "The best thing about a boolean is even if you're wrong, you're only off by a bit",
    "First, solve the problem. Then, write the code",
    "Experience is the name everyone gives to their mistakes",
    "It's not a bug, it's an undocumented feature",
    "The best code is the code you don't have to write",
    "Code is like humor. When you have to explain it, it's bad",
    "The only way to learn a new programming language is by writing programs in it",
    "The best error message is the one that never shows up",
    "I don't care if it works on your machine! We are not shipping your machine!",
    "The problem with troubleshooting is that trouble shoots back",
    "There are only 10 types of people in the world: those who understand binary",
    "and those who don't",
    "The best thing about a boolean is even if you're wrong, you're only off by a bit",
    "First, solve the problem. Then, write the code",
    "Experience is the name everyone gives to their mistakes",
    "It's not a bug, it's an undocumented feature",
    "The best code is the code you don't have to write",
    "Code is like humor. When you have to explain it, it's bad",
]

# Programming keywords
KEYWORDS = [
    "function",
    "variable",
    "algorithm",
    "recursion",
    "iteration",
    "polymorphism",
    "inheritance",
    "encapsulation",
    "abstraction",
    "asynchronous",
    "callback",
    "promise",
    "closure",
    "decorator",
    "generator",
    "iterator",
    "singleton",
    "factory",
    "observer",
    "middleware",
]

# All challenges combined
ALL_CHALLENGES = (
    PYTHON_SNIPPETS +
    JAVASCRIPT_SNIPPETS +
    ERROR_MESSAGES +
    DEV_MEMES +
    KEYWORDS
)


def get_random_challenge():
    """Return a random challenge from all available challenges."""
    return random.choice(ALL_CHALLENGES)


def get_challenges_by_category(category):
    """Get challenges by category.
    
    Args:
        category: One of 'python', 'javascript', 'errors', 'memes', 'keywords'
    
    Returns:
        List of challenges from the specified category
    """
    categories = {
        'python': PYTHON_SNIPPETS,
        'javascript': JAVASCRIPT_SNIPPETS,
        'errors': ERROR_MESSAGES,
        'memes': DEV_MEMES,
        'keywords': KEYWORDS,
    }
    return categories.get(category.lower(), ALL_CHALLENGES)

