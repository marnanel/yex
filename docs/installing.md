# Installing yex

yex is not yet in the Python package repository, so you'll have to install
from source. This makes the instructions overly complicated.
If they don't work for you, I'd love to hear about it.

I'm going to assume you have Python, git, and make installed, and
that you're using a Unix-like system (Linux, BSD, or a Mac).

yex runs under Python 3, not Python 2. You can tell which you have
by typing
```
python --version
```

If it tells you it's Python 2, Python 3 might be available by
writing `python3` instead of `python`.

## How to install yex

Get the code:
```
git clone https://gitlab.com/marnanel/yex.git
cd yex
```

Build a virtual environment for it:
```
make venv
source venv/bin/activate
```

Install the dependencies, which will take ages:
```
make dependencies
```

Run the tests, to check everything's working:
```
make test
```

They might not all pass, because you're running a development build.
But if they all succeeded, or *mostly* all succeeded,
let's go ahead and install it.

If you followed the instructions and built a virtual environment:
```
make install
```

If you didn't, you'll have to use sudo. I'll assume you know how to do that.

Now let's [go on and start using it](running.md)!
