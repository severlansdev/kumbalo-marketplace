import os
import json
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
from ..models import Tramite

class ContractPDF(FPDF):
    def header(self):
        # Fondo decorativo lateral sutil
        self.set_fill_color(250, 250, 250)
        self.rect(0, 0, 10, 300, 'F')
        
        # Logo de Kumbalo
        self.set_xy(15, 10)
        self.set_font('helvetica', 'B', 24)
        self.set_text_color(255, 40, 0) # Rojo Kumbalo
        self.cell(40, 10, 'KUMBALO', 0, 0, 'L')
        
        self.set_xy(15, 18)
        self.set_font('helvetica', 'B', 7)
        self.set_text_color(150, 150, 150)
        self.cell(40, 5, 'MARKETPLACE PREMIUM VERIFICADO', 0, 1, 'L')
        
        # Sello de Traspaso Express
        self.set_xy(140, 10)
        self.set_fill_color(255, 40, 0)
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 9)
        self.cell(55, 8, 'SERVICIO: TRASPASO EXPRESS', 0, 1, 'C', True)
        self.ln(15)

    def footer(self):
        self.set_y(-20)
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(180, 180, 180)
        self.cell(0, 5, 'Este documento tiene validez legal en el territorio colombiano bajo la Ley 527 de 1999 sobre comercio electrónico.', 0, 1, 'C')
        self.cell(0, 5, f'Página {self.page_no()} | Kumbalo Technologies SAS - NIT: 901.XXX.XXX-X', 0, 0, 'C')

def generate_purchase_contract(tramite: Tramite) -> BytesIO:
    """
    Genera un contrato de compraventa legal premium para Colombia.
    """
    vendedor = tramite.vendedor
    comprador = tramite.comprador
    moto = tramite.moto
    ahora = datetime.now()
    
    # Formateo de precios y fechas
    precio_num = moto.precio
    precio_str = "{:,.0f}".format(precio_num).replace(",", ".")
    
    pdf = ContractPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    
    # Título Principal con Estilo
    pdf.set_y(40)
    pdf.set_font('helvetica', 'B', 18)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 12, 'CONTRATO DE COMPRAVENTA VEHICULAR', 0, 1, 'C')
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'RADICADO ÚNICO: KMB-{tramite.id:05}-{ahora.year}', 0, 1, 'C')
    pdf.ln(10)

    # Cuerpo del Contrato
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)
    
    texto_intro = (
        f"En la ciudad de {moto.ciudad or 'Bogotá'}, a los {ahora.day} días del mes de {ahora.strftime('%B')} de {ahora.year}, "
        f"se celebra el presente contrato entre {vendedor.nombre.upper()}, identificado con C.C. {vendedor.cedula or '________'}, "
        f"quien para efectos de este contrato se denominará EL VENDEDOR, y {comprador.nombre.upper()}, "
        f"identificado con C.C. {comprador.cedula or '________'}, quien se denominará EL COMPRADOR."
    )
    pdf.multi_cell(0, 5, texto_intro, align='J')
    pdf.ln(8)

    # Cláusula 1: Objeto
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, '1. OBJETO DEL CONTRATO', 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, f"EL VENDEDOR transfiere a título de compraventa la propiedad de la motocicleta con las siguientes características técnicas:")
    pdf.ln(3)

    # Tabla de Moto con Diseño Limpio
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(230, 230, 230)
    
    specs = [
        ("MARCA", moto.marca),
        ("LÍNEA/MODELO", f"{moto.modelo} / {moto.año}"),
        ("PLACA", (moto.placa or "SIN PLACA").upper()),
        ("N° MOTOR", (moto.nro_motor or "PENDIENTE VERIFICACIÓN").upper()),
        ("N° CHASIS", (moto.nro_chasis or "PENDIENTE VERIFICACIÓN").upper()),
        ("CILINDRAJE", f"{moto.cilindraje} cc"),
        ("COLOR", (moto.color or "SIN ESPECIFICAR").upper())
    ]

    for label, val in specs:
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(50, 8, f"  {label}", 1, 0, 'L', True)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(0, 8, f"  {val}", 1, 1, 'L')
    
    pdf.ln(8)

    # Cláusula 2: Precio
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, '2. PRECIO Y FORMA DE PAGO', 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, f"El precio acordado es de ${precio_str} PESOS M/CTE, los cuales serán pagados por EL COMPRADOR conforme a los términos de seguridad de la plataforma Kumbalo.")
    pdf.ln(5)

    # Cláusula 3: Estado Legal (Garantía Kumbalo)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, '3. ESTADO LEGAL Y TRADICIÓN', 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, "EL VENDEDOR garantiza que el vehículo es de su exclusiva propiedad y se encuentra libre de gravámenes, embargos y multas. EL COMPRADOR acepta el estado del vehículo basado en la revisión de ADN Kumbalo realizada previamente.")
    
    # Firmas
    pdf.ln(25)
    pdf.set_font('helvetica', 'B', 10)
    
    # Líneas de firma
    x_offset = 20
    line_w = 70
    
    # Vendedor
    pdf.line(x_offset, pdf.get_y(), x_offset + line_w, pdf.get_y())
    pdf.set_xy(x_offset, pdf.get_y() + 2)
    pdf.cell(line_w, 5, 'EL VENDEDOR', 0, 1, 'C')
    pdf.set_font('helvetica', '', 9)
    pdf.set_x(x_offset)
    pdf.cell(line_w, 4, vendedor.nombre, 0, 1, 'C')
    
    # Comprador (posicionamiento absoluto para que queden al lado)
    y_signatures = pdf.get_y() - 11
    pdf.line(110, y_signatures, 110 + line_w, y_signatures)
    pdf.set_xy(110, y_signatures + 2)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(line_w, 5, 'EL COMPRADOR', 0, 1, 'C')
    pdf.set_font('helvetica', '', 9)
    pdf.set_x(110)
    pdf.cell(line_w, 4, comprador.nombre, 0, 1, 'C')

    # Guardado en buffer
    pdf_buffer = BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin-1')
    pdf_buffer.write(pdf_output)
    pdf_buffer.seek(0)
    return pdf_buffer
