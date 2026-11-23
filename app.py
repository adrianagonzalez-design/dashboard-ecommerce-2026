import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Dashboard Operativo 2026", page_icon="📊", layout="wide")

# ==========================================
# 1. PEGA AQUÍ EL ID DE TU GOOGLE SHEET
# ==========================================
SHEET_ID = "1DlGk2a1Olk7hlOwntiKNOc3W9xlQDCKtz7khS7j0dX0"

def leer_hoja(nombre_hoja):
    nombre_url = nombre_hoja.replace(" ", "%20")
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_url}"
    return pd.read_csv(url)

MAPA_PAISES = {
    "PANAMA": "PAN", "GUATEMALA": "GTM", "COLOMBIA": "COL", "PERU": "PER",
    "COSTA RICA": "CRI", "PARAGUAY": "PRY", "ECUADOR": "ECU",
    "ARGENTINA": "ARG", "EL SALVADOR": "SLV", "URUGUAY": "URY"
}

SLAS_DEFAULT = [
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "PAN", 6, ""),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "GTM", 7, ""),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "COL", 7, ""),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "PER", 7, ""),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "CRI", 7, "Problemas con la pasarela"),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "PRY", 5, ""),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "ECU", 7, ""),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "ARG", 8, ""),
    ("Mist Event Ago 2026", "Bath & Body Works", "2026-08-26", "2026-08-30", "SLV", 7, "Problemas con el pago"),
]

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_todo():
    df_bbw = leer_hoja("BBW")
    df_icg_bbw = leer_hoja("ICG REPORT BBW")

    try:
        df_tv_tf = leer_hoja("TV TF")
    except Exception:
        df_tv_tf = pd.DataFrame()

    try:
        df_vsba_vtex = leer_hoja("VSBA")
    except Exception:
        df_vsba_vtex = pd.DataFrame()

    try:
        df_slas = leer_hoja("EVENTOS_SLAS")
    except Exception:
        cols = ["Evento", "Marca", "Inicio", "Fin", "País", "Promesa_Dias", "Comentario"]
        df_slas = pd.DataFrame(SLAS_DEFAULT, columns=cols)

    try:
        df_ctrl = leer_hoja("CONTROL_UPDATE")
        last_upd = str(df_ctrl.iloc[0, 0])
    except Exception:
        last_upd = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    return df_bbw, df_icg_bbw, df_tv_tf, df_vsba_vtex, df_slas, last_upd

try:
    df_bbw, df_icg_bbw, df_tv_tf, df_vsba_vtex, df_slas, last_upd = cargar_todo()
except Exception as e:
    st.error("⚠️ Error conectando con Google Sheets. Revisa que el archivo esté compartido como 'Cualquier persona con el enlace puede ver' y que el SHEET_ID sea el correcto.")
    st.stop()

# ==========================================
# 3. ENCABEZADO Y FILTROS
# ==========================================
col_t, col_b = st.columns([4, 1])
with col_t:
    st.title("📊 Seguimiento Operativo & Capacidad de Procesamiento 2026")
    st.markdown(f"🕒 **Última actualización:** `{last_upd}`")
with col_b:
    st.write("")
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

f1, f2, f3 = st.columns(3)

with f1:
    marca_sel = st.selectbox("1️⃣ Marca:", ["Bath & Body Works", "Victoria's Secret", "Consolidado (Ambas Marcas)"])

with f2:
    if marca_sel == "Consolidado (Ambas Marcas)":
        eventos_disp = df_slas["Evento"].unique().tolist()
    else:
        ev_marca = df_slas[df_slas["Marca"] == marca_sel]["Evento"].unique().tolist()
        eventos_disp = ev_marca if len(ev_marca) > 0 else df_slas["Evento"].unique().tolist()
    evento_sel = st.selectbox("2️⃣ Evento 2026:", eventos_disp)

cfg_evt = df_slas[df_slas["Evento"] == evento_sel].copy()
if marca_sel != "Consolidado (Ambas Marcas)" and marca_sel in cfg_evt["Marca"].values:
    cfg_evt = cfg_evt[cfg_evt["Marca"] == marca_sel]

