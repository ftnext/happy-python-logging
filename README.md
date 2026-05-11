# happy-python-logging

Make practical Python logging easy.

[![PyPI - Version](https://img.shields.io/pypi/v/happy-python-logging.svg)](https://pypi.org/project/happy-python-logging)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/happy-python-logging.svg)](https://pypi.org/project/happy-python-logging)

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install happy-python-logging
```

## Usage

### For library developers

#### `getLoggerForLibrary()`

`happy_python_logging.getLoggerForLibrary()`

```diff
-import logging
+from happy_python_logging import getLoggerForLibrary

-logger = logging.getLogger(__name__)
-logger.addHandler(logging.NullHandler())
+logger = getLoggerForLibrary(__name__)
```

See [`example`](https://github.com/ftnext/happy-python-logging/tree/main/example) for detail.

#### `OrFilter`

`happy_python_logging.lib.filters.OrFilter`

```python
import logging

from happy_python_logging.lib.filters import OrFilter

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.addFilter(OrFilter("libA", "libB"))
root_logger.addHandler(stream_handler)
```

```
DEBUG | libA:libA_awesome:8 - awesome
DEBUG | libB:libB_fabulous:12 - fabulous
```

You can combine `OrFilter` with `logging.Filter` using the `|` operator:

```python
OrFilter("libA", "libB") | logging.Filter("app.important")
# reverse order also supported
```

### CLI: `happy-python-logging run` (experimental)

Run any Python script with quick library-level logging — RUST_LOG style:

```console
$ happy-python-logging run example_script.py --log-config httpx=debug
```

Multiple loggers can be set at once, comma-separated:

```console
$ happy-python-logging run example_script.py --log-config httpx=debug,urllib3=info
```

The same spec can be supplied via the `PYTHON_LOG` environment variable:

```console
$ PYTHON_LOG=httpx=debug happy-python-logging run example_script.py
```

A bare level (e.g. `--log-config debug`) sets the root logger.
The `StreamHandler` (stderr) and `Formatter` are fixed — the goal is to get
library logs onto the console with one flag.

## License

`happy-python-logging` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
