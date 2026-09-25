import tempfile
import unittest
from pathlib import Path

from docx import Document

from documents.loaders import chunk_text, extract_text


class DocumentLoaderTests(unittest.TestCase):
    def test_chunk_text_keeps_overlap(self) -> None:
        text = "А" * 400 + "\n\n" + "Б" * 400 + "\n\n" + "В" * 400
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(chunks[1].startswith(chunks[0][-50:]))

    def test_extract_txt(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            path = Path(tmp) / "note.txt"
            path.write_text("Офис в Казани", encoding="utf-8")
            self.assertIn("Казани", extract_text(path))

    def test_extract_docx(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            path = Path(tmp) / "note.docx"
            document = Document()
            document.add_paragraph("Цена Лапка-Про — 12400 рублей")
            document.save(path)
            self.assertIn("12400", extract_text(path))