f_ini = pd.to_datetime(cfg_evt["Inicio"].iloc[0])
f_fin = pd.to_datetime(cfg_evt["Fin"].iloc[0])
dias_evento = max((f_fin - f_ini).days + 1, 1)

st.caption(f"📅 **Ventana del Evento:** `{f_ini.strftime('%Y-%m-%d')}` al `{f_fin.strftime('%Y-%m-%d')}` ({dias_evento} días)")

# ==========================================
# 4. PROCESAMIENTO Y CRUCE OPERATIVO
# ==========================================
def preparar_vtex(df):
    if df.empty:
        return pd.DataFrame(columns=["País", "Orders", "QTY", "Sales_USD"])
    d = df.copy()
    d["Fecha"] = pd.to_datetime(d["CreationDate"], errors="coerce").dt.normalize()
    if "StatusRawValue" in d.columns:
        d = d[~d["StatusRawValue"].astype(str).str.lower().isin(["canceled", "cancelled", "payment-pending"])]
    d = d[(d["Fecha"] >= f_ini) & (d["Fecha"] <= f_fin)]
    return d.groupby("Country", as_index=False).agg(
        Orders=("Order", "nunique"),
        QTY=("QuantitySKU", "sum"),
        Sales_USD=("TOTAL SKU PRICE (Dollar)", "sum")
    ).rename(columns={"Country": "País"})

def preparar_icg_bbw(df):
    if df.empty:
        return pd.DataFrame(columns=["País", "Order_ICG", "Sales_ICG"])
    d = df.copy()
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce").dt.normalize()
    d = d[d["TIENDA"].astype(str).str.contains("E-COMMERCE", case=False, na=False)]
    d = d[d["Fecha"] >= f_ini]
    d["País"] = d["País"].astype(str).str.upper().str.strip().map(MAPA_PAISES).fillna(d["País"])
    return d.groupby("País", as_index=False).agg(
        Order_ICG=("TRANSACCIONES", "sum"),
        Sales_ICG=("VENTAS_DTO", "sum")
    )

def preparar_icg_vsba(df):
    if df.empty:
        return pd.DataFrame(columns=["País", "Order_ICG", "Sales_ICG"])
    d = df.copy()
    d["Fecha"] = pd.to_datetime(d["DATE"], errors="coerce").dt.normalize()
    d = d[d["TYPE"].astype(str).str.upper() == "ECOMMERCE"]
    d = d[d["Fecha"] >= f_ini]
    d["País"] = d["COUNTRY"].astype(str).str.upper().str.strip().map(MAPA_PAISES).fillna(d["COUNTRY"])
    return d.groupby("País", as_index=False).agg(
        Order_ICG=("TRANS", "sum"),
        Sales_ICG=("NET USD", "sum")
    )

if marca_sel == "Bath & Body Works":
    vtex_res = preparar_vtex(df_bbw)
    icg_res = preparar_icg_bbw(df_icg_bbw)
elif marca_sel == "Victoria's Secret":
    vtex_res = preparar_vtex(df_vsba_vtex)
    icg_res = preparar_icg_vsba(df_tv_tf)
else:
    vtex_res = pd.concat([preparar_vtex(df_bbw), preparar_vtex(df_vsba_vtex)]).groupby("País", as_index=False).sum()
    icg_res = pd.concat([preparar_icg_bbw(df_icg_bbw), preparar_icg_vsba(df_tv_tf)]).groupby("País", as_index=False).sum()

df_calc = pd.merge(vtex_res, icg_res, on="País", how="outer").fillna(0)
slas_pais = cfg_evt[["País", "Promesa_Dias", "Comentario"]].drop_duplicates(subset=["País"])
df_calc = pd.merge(df_calc, slas_pais, on="País", how="left")
df_calc["Promesa_Dias"] = df_calc["Promesa_Dias"].fillna(7)
df_calc["Comentario"] = df_calc["Comentario"].fillna("")

