"""Transform pipeline — chain of data transformations."""

from typing import Callable
from dataclasses import dataclass

from app.infrastructure.data_mapping.adapters import DataRecord


@dataclass
class TransformStep:
    name: str
    fn: Callable[[DataRecord], DataRecord]


class TransformPipeline:
    """Chain of transform functions applied to data records.

    Usage:
        pipeline = TransformPipeline()
        pipeline.add("clean_dates", clean_date_fields)
        pipeline.add("normalize_names", normalize_name_field)
        results = pipeline.run(records)
    """

    def __init__(self):
        self._steps: list[TransformStep] = []

    def add(self, name: str, fn: Callable[[DataRecord], DataRecord]) -> "TransformPipeline":
        self._steps.append(TransformStep(name=name, fn=fn))
        return self

    def run(self, records: list[DataRecord]) -> list[DataRecord]:
        for step in self._steps:
            records = [step.fn(r) for r in records]
        return records


# Common transform functions

def lowercase_keys(record: DataRecord) -> DataRecord:
    """Normalize all keys to lowercase."""
    if record.normalized:
        record.normalized = {k.lower(): v for k, v in record.normalized.items()}
    return record


def strip_whitespace(record: DataRecord) -> DataRecord:
    """Strip whitespace from string values."""
    if record.normalized:
        record.normalized = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in record.normalized.items()
        }
    return record


def drop_nulls(record: DataRecord) -> DataRecord:
    """Remove keys with None values."""
    if record.normalized:
        record.normalized = {k: v for k, v in record.normalized.items() if v is not None}
    return record
