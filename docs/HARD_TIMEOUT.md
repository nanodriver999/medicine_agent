# Hard deadline for CPU ADMET worker

`amo.isolated_worker.invoke_bounded` starts a fresh Python `spawn`
subprocess with an optional picklable test predictor (production defaults to
`ADMETModel().predict`). A deadline triggers process termination and, if
needed, kill. Failed workers return only sanitized error codes. The adapter
still validates numerical predictions, because a valid worker envelope is
not a verified scientific prediction.

`predict_with_deadline` can be injected into `ADMETAdapter` as its predictor:

```python
from functools import partial
from amo.isolated_worker import predict_with_deadline
from amo.admet import ADMETAdapter, Endpoint

model = ADMETAdapter(
    Endpoint("VERIFIED_ENDPOINT", "min", "VERIFIED_UNIT", "PINNED_REVISION"),
    predictor=partial(predict_with_deadline, timeout_seconds=120),
)
```

**Operational caveats:** fresh-process model loading is expensive and can
download the model on every call. The current implementation is suitable for
fault isolation and smoke testing, not efficient production batch inference.
Subprocess descendants and GPU resources may require additional process-group
cleanup. A per-call hard deadline is not an overall agent/LLM time limit.
Retry usage must be reserved in the enclosing budget as implemented in PR #18.
No real ADMET weights were exercised by the offline CI tests.
