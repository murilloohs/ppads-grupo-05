import re
from dataclasses import dataclass
from pathlib import Path

_MIN_TEXT = 12
_MAX_PAGES = 3

_STOP = (
    r"(?=\s+(?:nome(?:\s+do\s+\w+)?|atividade|institui[cç][aã]o(?:\s+promotora)?|"
    r"promovido\s+por|realizado\s+por|per[ií]odo|data(?:\s+de\s+\w+)?|"
    r"carga\s+hor[aá]ria)\s*[:\-]|$)"
)
_NAME = re.compile(
    rf"(?:nome(?:\s+do\s+(?:aluno|participante))?|participante|aluno)\s*[:\-]\s*(.+?){_STOP}",
    re.IGNORECASE,
)
_ACTIVITY = re.compile(
    rf"(?:atividade|nome\s+do\s+curso|curso|evento|treinamento)\s*[:\-]\s*(.+?){_STOP}",
    re.IGNORECASE,
)
_INSTITUTION = re.compile(
    rf"(?:institui[cç][aã]o(?:\s+promotora)?|promovido\s+por|realizado\s+por)\s*[:\-]\s*(.+?){_STOP}",
    re.IGNORECASE,
)
_PERIOD = re.compile(
    rf"(?:per[ií]odo|data(?:\s+de\s+realiza[cç][aã]o)?|realizado\s+em)\s*[:\-]\s*(.+?){_STOP}",
    re.IGNORECASE,
)
_HOURS = re.compile(
    r"carga\s+hor[aá]ria(?:\s+total)?(?:\s+de)?\s*[:\-]?\s*(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_HOURS_FALLBACK = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:h|horas)\b", re.IGNORECASE)
_PROSE_NAME = re.compile(
    r"certificamos que\s+(.+?)\s+(?:participou|concluiu|frequentou)\b",
    re.IGNORECASE,
)
_PROSE_ACTIVITY = re.compile(
    r"participou d[aeo]s?\s+(?:atividade|curso|evento|treinamento)\s+(.+?)"
    r"(?=,|\s+promovid|\s+realizad|\s+no\s+per|\s+com\s+carga|$)",
    re.IGNORECASE,
)
_PROSE_INSTITUTION = re.compile(
    r"promovid[ao] pela(?:\s+institui[cç][aã]o)?\s+(.+?)"
    r"(?=,|\s+no\s+per|\s+com\s+carga|$)",
    re.IGNORECASE,
)
_PROSE_PERIOD = re.compile(
    r"per[ií]odo de\s+(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
_RANGE_PERIOD = re.compile(
    r"\bde\s+(\d{2}/\d{2}/\d{4})\s+(?:a|at[eé])\s+(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
_COURSE_SENTENCE = re.compile(
    r"\bcurso de\s+(.+?)\s*,\s*com\s+carga\s+hor",
    re.IGNORECASE,
)
_DATE = re.compile(r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}")
_PARTICLE = {"de", "da", "do", "dos", "das", "e"}
_RICH_TEXT = 500


@dataclass(frozen=True)
class OcrReading:
    ok: bool
    text: str | None
    fields: dict[str, str | None] | None


def extract_certificate_fields(text: str) -> dict[str, str | None]:
    lined = re.sub(r"[^\S\n]+", " ", text).strip()
    flat = re.sub(r"\s+", " ", lined)
    course, provider = _course_sentence(flat)
    return {
        "Nome": _value(_NAME, flat) or _value(_PROSE_NAME, flat) or _name_from_layout(lined),
        "Atividade": (
            _value(_ACTIVITY, flat)
            or _value(_PROSE_ACTIVITY, flat)
            or course
            or _course_heading(lined)
        ),
        "Instituição": _value(_INSTITUTION, flat) or _value(_PROSE_INSTITUTION, flat) or provider,
        "Data/período": _period(flat),
        "Carga horária": _hours(flat),
    }


class CertificateOcrService:
    def read(self, path: str, mime_type: str | None) -> OcrReading:
        try:
            text = self._extract_text(path, mime_type)
        except Exception:
            return OcrReading(False, None, None)
        cleaned = _clean(text)
        if len(cleaned) < _MIN_TEXT:
            return OcrReading(False, None, None)
        return OcrReading(True, cleaned[:20000], extract_certificate_fields(cleaned))


    def _extract_text(self, path: str, mime_type: str | None) -> str:
        kind = _kind(path, mime_type)
        if kind == "pdf":
            return self._pdf_text(path)
        if kind == "image":
            return self._image_text(path)
        return ""

    def _pdf_text(self, path: str) -> str:
        import fitz

        document = fitz.open(path)
        try:
            pages = list(document)[:_MAX_PAGES]
            digital = "\n".join(page.get_text() for page in pages)
            if not _should_scan(pages, digital):
                return digital
            try:
                scanned = self._ocr_pages(pages)
            except Exception:
                scanned = ""
            if not _clean(scanned):
                return digital
            return _merge_text(digital, scanned)
        finally:
            document.close()

    def _ocr_pages(self, pages) -> str:
        from PIL import Image

        chunks = []
        for page in pages:
            pixmap = page.get_pixmap(dpi=200)
            mode = "RGBA" if pixmap.alpha else "RGB"
            image = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
            chunks.append(_tesseract(image))
        return "\n".join(chunks)

    def _image_text(self, path: str) -> str:
        from PIL import Image

        with Image.open(path) as image:
            return _tesseract(image.convert("RGB"))


def _tesseract(image) -> str:
    import pytesseract

    try:
        return pytesseract.image_to_string(image, lang="por+eng")
    except pytesseract.TesseractNotFoundError:
        return ""
    except pytesseract.TesseractError:
        try:
            return pytesseract.image_to_string(image)
        except pytesseract.TesseractError:
            return ""


def _kind(path: str, mime_type: str | None) -> str:
    mime = (mime_type or "").split(";", 1)[0].strip().lower()
    suffix = Path(path).suffix.lower()
    if mime == "application/pdf" or suffix == ".pdf":
        return "pdf"
    if mime in {"image/jpeg", "image/jpg", "image/png"} or suffix in {".jpg", ".jpeg", ".png"}:
        return "image"
    return "unknown"


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text).strip()


def _value(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1)).strip(" .;-")
    return value[:180] or None


