import streamlit as st
import pandas as pd
import math
from datetime import date
import os

st.set_page_config(page_title="Rubiq Arts - ERP & Cotizador", layout="wide")

# Escudo indestructible para cargar el logo
if os.path.exists("logo.png"):
    st.image("logo.png", width=250)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=250)
else:
    st.title("Rubiq Arts 🎨 | Sistema de Costos y Cotizaciones")
    st.caption("(Sube tu archivo 'logo.png' o 'logo.jpg' a la carpeta para verlo aquí)")

# --- BASES DE DATOS INTERNAS ---
PRENDAS = {
    "Tote Bag Canvas Básica": 2.50,
    "Playera Gildan 5000 (Algodón)": 3.15,
    "Playera Sport-Tek (Poliéster)": 4.50,
    "Playera Bella+Canvas 3001 (Premium)": 5.20,
    "Hoodie Mezcla Pesada (Gildan 18500)": 13.50,
}

PROVEEDORES_DTF = {
    "Gang Sheet Local Houston ($12/pliego 24x22)": {"ancho_max": 22, "costo_pulgada": 0.50},
    "Ninja Transfers ($19.99 + Tax/Envío)": {"ancho_max": 22, "costo_pulgada": 1.10}, 
}

PROVEEDORES_VINIL = {
    "Rollo HTVRONT 12\"x5ft": {"precio": 11.00, "ancho_util": 11.5, "largo_util": 60.0},
    "Siser EasyWeed (Yarda 15\"x36\")": {"precio": 14.00, "ancho_util": 14.5, "largo_util": 36.0},
}

TARIFA_HORA = 20.00
COSTO_PLANCHA_UNIDAD = 0.50

# --- BARRA LATERAL ---
st.sidebar.header("1. Configuración del Producto")
opcion_prenda = st.sidebar.selectbox("Selecciona el Blank:", list(PRENDAS.keys()) + ["Otro (Ingreso Manual)"])

if opcion_prenda == "Otro (Ingreso Manual)":
    nombre_prenda_final = st.sidebar.text_input("Nombre del blank:", value="Prenda Personalizada")
    costo_blank = st.sidebar.number_input("Costo unitario del blank ($):", min_value=0.0, value=5.00, step=0.50)
else:
    costo_blank = PRENDAS[opcion_prenda]
    nombre_prenda_final = opcion_prenda

cantidad = st.sidebar.number_input("Cantidad a producir:", min_value=1, value=20)

st.sidebar.header("2. Gastos Extra")
costo_empaque = st.sidebar.number_input("Empaque por unidad ($):", min_value=0.0, value=0.35, step=0.05)
cobro_tarjeta = st.sidebar.checkbox("Incluir comisión de tarjeta (2.9% + $0.30)")

st.sidebar.header("3. Rentabilidad")
margen_ganancia = st.sidebar.slider("Margen Deseado (%):", min_value=10, max_value=100, value=60, step=5)

def calcular_precio_final(costo_produccion):
    precio_base = costo_produccion / (1 - (margen_ganancia/100))
    if cobro_tarjeta:
        return (precio_base + 0.30) / (1 - 0.029)
    return precio_base

tab1, tab2, tab3 = st.tabs(["🔥 Impresión DTF", "✂️ Corte de Vinil", "📄 Generar Cotización"])

# ==================== PESTAÑA 1: DTF ====================
with tab1:
    st.header("Flujo de Trabajo: DTF")
    col1, col2 = st.columns([1, 1.5]) 
    
    with col1:
        opcion_proveedor_dtf = st.selectbox("Proveedor DTF:", list(PROVEEDORES_DTF.keys()) + ["Otro (Manual)"])
        if opcion_proveedor_dtf == "Otro (Manual)":
            ancho_max_final = st.number_input("Ancho del rollo (in):", value=22.0)
            costo_pliego = st.number_input("Costo del pliego ($):", value=15.00)
            largo_pliego = st.number_input("Largo del pliego (in):", value=39.3)
            costo_por_pulgada = costo_pliego / largo_pliego if largo_pliego > 0 else 0
        else:
            costo_por_pulgada = PROVEEDORES_DTF[opcion_proveedor_dtf]["costo_pulgada"]
            ancho_max_final = PROVEEDORES_DTF[opcion_proveedor_dtf]["ancho_max"]

    with col2:
        st.write("Ubicaciones (Agrega filas según los logos):")
        df_artes = st.data_editor(pd.DataFrame({"Ubicación": ["Frente"], "Ancho (in)": [7.0], "Alto (in)": [11.0]}), num_rows="dynamic", use_container_width=True)

    if st.button("Ejecutar Análisis DTF", type="primary"):
        largo_lineal = 0
        tiempo_plancha = 0
        for index, row in df_artes.iterrows():
            try:
                w = float(row["Ancho (in)"])
                h = float(row["Alto (in)"])
            except:
                w, h = 0.0, 0.0
            if w > 0 and h > 0:
                caben = math.floor(ancho_max_final / w) if w <= ancho_max_final else 1
                largo_lineal += h / caben
                tiempo_plancha += 2 

        costo_dtf = ((largo_lineal * cantidad) * costo_por_pulgada) / cantidad if cantidad > 0 else 0
        costo_mo = ((5 + tiempo_plancha) / 60) * TARIFA_HORA
        total = costo_blank + costo_dtf + costo_mo + COSTO_PLANCHA_UNIDAD + costo_empaque
        precio = calcular_precio_final(total)
        
        st.session_state['cot'] = {'fecha': date.today().strftime("%d/%m/%Y"), 'prod': nombre_prenda_final, 'cant': cantidad, 'tec': "DTF", 'pu': precio, 'pt': precio * cantidad}
        
        cA, cB, cC = st.columns(3)
        cA.metric("Costo Real (c/u)", f"${total:.2f}")
        cB.metric(f"Precio Venta", f"${precio:.2f}")
        cC.metric("Ganancia Neta", f"${(precio - total) * cantidad:.2f}")

