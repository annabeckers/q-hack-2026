"""Document extractors — PDF, CSV, JSON."""

import csv
import json
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractedDocument:
    source: str
    content: str
    metadata: dict


class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, file_path: Path) -> list[ExtractedDocument]:
        ...


class PDFExtractor(BaseExtractor):
    """Extract text from PDFs using kreuzberg."""

    async def extract(self, file_path: Path) -> list[ExtractedDocument]:
        from kreuzberg import extract_file

        result = await extract_file(file_path)
        return [
            ExtractedDocument(
                source=str(file_path),
                content=result.content,
                metadata={"type": "pdf", "filename": file_path.name},
            )
        ]


class CSVExtractor(BaseExtractor):
    """Extract rows from CSV files as documents."""

    async def extract(self, file_path: Path) -> list[ExtractedDocument]:
        docs = []
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                docs.append(
                    ExtractedDocument(
                        source=f"{file_path}:row_{i}",
                        content=json.dumps(row),
                        metadata={"type": "csv", "filename": file_path.name, "row": i},
                    )
                )
        return docs


class JSONExtractor(BaseExtractor):
    """Extract documents from JSON files (array of objects or single object)."""

    async def extract(self, file_path: Path) -> list[ExtractedDocument]:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return [
                ExtractedDocument(
                    source=f"{file_path}:item_{i}",
                    content=json.dumps(item),
                    metadata={"type": "json", "filename": file_path.name, "index": i},
                )
                for i, item in enumerate(data)
            ]
        return [
            ExtractedDocument(
                source=str(file_path),
                content=json.dumps(data),
                metadata={"type": "json", "filename": file_path.name},
            )
        ]


EXTRACTORS: dict[str, type[BaseExtractor]] = {
    ".pdf": PDFExtractor,
    ".csv": CSVExtractor,
    ".json": JSONExtractor,
}


def get_extractor(file_path: Path) -> BaseExtractor:
    ext = file_path.suffix.lower()
    if ext not in EXTRACTORS:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(EXTRACTORS.keys())}")
    return EXTRACTORS[ext]()
