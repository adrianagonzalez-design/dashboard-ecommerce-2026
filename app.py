import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE LA MARCA Y GOOGLE SHEET
# ==========================================
NOMBRE_MARCA = "Bath & Body Works"  # Cambiar a "Victoria's Secret" en el otro dashboard
SHEET_ID = "1DlGk2a1Olk7hlOwntiKNOc3W9xlQDCKtz7khS7j0dX0"

st.set_page_config(page_title=f"Seguimiento Operativo - {NOMBRE_MARCA}", page_icon="📊", layout="wide")

def leer_hoja(nombre_hoja):
    nombre_url = nombre_hoja.replace(" ", "%20")
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_url}"
    df = pd.read_csv(url)
    df.columns = df.columns.astype(str).str.strip()
    return df

def limpiar_numero(serie):
    return pd.to_numeric(
        serie.astype(str).str.replace(r"[\$,\s]", "", regex=True),
        errors="coerce"
    ).fillna(0.0)

MAPA_PAISES = {
    "PANAMA": "PAN", "GUATEMALA": "GTM", "COLOMBIA": "COL", "PERU": "PER",
    "COSTA RICA": "CRI", "PARAGUAY": "PRY", "ECUADOR": "ECU",
    "ARGENTINA": "ARG", "EL SALVADOR": "SLV", "URUGUAY": "URY"
}

SLAS_DEFAULT = [
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "PAN", 6, ""),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "GTM", 7, ""),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "COL", 7, ""),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "PER", 7, ""),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "CRI", 7, "Problemas con la pasarela"),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "PRY", 5, ""),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "ECU", 7, ""),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "ARG", 8, ""),
    ("Mist Event Ago 2026", "2026-08-26", "2026-08-30", "SLV", 7, "Problemas con el pago"),
]

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos():
    # Lee hoja principal de VTEX (BBW o VSBA o VTEX_RAW)
    df_vtex = pd.DataFrame()
    for hoja in ["BBW", "VSBA", "VTEX_RAW"]:
        try:
            df_vtex = leer_hoja(hoja)
            if not df_vtex.empty:
                break
        except Exception:
            continue

    # Lee hoja principal de ICG (ICG REPORT BBW o TV TF o ICG_RAW)
    df_icg = pd.DataFrame()
    for hoja in ["ICG REPORT BBW", "TV TF", "ICG_RAW"]:
        try:
            df_icg = leer_hoja(hoja)
            if not df_icg.empty:
                break
        except Exception:
            continue

    cols_sla = ["Evento", "Inicio", "Fin", "País", "Promesa_Dias", "Comentario"]
    df_slas_def = pd.DataFrame(SLAS_DEFAULT, columns=cols_sla)

    try:
        df_slas = leer_hoja("EVENTOS_SLAS")
        if df_slas.empty or not set(["Evento", "Inicio", "Fin", "País"]).issubset(df_slas.columns):
            df_slas = df_slas_def
    except Exception:
        df_slas = df_slas_def

    try:
        df_ctrl = leer_hoja("CONTROL_UPDATE")
        last_upd = str(df_ctrl.iloc[0, 0]) if not df_ctrl.empty else datetime.now().strftime("%d/%m/%Y %I:%M %p")
    except Exception:
        last_upd = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    return df_vtex, df_icg, df_slas, last_upd

try:
    df_vtex, df_icg, df_slas, last_upd = cargar_datos()
except Exception:
    st.error("⚠️ Error conectando con Google Sheets. Verifica el SHEET_ID y los permisos de lectura.")
    st.stop()

# ==========================================
# 3. ENCABEZADO Y 2 FILTROS LIMPIOS
# ==========================================
col_t, col_b = st.columns([4, 1])
with col_t:
    st.title(f"📊 Seguimiento Operativo — {NOMBRE_MARCA}")
    st.markdown(f"🕒 **Última actualización:** `{last_upd}`")
with col_b:
    st.write("")
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

f1, f2 = st.columns(2)
with f1:
    eventos_disp = df_slas["Evento"].dropna().unique().tolist()
    evento_sel = st.selectbox("1️⃣ Seleccionar Evento 2026:", eventos_disp)

cfg_evt = df_slas[df_slas["Evento"] == evento_sel].copy()
f_ini = pd.to_datetime(cfg_evt["Inicio"].iloc[0])
f_fin = pd.to_datetime(cfg_evt["Fin"].iloc[0])

# ==========================================
# 4. PROCESAMIENTO DE DATOS
# ==========================================
# VTEX
d_v = df_vtex.copy()
d_v["Fecha"] = pd.to_datetime(d_v["CreationDate"], errors="coerce").dt.normalize()
if "StatusRawValue" in d_v.columns:
    d_v = d_v[~d_v["StatusRawValue"].astype(str).str.lower().isin(["canceled", "cancelled", "payment-pending"])]
