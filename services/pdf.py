"""
Renders CV and cover letter to HTML and PDF using Jinja2 templates + Playwright (Chromium).
"""
import base64
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from services.generation import CVContent

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"
PROFILE_DIR = Path(__file__).parent.parent / "data" / "profile"

_jinja = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def _ensure_output_dir(subdir: str) -> Path:
    path = OUTPUT_DIR / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_photo_data_uri() -> str | None:
    """Return a base64 data URI for the profile photo, or None if not found."""
    for name in ("photo.jpg", "photo.jpeg", "photo.png", "photo.webp"):
        photo_path = PROFILE_DIR / name
        if photo_path.exists():
            ext = photo_path.suffix.lstrip(".")
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            data = base64.b64encode(photo_path.read_bytes()).decode()
            return f"data:{mime};base64,{data}"
    return None


def _html_to_pdf(html_str: str, out_path: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_str, wait_until="networkidle")
        page.pdf(
            path=str(out_path),
            format="A4",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
        )
        browser.close()


def html_to_pdf(html_path: Path) -> Path:
    """Convert a saved HTML file to PDF in the same directory."""
    html_str = html_path.read_text(encoding="utf-8")
    out_path = html_path.with_suffix(".pdf")
    _html_to_pdf(html_str, out_path)
    return out_path


def render_cv(cv: CVContent, output_subdir: str) -> tuple[Path, Path]:
    """Render CV to both HTML and PDF. Returns (pdf_path, html_path)."""
    photo = _get_photo_data_uri()
    template = _jinja.get_template("cv.html")
    html_str = template.render(cv=cv, photo=photo)

    out_dir = _ensure_output_dir(output_subdir)
    html_path = out_dir / "cv.html"
    pdf_path = out_dir / "cv.pdf"

    html_path.write_text(html_str, encoding="utf-8")
    _html_to_pdf(html_str, pdf_path)
    return pdf_path, html_path


def render_cover_letter(
    cv: CVContent,
    cover_letter_text: str,
    job_title: str,
    job_company: str,
    output_subdir: str,
) -> tuple[Path, Path]:
    """Render cover letter to both HTML and PDF. Returns (pdf_path, html_path)."""
    paragraphs = [p.strip() for p in cover_letter_text.split("\n\n") if p.strip()]

    template = _jinja.get_template("cover_letter.html")
    html_str = template.render(
        name=cv.name,
        email=cv.email,
        phone=cv.phone,
        location=cv.location,
        linkedin_url=cv.linkedin_url,
        language=cv.language,
        job_title=job_title,
        job_company=job_company,
        paragraphs=paragraphs,
    )

    out_dir = _ensure_output_dir(output_subdir)
    html_path = out_dir / "cover_letter.html"
    pdf_path = out_dir / "cover_letter.pdf"

    html_path.write_text(html_str, encoding="utf-8")
    _html_to_pdf(html_str, pdf_path)
    return pdf_path, html_path
