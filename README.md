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

## License

`happy-python-logging` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