df_calc["% Share"] = np.where(df_calc["Sales_USD"].sum() > 0, (df_calc["Sales_USD"] / df_calc["Sales_USD"].sum()) * 100, 0)
df_calc["Avance Facturación %"] = np.where(df_calc["Sales_USD"] > 0, (df_calc["Sales_ICG"] / df_calc["Sales_USD"]) * 100, 0)
df_calc["Pedidos Pendientes"] = df_calc["Orders"] - df_calc["Order_ICG"]
df_calc["GAP ($)"] = df_calc["Sales_ICG"] - df_calc["Sales_USD"]
df_calc["Meta Mínima Diaria"] = np.ceil(df_calc["Orders"] / df_calc["Promesa_Dias"])
df_calc["Pedido Promedio Diario"] = df_calc["Order_ICG"] / dias_evento
df_calc["Eficacia Operativa %"] = np.where(df_calc["Meta Mínima Diaria"] > 0, (df_calc["Pedido Promedio Diario"] / df_calc["Meta Mínima Diaria"]) * 100, 0)
df_calc["Días Hombre"] = np.where(df_calc["Meta Mínima Diaria"] > 0, df_calc["Pedidos Pendientes"] / df_calc["Meta Mínima Diaria"], 0)

with f3:
    paises_lista = ["🌎 OVERVIEW REGIONAL (Todos los Países)"] + sorted(df_calc["País"].unique().tolist())
    pais_sel = st.selectbox("3️⃣ País:", paises_lista)

df_vista = df_calc if "OVERVIEW" in pais_sel else df_calc[df_calc["País"] == pais_sel]

# ==========================================
# 5. KPIS, GRÁFICOS Y TABLA OPERATIVA
# ==========================================
k1, k2, k3, k4, k5 = st.columns(5)
tot_orders = df_vista["Orders"].sum()
tot_icg = df_vista["Order_ICG"].sum()
pend = df_vista["Pedidos Pendientes"].sum()
avance_tot = (df_vista["Sales_ICG"].sum() / df_vista["Sales_USD"].sum() * 100) if df_vista["Sales_USD"].sum() > 0 else 0
dias_h = df_vista["Días Hombre"].mean()

k1.metric("Orders (Entrantes)", f"{tot_orders:,.0f}")
k2.metric("Orders ICG (Facturadas)", f"{tot_icg:,.0f}")
k3.metric("Pedidos Pendientes", f"{pend:,.0f}")
k4.metric("Avance Facturación", f"{avance_tot:.1f}%")
k5.metric("Días Hombre (Backlog)", f"{dias_h:.2f} días")

st.divider()

g1, g2 = st.columns([1.3, 1])
with g1:
    st.subheader("📦 Orders Entrantes vs. Facturadas (ICG)")
    fig1 = px.bar(
        df_vista, x="País", y=["Orders", "Order_ICG"], barmode="group",
        labels={"value": "Pedidos", "variable": "Métrica"},
        color_discrete_map={"Orders": "#64748B", "Order_ICG": "#0EA5E9"}
    )
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.subheader("⏱️ Días Hombre por País")
    fig2 = px.bar(
        df_vista, x="País", y="Días Hombre",
        color="Días Hombre", color_continuous_scale="RdYlGn_r"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("📋 Seguimiento Detallado de Capacidad Operativa")
cols_mostrar = [
    "País", "Orders", "QTY", "Sales_USD", "% Share", "Sales_ICG", "Order_ICG",
    "Avance Facturación %", "Pedidos Pendientes", "GAP ($)", "Promesa_Dias",
    "Meta Mínima Diaria", "Pedido Promedio Diario", "Eficacia Operativa %",
    "Días Hombre", "Comentario"
]

st.dataframe(
    df_vista[cols_mostrar].style.format({
        "Orders": "{:,.0f}", "QTY": "{:,.0f}", "Sales_USD": "${:,.2f}",
        "% Share": "{:.1f}%", "Sales_ICG": "${:,.2f}", "Order_ICG": "{:,.0f}",
        "Avance Facturación %": "{:.1f}%", "Pedidos Pendientes": "{:,.0f}",
        "GAP ($)": "${:,.2f}", "Promesa_Dias": "{:.0f}",
        "Meta Mínima Diaria": "{:,.0f}", "Pedido Promedio Diario": "{:,.1f}",
        "Eficacia Operativa %": "{:.1f}%", "Días Hombre": "{:.2f}"
    }),
    use_container_width=True,
    hide_index=True
)