def _hours(text: str) -> str | None:
    labeled = _HOURS.search(text)
    if labeled:
        return labeled.group(1)
    found = _HOURS_FALLBACK.findall(text)
    if len(found) == 1:
        return found[0]
    return None


def _period(text: str) -> str | None:
    labeled = _value(_PERIOD, text)
    if labeled:
        dates = _unique_dates(labeled)
        if len(dates) >= 2:
            return f"{dates[0]} a {dates[1]}"
        if dates:
            return dates[0]
        return labeled
    prose = _PROSE_PERIOD.search(text) or _RANGE_PERIOD.search(text)
    if prose:
        return f"{prose.group(1)} a {prose.group(2)}"
    dates = _unique_dates(text)
    if len(dates) >= 2:
        return f"{dates[0]} a {dates[1]}"
    if len(dates) == 1:
        return dates[0]
    return None


def _unique_dates(text: str) -> list[str]:
    found = []
    for token in _DATE.findall(text):
        if token not in found:
            found.append(token)
    return found


def _course_sentence(text: str) -> tuple[str | None, str | None]:
    match = _COURSE_SENTENCE.search(text)
    if not match:
        return None, None
    body = match.group(1).strip(" .;-")
    split = re.match(r"(.+)\s+d[aeo]s?\s+([A-ZÀ-Ý0-9].+)$", body)
    if not split:
        return _clip(body), None
    return _clip(split.group(1)), _clip(split.group(2))


def _course_heading(text: str) -> str | None:
    for line in text.splitlines():
        match = re.match(r"Curso\s+(?!de\b)(.+)$", line.strip(), re.IGNORECASE)
        if match:
            return _clip(match.group(1))
    return None


def _name_from_layout(text: str) -> str | None:
    lines = [line.strip(" .;-") for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if re.match(r"concluiu\b", line, re.IGNORECASE) and index:
            candidate = lines[index - 1]
            if _looks_like_person(candidate):
                return _clip(candidate)
        inline = re.match(r"(.+?)\s+concluiu\b", line, re.IGNORECASE)
        if inline and _looks_like_person(inline.group(1)):
            return _clip(inline.group(1))
    return None


def _looks_like_person(value: str) -> bool:
    words = value.split()
    if not 2 <= len(words) <= 6 or any(char.isdigit() for char in value):
        return False
    capitals = 0
    for word in words:
        if word.casefold() in _PARTICLE:
            continue
        if not word[0].isupper():
            return False
        capitals += 1
    return capitals >= 2


def _clip(value: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", value).strip(" .;-")
    return cleaned[:180] or None


def _should_scan(pages, digital: str) -> bool:
    cleaned = _clean(digital)
    if len(cleaned) < _MIN_TEXT:
        return True
    return len(cleaned) < _RICH_TEXT and _has_large_image(pages)


def _has_large_image(pages) -> bool:
    for page in pages:
        area = float(page.rect.width * page.rect.height)
        if area <= 0:
            continue
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 1:
                continue
            x0, y0, x1, y1 = block["bbox"]
            if (x1 - x0) * (y1 - y0) >= area * 0.55:
                return True
    return False


def _merge_text(digital: str, scanned: str) -> str:
    if len(_clean(scanned)) < len(_clean(digital)):
        return digital
    scanned_flat = re.sub(r"\s+", " ", scanned)
    extra = [
        line.strip()
        for line in digital.splitlines()
        if line.strip() and line.strip() not in scanned_flat
    ]
    if not extra:
        return scanned
    return scanned.rstrip() + "\n" + "\n".join(extra)

