# obp-accounting-sdk

[![Build status][build_status_badge]][build_status_target]
[![License][license_badge]][license_target]
[![Code coverage][coverage_badge]][coverage_target]
[![CodeQL][codeql_badge]][codeql_target]
[![PyPI][pypi_badge]][pypi_target]

## Description

Python SDK for the OBP Accounting Service.


## Usage

The API provides the following main classes to be used asynchronously:

- `obp_accounting_sdk.AsyncAccountingSessionFactory`
- `obp_accounting_sdk.AsyncOneshotSession`

and the corresponding synchronous versions:

- `obp_accounting_sdk.AccountingSessionFactory`
- `obp_accounting_sdk.OneshotSession`

The factory class must be instantiated only once, and a new session can be obtained by calling the `oneshot_session` method used as a context manager:

```python
subtype: ServiceSubtype = ...
proj_id: UUID = ...
estimated_count: int = ...
async with accounting_session_factory.oneshot_session(
    subtype=subtype,
    proj_id=proj_id,
    count=estimated_count,
) as acc_session:
    # actual logic
    acc_session.count = actual_count
```

In the example above:
- The reservation with the accounting service happens when entering the context manager.
- The usage is sent to the accounting service when exiting the context manager, unless an exception is raised, because in this case we suppose that the actual business logic to be charged didn't get executed.
- The value of `estimated_count` is used for reservation, and it's used also for usage unless a new value is assigned to `acc_session.count`.


## Example

See the [Demo app](demo/app) for a working example integrated in a simple FastAPI app.

If you installed `tox`, you can set the required env variables and run the demo with:

```bash
export ACCOUNTING_BASE_URL=http://127.0.0.1:8100
export UVICORN_PORT=8000
tox -e demo
```

and call the endpoint after setting a valid project-id with:

```bash
export PROJECT_ID=8eb248a8-672c-4158-9365-b95286cba796
curl -vs "http://127.0.0.1:$UVICORN_PORT/query" \
-H "content-type: application/json" \
-H "project-id: $PROJECT_ID" \
--data-binary @- <<EOF
{"input_text": "my query"}
EOF
```

Contribution Guidelines
-----------------------

See [CONTRIBUTING](CONTRIBUTING.md).


Acknowledgment
--------------

The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology.

For license and authors, see [LICENSE](LICENSE.txt) and [AUTHORS](AUTHORS.txt) respectively.

Copyright © 2024 Blue Brain Project/EPFL


[build_status_badge]: https://github.com/BlueBrain/obp-accounting-sdk/actions/workflows/run-tox.yml/badge.svg
[build_status_target]: https://github.com/BlueBrain/obp-accounting-sdk/actions
[license_badge]: https://img.shields.io/pypi/l/obp-accounting-sdk
[license_target]: https://github.com/BlueBrain/obp-accounting-sdk/blob/main/LICENSE.txt
[coverage_badge]: https://codecov.io/github/BlueBrain/obp-accounting-sdk/coverage.svg?branch=main
[coverage_target]: https://codecov.io/github/BlueBrain/obp-accounting-sdk?branch=main
[codeql_badge]: https://github.com/BlueBrain/obp-accounting-sdk/actions/workflows/github-code-scanning/codeql/badge.svg
[codeql_target]: https://github.com/BlueBrain/obp-accounting-sdk/actions/workflows/github-code-scanning/codeql
[pypi_badge]: https://github.com/BlueBrain/obp-accounting-sdk/actions/workflows/publish-sdist.yml/badge.svg
[pypi_target]: https://pypi.org/project/obp-accounting-sdk/
