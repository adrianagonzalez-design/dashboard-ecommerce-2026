import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE LA MARCA Y GOOGLE SHEET
# ==========================================
NOMBRE_MARCA = "Bath & Body Works"
SHEET_ID = "1DlGk2a1Olk7hlOwntiKNOc3W9xlQDCKtz7khS7j0dX0"

st.set_page_config(page_title=f"Seguimiento Operativo - {NOMBRE_MARCA}", page_icon="🫧", layout="wide")

# Estilo visual inspirado en Bath & Body Works (Azul Gingham + Rosa Suave)
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    h1 { color: #1B365D !important; font-weight: 800 !important; }
    h2, h3 { color: #005696 !important; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #D6E4F0;
        border-left: 5px solid #005696;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0, 86, 150, 0.06);
    }
    div[data-testid="stMetricLabel"] { color: #4A5568 !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] { color: #1B365D !important; }
    </style>
""", unsafe_allow_html=True)

def leer_hoja(nombre_hoja, col_clave=None):
    nombre_url = nombre_hoja.replace(" ", "%20")
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_url}"
    df = pd.read_csv(url)
    df.columns = df.columns.astype(str).str.strip()
    if col_clave and col_clave not in df.columns:
        for i in range(min(15, len(df))):
            fila_vals = [str(v).strip() for v in df.iloc[i].values]
            if col_clave in fila_vals:
                df.columns = fila_vals
                df = df.iloc[i + 1:].reset_index(drop=True)
                break
    return df

def limpiar_numero(serie):
    def parse_val(v):
        if pd.isna(v):
            return 0.0
        s = re.sub(r"[\$\s]", "", str(v)).strip()
        if not s or s.lower() in ["nan", "none", "#num!", "#div/0!", "-"]:
            return 0.0
        # Si tiene coma y punto (ej. 1.234,56 o 1,234.56)
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            # Si hay una sola coma con 1 o 2 decimales al final (ej. 79844,43) -> decimal
            partes = s.split(",")
            if len(partes) == 2 and len(partes[1]) <= 2:
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        try:
            return float(s)
        except Exception:
            return 0.0
    return serie.apply(parse_val)

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
    df_vtex = pd.DataFrame()
    for hoja in ["BBW", "VSBA", "VTEX_RAW"]:
        try:
            temp = leer_hoja(hoja, col_clave="CreationDate")
            if "CreationDate" in temp.columns and len(temp) > 0:
                df_vtex = temp
                break
        except Exception:
            continue

    df_icg = pd.DataFrame()
    for hoja in ["ICG REPORT BBW", "TV TF", "ICG_RAW"]:
        try:
            temp = leer_hoja(hoja, col_clave="TIENDA")
            if ("TIENDA" in temp.columns or "TYPE" in temp.columns) and len(temp) > 0:
                df_icg = temp
                break
        except Exception:
            continue

    cols_sla = ["Evento", "Inicio", "Fin", "País", "Promesa_Dias", "Comentario"]
    df_slas_def = pd.DataFrame(SLAS_DEFAULT, columns=cols_sla)

    try:
        df_slas = leer_hoja("EVENTOS_SLAS", col_clave="Evento")
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

df_vtex, df_icg, df_slas, last_upd = cargar_datos()

if df_vtex.empty:
    st.error("⚠️ No se encontraron datos con la columna 'CreationDate' en la pestaña BBW.")
    st.stop()

# ==========================================
# 3. ENCABEZADO Y 2 FILTROS LIMPIOS
# ==========================================
col_t, col_b = st.columns([4, 1])
with col_t:
    st.title(f"🫧 Seguimiento Operativo — {NOMBRE_MARCA}")
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
# 4. PROCESAMIENTO Y NOMBRES EXACTOS DE COLUMNAS
# ==========================================
d_v = df_vtex.copy()
d_v["Fecha"] = pd.to_datetime(d_v["CreationDate"], errors="coerce").dt.normalize()
if "StatusRawValue" in d_v.columns:
    d_v = d_v[~d_v["StatusRawValue"].astype(str).str.lower().isin(["canceled", "cancelled", "payment-pending"])]
d_v = d_v[(d_v["Fecha"] >= f_ini) & (d_v["Fecha"] <= f_fin)].copy()
d_v["TOTAL SKU PRICE (Dollar)"] = limpiar_numero(d_v["TOTAL SKU PRICE (Dollar)"])
d_v["País"] = d_v["Country"].astype(str).str.strip()

vtex_res = d_v.groupby("País", as_index=False).agg(
    **{
        "Vtex Orders": ("Order", "nunique"),
        "Vtex Sales": ("TOTAL SKU PRICE (Dollar)", "sum")
    }
)

d_i = df_icg.copy()
if not d_i.empty and "Fecha" in d_i.columns:
    d_i["Fecha_dt"] = pd.to_datetime(d_i["Fecha"], errors="coerce").dt.normalize()
    d_i = d_i[d_i["TIENDA"].astype(str).str.contains("E-COMMERCE", case=False, na=False)]
    d_i = d_i[d_i["Fecha_dt"] >= f_ini].copy()
    d_i["País"] = d_i["País"].astype(str).str.upper().str.strip().map(MAPA_PAISES).fillna(d_i["País"])
    d_i["ICG Orders"] = limpiar_numero(d_i["TRANSACCIONES"])
    d_i["Facturado ICG"] = limpiar_numero(d_i["VENTAS_DTO"])
    icg_res = d_i.groupby("País", as_index=False).agg(
        **{"ICG Orders": ("ICG Orders", "sum"), "Facturado ICG": ("Facturado ICG", "sum")}
    )
elif not d_i.empty and "DATE" in d_i.columns:
    d_i["Fecha_dt"] = pd.to_datetime(d_i["DATE"], errors="coerce").dt.normalize()
    d_i = d_i[d_i["TYPE"].astype(str).str.upper() == "ECOMMERCE"]
    d_i = d_i[d_i["Fecha_dt"] >= f_ini].copy()
    d_i["País"] = d_i["COUNTRY"].astype(str).str.upper().str.strip().map(MAPA_PAISES).fillna(d_i["COUNTRY"])
    d_i["ICG Orders"] = limpiar_numero(d_i["TRANS"])
    d_i["Facturado ICG"] = limpiar_numero(d_i["NET USD"])
    icg_res = d_i.groupby("País", as_index=False).agg(
        **{"ICG Orders": ("ICG Orders", "sum"), "Facturado ICG": ("Facturado ICG", "sum")}
    )
else:
    icg_res = pd.DataFrame(columns=["País", "ICG Orders", "Facturado ICG"])

df_calc = pd.merge(vtex_res, icg_res, on="País", how="outer")
for col in ["Vtex Orders", "Vtex Sales", "ICG Orders", "Facturado ICG"]:
    df_calc[col] = pd.to_numeric(df_calc[col], errors="coerce").fillna(0.0)

slas_pais = cfg_evt[["País", "Promesa_Dias", "Comentario"]].drop_duplicates(subset=["País"])
df_calc = pd.merge(df_calc, slas_pais, on="País", how="left")
df_calc["PROMESA DE ENTREGA"] = pd.to_numeric(df_calc["Promesa_Dias"], errors="coerce").fillna(7).astype(int)
df_calc["COMENTARIOS"] = df_calc["Comentario"].fillna("")

df_calc["AVANCE DE FACTURACIÓN"] = np.where(df_calc["Vtex Sales"] > 0, (df_calc["Facturado ICG"] / df_calc["Vtex Sales"]) * 100, 0.0)
df_calc["PEDIDOS PENDIENTES"] = df_calc["Vtex Orders"] - df_calc["ICG Orders"]
df_calc["GAP"] = df_calc["Facturado ICG"] - df_calc["Vtex Sales"]
df_calc["META MINIMA"] = np.ceil(df_calc["Vtex Orders"] / df_calc["PROMESA DE ENTREGA"])
df_calc["DÍAS HOMBRES"] = np.where(df_calc["META MINIMA"] > 0, np.round(df_calc["PEDIDOS PENDIENTES"] / df_calc["META MINIMA"], 0), 0)

with f2:
    paises_opciones = ["🌎 Todos los Países (Overview)"] + sorted(df_calc["País"].astype(str).unique().tolist())
    pais_sel = st.selectbox("2️⃣ Filtrar País:", paises_opciones)

df_vista = df_calc if "Todos" in pais_sel else df_calc[df_calc["País"] == pais_sel]

# ==========================================
# 5. TARJETAS RESUMEN Y TABLA PALETA BATH & BODY WORKS
# ==========================================
st.caption(f"📅 **Ventana del Evento:** `{f_ini.strftime('%Y-%m-%d')}` al `{f_fin.strftime('%Y-%m-%d')}`")

k1, k2, k3, k4 = st.columns(4)
tot_ord = df_vista["Vtex Orders"].sum()
tot_icg_ord = df_vista["ICG Orders"].sum()
tot_sales = df_vista["Vtex Sales"].sum()
tot_icg_sales = df_vista["Facturado ICG"].sum()
tot_pend = df_vista["PEDIDOS PENDIENTES"].sum()
tot_avance = (tot_icg_sales / tot_sales * 100) if tot_sales > 0 else 0.0

k1.metric("Vtex Orders", f"{tot_ord:,.0f}")
k2.metric("ICG Orders", f"{tot_icg_ord:,.0f}")
k3.metric("Pedidos Pendientes", f"{tot_pend:,.0f}")
k4.metric("Avance de Facturación", f"{tot_avance:.0f}%")

cols_tabla = [
    "País", "Vtex Orders", "Vtex Sales", "ICG Orders", "Facturado ICG",
    "AVANCE DE FACTURACIÓN", "PEDIDOS PENDIENTES", "GAP",
    "PROMESA DE ENTREGA", "META MINIMA", "DÍAS HOMBRES", "COMENTARIOS"
]

df_mostrar = df_vista[cols_tabla].copy()
if "Todos" in pais_sel and len(df_mostrar) > 1:
    fila_total = pd.DataFrame([{
        "País": "Total general",
        "Vtex Orders": df_mostrar["Vtex Orders"].sum(),
        "Vtex Sales": df_mostrar["Vtex Sales"].sum(),
        "ICG Orders": df_mostrar["ICG Orders"].sum(),
        "Facturado ICG": df_mostrar["Facturado ICG"].sum(),
        "AVANCE DE FACTURACIÓN": (df_mostrar["Facturado ICG"].sum() / df_mostrar["Vtex Sales"].sum() * 100) if df_mostrar["Vtex Sales"].sum() > 0 else 0.0,
        "PEDIDOS PENDIENTES": df_mostrar["PEDIDOS PENDIENTES"].sum(),
        "GAP": df_mostrar["GAP"].sum(),
        "PROMESA DE ENTREGA": np.nan,
        "META MINIMA": np.nan,
        "DÍAS HOMBRES": np.nan,
        "COMENTARIOS": ""
    }])
    df_mostrar = pd.concat([df_mostrar, fila_total], ignore_index=True)

def fmt_pendientes(val):
    if pd.isna(val):
        return ""
    return f"({abs(val):,.0f})" if val < 0 else f"{val:,.0f}"

def fmt_ent_vacio(val):
    return "" if pd.isna(val) else f"{val:,.0f}"

def aplicar_estilos_bbw(df):
    styler = df.style.format({
        "Vtex Orders": "{:,.0f}",
        "Vtex Sales": "${:,.2f}",
        "ICG Orders": "{:,.0f}",
        "Facturado ICG": "${:,.2f}",
        "AVANCE DE FACTURACIÓN": "{:.0f}%",
        "PEDIDOS PENDIENTES": fmt_pendientes,
        "GAP": "${:,.2f}",
        "PROMESA DE ENTREGA": fmt_ent_vacio,
        "META MINIMA": fmt_ent_vacio,
        "DÍAS HOMBRES": fmt_ent_vacio,
    })

    # Paleta Bath & Body Works:
    # Bloque VTEX (Azul Gingham Suave)
    styler = styler.set_properties(
        subset=["Vtex Orders", "Vtex Sales"],
        **{"background-color": "#EBF3FA", "color": "#1B365D", "font-weight": "600"}
    )
    # Bloque ICG (Celeste Gingham Medio)
    styler = styler.set_properties(
        subset=["ICG Orders", "Facturado ICG"],
        **{"background-color": "#D4E6F6", "color": "#0F2942", "font-weight": "600"}
    )
    # Bloque Operativo (Blanco limpio + Rosa BBW suave en Avance)
    styler = styler.set_properties(
        subset=["AVANCE DE FACTURACIÓN"],
        **{"background-color": "#FCE8EE", "color": "#9B1B48", "font-weight": "bold"}
    )

    def color_pendientes(val):
        if isinstance(val, (int, float)):
            if val < 0:
                return "color: #C00000; font-weight: bold;"
            elif val > 0:
                return "color: #1B365D; font-weight: 600;"
        return ""

    styler = styler.map(color_pendientes, subset=["PEDIDOS PENDIENTES"])

    def resaltar_total(row):
        if row["País"] == "Total general":
            return ["background-color: #1B365D; color: #FFFFFF; font-weight: bold;"] * len(row)
        return [""] * len(row)

    styler = styler.apply(resaltar_total, axis=1)
    return styler

st.subheader("📋 Cuadro de Seguimiento Operativo")
alto_tabla = (len(df_mostrar) + 1) * 38 + 10
st.dataframe(
    aplicar_estilos_bbw(df_mostrar),
    use_container_width=True,
    hide_index=True,
    height=alto_tabla,
    column_config={
        "País": st.column_config.TextColumn("País", width="small"),
        "COMENTARIOS": st.column_config.TextColumn("COMENTARIOS", width="large"),
    }
)
