"""Generate minimal zoology-themed sample files for local search tests."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from xlwt import Workbook


def write_samples(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    mammals = root / "mammals"
    birds = root / "birds"
    marine = root / "marine"
    for folder in (mammals, birds, marine):
        folder.mkdir(parents=True, exist_ok=True)

    (root / "overview.txt").write_text(
        "Zoology sample corpus: mammals, birds, marine life, and reptiles.\n",
        encoding="utf-8",
    )
    (mammals / "elephant_facts.txt").write_text(
        "African elephants are the largest land mammals. They use tusks for foraging.\n",
        encoding="utf-8",
    )
    (root / "reptiles").mkdir(exist_ok=True)
    (root / "reptiles" / "gecko_notes.txt").write_text(
        "Geckos are reptiles known for vocal communication and toe pad adhesion.\n",
        encoding="utf-8",
    )

    doc = Document()
    doc.add_heading("Marine Mammals", level=1)
    doc.add_paragraph(
        "Dolphins and whales belong to the order Cetacea. They breathe air and nurse their young."
    )
    doc.save(str(marine / "cetaceans.docx"))

    book = Workbook()
    sheet = book.add_sheet("Species")
    sheet.write(0, 0, "Species")
    sheet.write(0, 1, "Class")
    sheet.write(1, 0, "Monarch butterfly")
    sheet.write(1, 1, "Insecta")
    sheet.write(2, 0, "Green sea turtle")
    sheet.write(2, 1, "Reptilia")
    book.save(str(birds / "species_catalog.xls"))

    pdf_path = birds / "migration_study.pdf"
    pdf_canvas = canvas.Canvas(str(pdf_path), pagesize=letter)
    pdf_canvas.drawString(
        72,
        720,
        "Bird migration patterns across seasonal flyways and stopover habitats.",
    )
    pdf_canvas.save()

    img = Image.new("RGB", (64, 64), color=(120, 180, 90))
    img.save(birds / "butterfly.jpg", format="JPEG")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    write_samples(project_root / "data" / "samples" / "zoology")
    print("Sample data written.")
