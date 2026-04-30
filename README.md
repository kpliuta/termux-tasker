# termux-tasker

TBD


## Install dependencies

For prod build:

```
poetry install
```

For dev build:

```
poetry install --with dev
```


## Sync dependencies

For prod build:

```
poetry sync
```

For dev build:

```
poetry sync --with dev
```


## Test execution

```
poetry run python -m textual_dev run --dev tests/ui/base/file_browser_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/info_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/input_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/loading_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/log_screen.py
poetry run python -m textual_dev run --dev tests/ui/base/menu_screen.py
```
