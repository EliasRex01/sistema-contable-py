"""Pipeline: PDF nativo (PyMuPDF) -> OpenCV preproceso -> Tesseract."""
import fitz  # PyMuPDF
import cv2
import numpy as np

def pdf_text_native(path: str) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)

def preprocess_voucher(img_path: str) -> np.ndarray:
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(img_path)
    # resize si muy chico + CLAHE + threshold adaptativo
    h = img.shape[0]
    if h < 1200:
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 31, 10)
    return img

def ocr_image(img) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(img, lang="spa")
    except Exception as e:
        return f"[OCR no disponible: {e}]"
