import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.modules.ingestion.regex_py import extract_entities, iva_credito
from app.modules.validador.timbrado import validar_formato_local
from app.modules.validador.topes import chequear_topes
from app.modules.rg90.generator import to_txt, RG90Row

def test_regex_basico():
    t = "RUC: 80012345-1 TIMBRADO NRO 1234567890 Factura 001-002-0001234 Fecha 15/03/2026 Gravadas 10% 1.100.000 Total 1.100.000"
    e = extract_entities(t)
    assert e["ruc_emisor"] == "80012345" and e["dv"] == "1"
    assert e["timbrado"] == "1234567890"
    assert e["nro_comprobante"] == "001-002-0001234"
    assert e["fecha"] == "15/03/2026"

def test_iva():
    assert iva_credito(1100000, 210000) == (100000.0, 10000.0)

def test_formato():
    assert validar_formato_local("80012345", "1234567890", "001-002-0001234")[0]
    assert not validar_formato_local("ABC", "12", "1")[0]

def test_topes():
    a = chequear_topes({"ESPARCIMIENTO": 19_000_000}, "ESPARCIMIENTO", 2_000_000)
    assert a, "debe alertar tope superado"

def test_rg90():
    txt = to_txt([RG90Row("80012345", "TEST", "1234567890", "001-002-0001234", "15/03/2026", 1100000, 0, 0, 1100000)])
    assert "\t" in txt and "001-002-0001234" in txt

def test_calidad():
    from app.modules.ingestion.calidad import UMBRAL_NITIDEZ, evaluar_imagen
    assert UMBRAL_NITIDEZ > 0
    try:
        evaluar_imagen("no_existe.jpg")
        assert False, "debió fallar con imagen inexistente"
    except ValueError as e:
        assert "No se pudo leer" in str(e)
    except ImportError:
        pass  # cv2 solo en venv; lógica verificada en servidor

def test_documento():
    from app.modules.ingestion.documento import es_comprobante, MENSAJE_NO_VALIDO
    factura = "FACTURA RUC: 80012345-1 TIMBRADO 1234567890 001-002-0001234 15/03/2026 Total 1.100.000"
    ent_ok = {"ruc_emisor": "80012345", "timbrado": "1234567890",
              "nro_comprobante": "001-002-0001234", "fecha": "15/03/2026",
              "grav10": 1100000.0, "grav5": 0.0, "exenta": 0.0, "total": 1100000.0}
    assert es_comprobante(factura, ent_ok)["es_valido"]
    foto_otra = "paisaje montañas vacaciones playa 2026"
    ent_vacia = {"ruc_emisor": "", "timbrado": "", "nro_comprobante": "",
                 "fecha": "", "grav10": 0.0, "grav5": 0.0, "exenta": 0.0, "total": 0.0}
    r = es_comprobante(foto_otra, ent_vacia)
    assert not r["es_valido"] and r["mensaje"].startswith(MENSAJE_NO_VALIDO)

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)
    print("ALL OK")
