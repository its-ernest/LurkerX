# Token Generation Manual

Recommended to clone the repo to your system. 

```bash
# Clone repo
$ git clone https://github.com/the-hollowclan/LurkerX && cd LurkerX

# Ensure you have python3 installed
$ python3 --version

# Create a virtual envirionment
$ python3 -m venv venv

# Activate virtual environment
$ source ./venv/bin/activate

# Install requirements
$ python -m pip install -r requirements.txt

# Enter Python shell and start token generation
$ python

Python 3.14.5 (main, May 10 2026, 18:26:20) [GCC 16.1.1 20260430] on linux
Type "help", "copyright", "credits" or "license" for more information.
...
>>> from token_generator import generate_token
>>> token = generate_token(tool_name="LurkerX", days_valid=14)
>>> print(token)
gAAAAABqcEm863TY59cFPkKVbj_QHgDuG3CIWHePqgPGIaaymHRCddC1U1_bT1NyX5P5XBBvm-uMArWnT8Dq-yOQxyqxZ3a2VPVAs6ayqdLq10_K7pQDD0z3_XTUX0Itdjj2N-IXnK98gOn51XrtlLkJBolWTHn7cr7FIuAyIKv-fAmgJwcExKw=
>>> CTRL + D
```