# ==================== PESTAÑA 2: VINIL (Nesting Automático) ====================
with tab2:
    st.header("Flujo de Trabajo: Vinil Textil")
    col3, col4 = st.columns(2)
    
    with col3:
        tipo_vinil = st.selectbox("Material:", list(PROVEEDORES_VINIL.keys()) + ["Otro (Manual)"])
        if tipo_vinil == "Otro (Manual)":
            costo_rollo = st.number_input("Costo del rollo ($):", value=15.00)
            ancho_util = st.number_input("Ancho útil (in):", value=11.5)
            largo_util = st.number_input("Largo útil (in):", value=60.0)
        else:
            costo_rollo = PROVEEDORES_VINIL[tipo_vinil]["precio"]
            ancho_util = PROVEEDORES_VINIL[tipo_vinil]["ancho_util"]
            largo_util = PROVEEDORES_VINIL[tipo_vinil]["largo_util"]

        st.subheader("Medidas del Diseño Principal")
        ancho_diseno = st.number_input("Ancho del diseño (in):", value=10.0, step=0.5)
        alto_diseno = st.number_input("Alto del diseño (in):", value=10.0, step=0.5)

    with col4:
        st.subheader("Complejidad")
        minutos_depilado = st.slider("Minutos de depilado (por unidad):", min_value=2, max_value=45, value=15)
        
    if st.button("Ejecutar Análisis Vinil", type="primary"):
        # Lógica de Nesting Automático
        if ancho_diseno > 0 and alto_diseno > 0:
            caben_ancho = math.floor(ancho_util / ancho_diseno)
            caben_largo = math.floor(largo_util / alto_diseno)
            piezas_por_rollo = caben_ancho * caben_largo
        else:
            piezas_por_rollo = 1
            
        if piezas_por_rollo <= 0:
            st.error("El diseño es más grande que el rollo seleccionado.")
        else:
            rollos_necesarios = math.ceil(cantidad / piezas_por_rollo)
            st.info(f"💡 El sistema calcula que salen **{piezas_por_rollo} piezas por rollo**. Necesitarás comprar/usar **{rollos_necesarios} rollo(s)** para este proyecto.")
            
            costo_vinil_unidad = costo_rollo / piezas_por_rollo
            costo_mo = ((minutos_depilado + 3) / 60) * TARIFA_HORA
            total = costo_blank + costo_vinil_unidad + costo_mo + COSTO_PLANCHA_UNIDAD + costo_empaque
            precio = calcular_precio_final(total)
            
            st.session_state['cot'] = {'fecha': date.today().strftime("%d/%m/%Y"), 'prod': nombre_prenda_final, 'cant': cantidad, 'tec': "Corte de Vinil", 'pu': precio, 'pt': precio * cantidad}

            cD, cE, cF = st.columns(3)
            cD.metric("Costo Real (c/u)", f"${total:.2f}")
            cE.metric(f"Precio Venta", f"${precio:.2f}")
            cF.metric("Ganancia Neta", f"${(precio - total) * cantidad:.2f}")

# ==================== PESTAÑA 3: COTIZACIÓN ====================
with tab3:
    st.header("📄 Generador de Presupuesto")
    colC1, colC2 = st.columns(2)
    with colC1:
        empresa = st.text_input("Cliente/Empresa:", placeholder="Ej. Eternal Beauty")
    with colC2:
        contacto = st.text_input("Atención a:", placeholder="Ej. María")
        
    if 'cot' in st.session_state:
        d = st.session_state['cot']
        nom = empresa if empresa else "A quien corresponda"
        atn = f"\nAtención: {contacto}" if contacto else ""
        
        texto = f"""=========================================
           PRESUPUESTO - RUBIQ ARTS
=========================================
Fecha: {d['fecha']}
Cliente: {nom} {atn}

Detalles del Pedido:
-----------------------------------------
- Producto: {d['prod']}
- Técnica:  {d['tec']}
- Cantidad: {d['cant']} unidades

Inversión:
-----------------------------------------
- Precio Unitario:  ${d['pu']:.2f} USD
- TOTAL PROYECTO:   ${d['pt']:.2f} USD

* Condiciones: 50% anticipo. Válido por 15 días.
========================================="""
        st.text_area("Vista previa:", value=texto, height=350)
        st.download_button("📥 Descargar Cotización", data=texto, file_name=f"Cotizacion_RubiqArts.txt", mime="text/plain")