d_v = d_v[(d_v["Fecha"] >= f_ini) & (d_v["Fecha"] <= f_fin)].copy()
d_v["QuantitySKU"] = limpiar_numero(d_v["QuantitySKU"])
d_v["TOTAL SKU PRICE (Dollar)"] = limpiar_numero(d_v["TOTAL SKU PRICE (Dollar)"])
d_v["País"] = d_v["Country"].astype(str).str.strip()

vtex_res = d_v.groupby("País", as_index=False).agg(
    Orders=("Order", "nunique"),
    QTY=("QuantitySKU", "sum"),
    SALES=("TOTAL SKU PRICE (Dollar)", "sum")
)

# ICG (soporta formato ICG REPORT BBW y TV TF)
d_i = df_icg.copy()
if "Fecha" in d_i.columns:
    d_i["Fecha_dt"] = pd.to_datetime(d_i["Fecha"], errors="coerce").dt.normalize()
    d_i = d_i[d_i["TIENDA"].astype(str).str.contains("E-COMMERCE", case=False, na=False)]
    d_i = d_i[d_i["Fecha_dt"] >= f_ini].copy()
    d_i["País"] = d_i["País"].astype(str).str.upper().str.strip().map(MAPA_PAISES).fillna(d_i["País"])
    d_i["ORDER ICG"] = limpiar_numero(d_i["TRANSACCIONES"])
    d_i["SALES ICG"] = limpiar_numero(d_i["VENTAS_DTO"])
else:
    d_i["Fecha_dt"] = pd.to_datetime(d_i["DATE"], errors="coerce").dt.normalize()
    d_i = d_i[d_i["TYPE"].astype(str).str.upper() == "ECOMMERCE"]
    d_i = d_i[d_i["Fecha_dt"] >= f_ini].copy()
    d_i["País"] = d_i["COUNTRY"].astype(str).str.upper().str.strip().map(MAPA_PAISES).fillna(d_i["COUNTRY"])
    d_i["ORDER ICG"] = limpiar_numero(d_i["TRANS"])
    d_i["SALES ICG"] = limpiar_numero(d_i["NET USD"])

icg_res = d_i.groupby("País", as_index=False).agg(
    **{"SALES ICG": ("SALES ICG", "sum"), "ORDER ICG": ("ORDER ICG", "sum")}
)

# Cruce y SLAs
df_calc = pd.merge(vtex_res, icg_res, on="País", how="outer")
for col in ["Orders", "QTY", "SALES", "SALES ICG", "ORDER ICG"]:
    df_calc[col] = pd.to_numeric(df_calc[col], errors="coerce").fillna(0.0)

slas_pais = cfg_evt[["País", "Promesa_Dias", "Comentario"]].drop_duplicates(subset=["País"])
df_calc = pd.merge(df_calc, slas_pais, on="País", how="left")
df_calc["PROMESA DE ENTREGA"] = pd.to_numeric(df_calc["Promesa_Dias"], errors="coerce").fillna(7).astype(int)
df_calc["Comentarios"] = df_calc["Comentario"].fillna("")

df_calc["AVANCE FACTURACIÓN"] = np.where(df_calc["SALES"] > 0, (df_calc["SALES ICG"] / df_calc["SALES"]) * 100, 0.0)
df_calc["PEDIDOS PENDIENTES"] = df_calc["Orders"] - df_calc["ORDER ICG"]
df_calc["GAP"] = df_calc["SALES ICG"] - df_calc["SALES"]
df_calc["META MINIMA"] = np.ceil(df_calc["Orders"] / df_calc["PROMESA DE ENTREGA"])
df_calc["DIAS HOMBRE"] = np.where(df_calc["META MINIMA"] > 0, np.round(df_calc["PEDIDOS PENDIENTES"] / df_calc["META MINIMA"], 0), 0)

# Filtro 2: País (Default: Todos los países)
with f2:
    paises_opciones = ["🌎 Todos los Países (Overview)"] + sorted(df_calc["País"].astype(str).unique().tolist())
    pais_sel = st.selectbox("2️⃣ Filtrar País:", paises_opciones)

df_vista = df_calc if "Todos" in pais_sel else df_calc[df_calc["País"] == pais_sel]

# ==========================================
# 5. TARJETAS RESUMEN Y TABLA CON BLOQUES DE COLOR
# ==========================================
st.caption(f"📅 **Ventana del Evento:** `{f_ini.strftime('%Y-%m-%d')}` al `{f_fin.strftime('%Y-%m-%d')}`")

