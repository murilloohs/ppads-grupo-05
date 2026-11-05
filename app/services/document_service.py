import hashlib
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings


def validate_content(content: bytes, mime: str):
    if not content:
        raise HTTPException(400, "O arquivo está vazio.")
    try:
        if mime == "application/pdf":
            import fitz

            with fitz.open(stream=content, filetype="pdf") as document:
                if document.is_encrypted or document.page_count == 0:
                    raise ValueError("PDF protegido ou vazio")
        else:
            from PIL import Image

            with Image.open(BytesIO(content)) as image:
                expected = "JPEG" if mime == "image/jpeg" else "PNG"
                if image.format != expected:
                    raise ValueError("Formato divergente")
                image.verify()
    except Exception as exc:
        raise HTTPException(400, "Arquivo inválido, corrompido ou protegido. Substitua-o.") from exc


def verified_path(document):
    root = Path(settings.upload_dir).resolve()
    path = Path(document.storage_path).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, "Certificado não encontrado.")
    if hashlib.sha256(path.read_bytes()).hexdigest() != document.sha256:
        raise HTTPException(409, "A integridade do certificado não pôde ser confirmada.")
    return path
