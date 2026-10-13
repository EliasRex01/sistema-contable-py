from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Cliente(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ruc: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    dv: Mapped[str] = mapped_column(String(2))
    razon_social: Mapped[str] = mapped_column(String(255))
    obligaciones: Mapped[str] = mapped_column(String(50), default="211,715")  # 211 IVA, 715 IRP
    dnit_user: Mapped[str] = mapped_column(String(50))
    dnit_pass_enc: Mapped[str] = mapped_column(Text)  # AES-256
    familiares: Mapped[str] = mapped_column(Text, default="[]")  # JSON lista cedulas/RUC

class ProveedorRubro(Base):
    __tablename__ = "proveedores_rubro"
    ruc: Mapped[str] = mapped_column(String(20), primary_key=True)
    razon_social: Mapped[str] = mapped_column(String(255), default="")
    rubro: Mapped[str] = mapped_column(String(100))  # ej. SUPERMERCADO, SALUD
    deducible_irp: Mapped[bool] = mapped_column(Boolean, default=True)

class Comprobante(Base):
    __tablename__ = "comprobantes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    ruc_emisor: Mapped[str] = mapped_column(String(20), index=True)
    razon_emisor: Mapped[str] = mapped_column(String(255), default="")
    timbrado: Mapped[str] = mapped_column(String(20), index=True)
    nro_comprobante: Mapped[str] = mapped_column(String(20))  # 000-000-0000000
    fecha: Mapped[str] = mapped_column(String(10))  # DD/MM/YYYY -> ISO en validación
    grav10: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    grav5: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    exenta: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    tipo: Mapped[str] = mapped_column(String(20), default="COMPRA")
    rubro: Mapped[str] = mapped_column(String(100), default="")
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE")  # PENDIENTE/VALIDADO/RECHAZADO
    fuente: Mapped[str] = mapped_column(String(10), default="OCR")  # OCR/XML/PDF
    imagen_path: Mapped[str] = mapped_column(Text, default="")
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

class LoteRG90(Base):
    __tablename__ = "lotes_rg90"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    periodo: Mapped[str] = mapped_column(String(7))  # YYYY-MM
    archivo_txt: Mapped[str] = mapped_column(Text)
    nro_lote_dnit: Mapped[str] = mapped_column(String(50), default="")
    estado: Mapped[str] = mapped_column(String(20), default="GENERADO")