k1, k2, k3, k4 = st.columns(4)
tot_ord = df_vista["Orders"].sum()
tot_icg_ord = df_vista["ORDER ICG"].sum()
tot_sales = df_vista["SALES"].sum()
tot_icg_sales = df_vista["SALES ICG"].sum()
tot_pend = df_vista["PEDIDOS PENDIENTES"].sum()
tot_avance = (tot_icg_sales / tot_sales * 100) if tot_sales > 0 else 0.0

k1.metric("Orders Entrantes", f"{tot_ord:,.0f}")
k2.metric("Orders Facturadas (ICG)", f"{tot_icg_ord:,.0f}")
k3.metric("Pedidos Pendientes", f"{tot_pend:,.0f}")
k4.metric("Avance Facturación ($)", f"{tot_avance:.0f}%")

# Agregar fila de Total General si se están viendo todos los países
cols_tabla = [
    "País", "Orders", "QTY", "SALES", "SALES ICG", "ORDER ICG",
    "AVANCE FACTURACIÓN", "PEDIDOS PENDIENTES", "GAP",
    "PROMESA DE ENTREGA", "META MINIMA", "DIAS HOMBRE", "Comentarios"
]

df_mostrar = df_vista[cols_tabla].copy()
if "Todos" in pais_sel and len(df_mostrar) > 1:
    fila_total = pd.DataFrame([{
        "País": "Total general",
        "Orders": df_mostrar["Orders"].sum(),
        "QTY": df_mostrar["QTY"].sum(),
        "SALES": df_mostrar["SALES"].sum(),
        "SALES ICG": df_mostrar["SALES ICG"].sum(),
        "ORDER ICG": df_mostrar["ORDER ICG"].sum(),
        "AVANCE FACTURACIÓN": (df_mostrar["SALES ICG"].sum() / df_mostrar["SALES"].sum() * 100) if df_mostrar["SALES"].sum() > 0 else 0.0,
        "PEDIDOS PENDIENTES": df_mostrar["PEDIDOS PENDIENTES"].sum(),
        "GAP": df_mostrar["GAP"].sum(),
        "PROMESA DE ENTREGA": np.nan,
        "META MINIMA": np.nan,
        "DIAS HOMBRE": np.nan,
        "Comentarios": ""
    }])
    df_mostrar = pd.concat([df_mostrar, fila_total], ignore_index=True)

# Formatos visuales idénticos a tu Excel (negativos en paréntesis y colores por columna)
def fmt_pendientes(val):
    if pd.isna(val):
        return ""
    return f"({abs(val):,.0f})" if val < 0 else f"{val:,.0f}"

def fmt_ent_vacio(val):
    return "" if pd.isna(val) else f"{val:,.0f}"

def aplicar_estilos(df):
    styler = df.style.format({
        "Orders": "{:,.0f}",
        "QTY": "{:,.0f}",
        "SALES": "${:,.2f}",
        "SALES ICG": "${:,.2f}",
        "ORDER ICG": "{:,.0f}",
        "AVANCE FACTURACIÓN": "{:.0f}%",
        "PEDIDOS PENDIENTES": fmt_pendientes,
        "GAP": "${:,.2f}",
        "PROMESA DE ENTREGA": fmt_ent_vacio,
        "META MINIMA": fmt_ent_vacio,
        "DIAS HOMBRE": fmt_ent_vacio,
    })

    # Colores de fondo por bloque de columnas (igual a tu Excel)
    styler = styler.set_properties(subset=["SALES"], **{"background-color": "#9BC2E6", "color": "#000000", "font-weight": "bold"})
    styler = styler.set_properties(subset=["SALES ICG"], **{"background-color": "#D9E1F2", "color": "#000000"})
    styler = styler.set_properties(subset=["ORDER ICG"], **{"background-color": "#5B9BD5", "color": "#000000", "font-weight": "bold"})
    styler = styler.set_properties(subset=["AVANCE FACTURACIÓN"], **{"font-weight": "bold"})

    # Texto rojo para pedidos pendientes negativos
    def color_negativo(val):
        if isinstance(val, (int, float)) and val < 0:
            return "color: #C00000; font-weight: bold;"
        return ""

    styler = styler.map(color_negativo, subset=["PEDIDOS PENDIENTES"])

    # Resaltar fila Total general
    def resaltar_total(row):
        if row["País"] == "Total general":
            return ["background-color: #D9D9D9; font-weight: bold; border-top: 2px solid #1B365D;"] * len(row)
        return [""] * len(row)

    styler = styler.apply(resaltar_total, axis=1)
    return styler

st.subheader("📋 Cuadro de Seguimiento Operativo")
alto_tabla = (len(df_mostrar) + 1) * 38 + 10
st.dataframe(
    aplicar_estilos(df_mostrar),
    use_container_width=True,
    hide_index=True,
    height=alto_tabla
)
