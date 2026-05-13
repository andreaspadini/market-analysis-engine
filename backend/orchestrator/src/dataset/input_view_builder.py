from typing import Any, Mapping

from .dataset_schema import DatasetInputView, DatasetResolved


def _canonicalize_dataset(dataset: DatasetResolved) -> dict[str, Any]:
    """
    Project DatasetResolved into the canonical dataset section used inside
    DatasetInputView.inputs["dataset"].
    """
    return {
        "dataset_id": dataset.dataset_id,
        "end_date": dataset.end_date,
        "instruments": list(dataset.instruments),
        "start_date": dataset.start_date,
        "timeframe": dataset.timeframe,
    }


def _canonicalize_value(value: Any) -> Any:
    """
    Recursively convert values into JSON-serializable canonical structures.

    Rules:
    - mappings -> plain dict with deterministic key order
    - tuple/list -> list
    - set/frozenset -> sorted list
    - scalars -> unchanged
    """
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize_value(value[key])
            for key in sorted(value.keys(), key=lambda k: str(k))
        }

    if isinstance(value, (list, tuple)):
        return [_canonicalize_value(item) for item in value]

    if isinstance(value, (set, frozenset)):
        return [
            _canonicalize_value(item)
            for item in sorted(value, key=lambda item: repr(item))
        ]

    return value


def build_dataset_input_view(
    *,
    tool_id: str,
    dataset: DatasetResolved,
    inputs: Mapping[str, Any],
    parameters: Mapping[str, Any],
) -> DatasetInputView:
    """
    Build the canonical DatasetInputView used downstream by D4.
    """
    merged_inputs = dict(inputs)
    merged_inputs["dataset"] = _canonicalize_dataset(dataset)

    canonical_inputs = _canonicalize_value(merged_inputs)
    canonical_parameters = _canonicalize_value(dict(parameters))

    return DatasetInputView(
        tool_id=tool_id,
        inputs=canonical_inputs,
        parameters=canonical_parameters,
    )