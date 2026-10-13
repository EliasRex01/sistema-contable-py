"""Control de calidad de imagen antes del OCR.

Si la foto es borrosa, oscura o muy chica, el OCR falla; en ese caso se
devuelve el mensaje "la imagen no está muy clara" y se pide retomar la foto
en vez de procesar datos poco fiables.
"""
UMBRAL_NITIDEZ = 100.0      # varianza del Laplaciano (menor = más borrosa)
LADO_MINIMO_PX = 800
BRILLO_MIN, BRILLO_MAX = 40.0, 245.0  # papel blanco ≈200-235; >245 = sobreexpuesta

def evaluar_imagen(path: str) -> dict:
    import cv2
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"No se pudo leer la imagen: {path}")
    h, w = img.shape
    nitidez = float(cv2.Laplacian(img, cv2.CV_64F).var())
    brillo = float(img.mean())
    mensajes: list[str] = []
    if min(h, w) < LADO_MINIMO_PX:
        mensajes.append(f"Imagen muy chica ({w}x{h}); usa mayor resolución.")
    if nitidez < UMBRAL_NITIDEZ:
        mensajes.append("La imagen no está muy clara (borrosa o movida); "
                        "toma la foto de nuevo con buen enfoque y luz.")
    if brillo < BRILLO_MIN:
        mensajes.append("Imagen muy oscura; mejora la iluminación.")
    elif brillo > BRILLO_MAX:
        mensajes.append("Imagen sobreexpuesta (muy clara); evita el flash directo.")
    return {"nitida": not mensajes, "nitidez": round(nitidez, 1),
            "brillo": round(brillo, 1), "ancho": w, "alto": h,
            "mensajes": mensajes}
