import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE MARCA Y GOOGLE SHEET
# ==========================================
NOMBRE_MARCA = "BATH & BODY WORKS"
SHEET_ID = "1DlGk2a1Olk7hlOwntiKNOc3W9xlQDCKtz7khS7j0dX0"

st.set_page_config(
    page_title=f"Seguimiento Operativo | {NOMBRE_MARCA}",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. ESTILO CORPORATIVO CLEAN (BATH & BODY WORKS)
# ==========================================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1E293B;
}

.stApp {
    background-color: #FFFFFF;
}

.block-container {
    padding-top: 3.2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1440px;
}

.bbw-brand-tag {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #005696;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}

.bbw-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1B365D;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.2;
}

.bbw-meta {
    font-size: 0.85rem;
    color: #64748B;
    margin-top: 0.45rem;
}

div.stButton > button {
    background-color: #FFFFFF;
    color: #1B365D;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.45rem 1rem;
    transition: all 0.15s ease;
}
div.stButton > button:hover {
    background-color: #F0F6FC;
    border-color: #005696;
    color: #005696;
}

div[data-baseweb="select"] > div {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    font-size: 0.9rem;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.1rem 0 1.75rem 0;
}
.kpi-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
}
.kpi-card.accent {
    background-color: #F0F6FC;
    border-color: #BFD9F2;
}
.kpi-label {
    font-size: 0.76rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 0.35rem;
}
.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1B365D;
    line-height: 1.15;
}
.kpi-sub {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 0.3rem;
}

.section-header {
    font-size: 1.05rem;
    font-weight: 600;
    color: #1B365D;
    margin-bottom: 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #E2E8F0;
}

.table-wrapper {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
}

table.bbw-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
    background-color: #FFFFFF;
}

table.bbw-table thead th {
    background-color: #1B365D;
    color: #FFFFFF;
    font-weight: 600;
    font-size: 0.74rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.75rem 0.65rem;
    text-align: right;
    border-bottom: 2px solid #0F2342;
    white-space: nowrap;
}

table.bbw-table thead th.col-left {
    text-align: left;
}

table.bbw-table thead th.th-vtex {
    background-color: #005696;
}

table.bbw-table thead th.th-icg {
    background-color: #2B6CB0;
}

table.bbw-table tbody td {
    padding: 0.65rem 0.65rem;
    border-bottom: 1px solid #E2E8F0;
    text-align: right;
    color: #1E293B;
    white-space: nowrap;
}

table.bbw-table tbody tr:hover td {
    background-color: #F8FAFC !important;
}

table.bbw-table tbody td.col-pais {
    text-align: left;
    font-weight: 600;
    color: #1B365D;
}

table.bbw-table tbody td.bg-vtex {
    background-color: #F4F8FC;
    color: #1B365D;
    font-weight: 500;
}

table.bbw-table tbody td.bg-icg {
    background-color: #EBF3FA;
    color: #0F2942;
    font-weight: 500;
}

table.bbw-table tbody td.bg-avance {
    background-color: #FDF2F5;
    color: #9B1B48;
    font-weight: 600;
}

table.bbw-table tbody td.pend-neg {
    color: #B91C1C;
    font-weight: 600;
}

table.bbw-table tbody td.pend-pos {
    color: #1B365D;
    font-weight: 600;
}

table.bbw-table tbody td.col-comentarios {
    text-align: left;
    white-space: normal;
    min-width: 240px;
    max-width: 340px;
    color: #475569;
    font-size: 0.82rem;
}

table.bbw-table tbody tr.row-total td {
    background-color: #1B365D !important;
    color: #FFFFFF !important;
    font-weight: 700;
    border-top: 2px solid #0F2342;
    border-bottom: none;
    padding: 0.75rem 0.65rem;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# ==========================================
# 3. FUNCIONES DE LECTURA Y LIMPIEZA
# ==========================================
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
        if not s or s.lower() in ["nan", "none", "#num!", "#div/0!", "#value!", "#n/a", "-"]:
            return 0.0
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
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
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "PAN", 6, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "GTM", 7, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "COL", 7, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "PER", 7, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "CRI", 7, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "PRY", 5, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "ECU", 7, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "ARG", 8, ""),
    ("Black Friday 2026", "2026-11-22", "2026-11-29", "SLV", 7, ""),
]

# ==========================================
# 4. CARGA DE DATOS
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

    last_upd = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    try:
        df_ctrl = leer_hoja("CONTROL_UPDATE")
        if not df_ctrl.empty:
            val_ctrl = str(df_ctrl.iloc[0, 0]).strip()
            if "/" in val_ctrl or "-" in val_ctrl:
                last_upd = val_ctrl
    except Exception:
        pass

    return df_vtex, df_icg, df_slas, last_upd

df_vtex, df_icg, df_slas, last_upd = cargar_datos()

if df_vtex.empty:
    st.error("No se encontraron datos válidos en la hoja de ventas.")
    st.stop()

# ==========================================
# 5. ENCABEZADO Y FILTROS LIMPIOS
# ==========================================
col_t, col_b = st.columns([5, 1])
with col_t:
    st.markdown(
        f'<div class="bbw-brand-tag">{NOMBRE_MARCA}</div>'
        f'<h1 class="bbw-title">Seguimiento Operativo y Capacidad de Procesamiento</h1>'
        f'<div class="bbw-meta">Última actualización de datos: <strong>{last_upd}</strong></div>',
        unsafe_allow_html=True
    )

with col_b:
    st.write("")
    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<hr style='margin: 1rem 0 1.25rem 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

f1, f2, _ = st.columns([1.2, 1.2, 1.6])
with f1:
    eventos_disp = df_slas["Evento"].dropna().unique().tolist()
    evento_sel = st.selectbox("Evento", eventos_disp)

cfg_evt = df_slas[df_slas["Evento"] == evento_sel].copy()
f_ini = pd.to_datetime(cfg_evt["Inicio"].iloc[0])
f_fin = pd.to_datetime(cfg_evt["Fin"].iloc[0])

# ==========================================
# 6. PROCESAMIENTO OPERATIVO
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
df_calc["COMENTARIOS"] = df_calc["Comentario"].fillna("").astype(str).replace("nan", "")

df_calc["AVANCE DE FACTURACIÓN"] = np.where(df_calc["Vtex Sales"] > 0, (df_calc["Facturado ICG"] / df_calc["Vtex Sales"]) * 100, 0.0)
df_calc["PEDIDOS PENDIENTES"] = df_calc["Vtex Orders"] - df_calc["ICG Orders"]
df_calc["GAP"] = df_calc["Facturado ICG"] - df_calc["Vtex Sales"]
df_calc["META MINIMA"] = np.ceil(df_calc["Vtex Orders"] / df_calc["PROMESA DE ENTREGA"])
df_calc["DÍAS HOMBRES"] = np.where(df_calc["META MINIMA"] > 0, np.round(df_calc["PEDIDOS PENDIENTES"] / df_calc["META MINIMA"], 0), 0)

with f2:
    paises_opciones = ["Todos los países"] + sorted(df_calc["País"].astype(str).unique().tolist())
    pais_sel = st.selectbox("País", paises_opciones)

df_vista = df_calc if pais_sel == "Todos los países" else df_calc[df_calc["País"] == pais_sel]

# ==========================================
# 7. TARJETAS KPI CLEAN
# ==========================================
tot_ord = df_vista["Vtex Orders"].sum()
tot_icg_ord = df_vista["ICG Orders"].sum()
tot_sales = df_vista["Vtex Sales"].sum()
tot_icg_sales = df_vista["Facturado ICG"].sum()
tot_pend = df_vista["PEDIDOS PENDIENTES"].sum()
tot_avance = (tot_icg_sales / tot_sales * 100) if tot_sales > 0 else 0.0

kpi_html = (
    f'<div style="font-size: 0.82rem; color: #64748B; margin-top: 0.25rem;">'
    f'Ventana del evento: <strong>{f_ini.strftime("%d/%m/%Y")}</strong> al <strong>{f_fin.strftime("%d/%m/%Y")}</strong>'
    f'</div>'
    f'<div class="kpi-grid">'
    f'<div class="kpi-card"><div class="kpi-label">Vtex Orders</div><div class="kpi-value">{tot_ord:,.0f}</div><div class="kpi-sub">Venta entrante: ${tot_sales:,.2f}</div></div>'
    f'<div class="kpi-card"><div class="kpi-label">ICG Orders</div><div class="kpi-value">{tot_icg_ord:,.0f}</div><div class="kpi-sub">Facturado: ${tot_icg_sales:,.2f}</div></div>'
    f'<div class="kpi-card"><div class="kpi-label">Pedidos Pendientes</div><div class="kpi-value">{tot_pend:,.0f}</div><div class="kpi-sub">Por facturar en ERP</div></div>'
    f'<div class="kpi-card accent"><div class="kpi-label">Avance de Facturación</div><div class="kpi-value">{tot_avance:.0f}%</div><div class="kpi-sub">Sobre venta total USD</div></div>'
    f'</div>'
)
st.markdown(kpi_html, unsafe_allow_html=True)

# ==========================================
# 8. TABLA HTML CORPORATIVA (SIN SANGRÍAS)
# ==========================================
st.markdown('<div class="section-header">Detalle de Capacidad Operativa por País</div>', unsafe_allow_html=True)

filas = []
for _, r in df_vista.iterrows():
    pend_val = r["PEDIDOS PENDIENTES"]
    if pend_val < 0:
        pend_str = f"({abs(pend_val):,.0f})"
        pend_cls = "pend-neg"
    else:
        pend_str = f"{pend_val:,.0f}"
        pend_cls = "pend-pos"

    filas.append(
        f'<tr>'
        f'<td class="col-pais">{r["País"]}</td>'
        f'<td class="bg-vtex">{r["Vtex Orders"]:,.0f}</td>'
        f'<td class="bg-vtex">${r["Vtex Sales"]:,.2f}</td>'
        f'<td class="bg-icg">{r["ICG Orders"]:,.0f}</td>'
        f'<td class="bg-icg">${r["Facturado ICG"]:,.2f}</td>'
        f'<td class="bg-avance">{r["AVANCE DE FACTURACIÓN"]:.0f}%</td>'
        f'<td class="{pend_cls}">{pend_str}</td>'
        f'<td>${r["GAP"]:,.2f}</td>'
        f'<td>{r["PROMESA DE ENTREGA"]:.0f}</td>'
        f'<td>{r["META MINIMA"]:,.0f}</td>'
        f'<td>{r["DÍAS HOMBRES"]:,.0f}</td>'
        f'<td class="col-comentarios">{r["COMENTARIOS"]}</td>'
        f'</tr>'
    )

if pais_sel == "Todos los países" and len(df_vista) > 1:
    tot_gap = df_vista["GAP"].sum()
    tot_pend_str = f"({abs(tot_pend):,.0f})" if tot_pend < 0 else f"{tot_pend:,.0f}"
    filas.append(
        f'<tr class="row-total">'
        f'<td style="text-align:left;">Total general</td>'
        f'<td>{tot_ord:,.0f}</td>'
        f'<td>${tot_sales:,.2f}</td>'
        f'<td>{tot_icg_ord:,.0f}</td>'
        f'<td>${tot_icg_sales:,.2f}</td>'
        f'<td>{tot_avance:.0f}%</td>'
        f'<td>{tot_pend_str}</td>'
        f'<td>${tot_gap:,.2f}</td>'
        f'<td></td><td></td><td></td><td></td>'
        f'</tr>'
    )

tabla_html = (
    '<div class="table-wrapper">'
    '<table class="bbw-table">'
    '<thead><tr>'
    '<th class="col-left">País</th>'
    '<th class="th-vtex">Vtex Orders</th>'
    '<th class="th-vtex">Vtex Sales</th>'
    '<th class="th-icg">ICG Orders</th>'
    '<th class="th-icg">Facturado ICG</th>'
    '<th>Avance de Facturación</th>'
    '<th>Pedidos Pendientes</th>'
    '<th>GAP</th>'
    '<th>Promesa de Entrega</th>'
    '<th>Meta Mínima</th>'
    '<th>Días Hombres</th>'
    '<th class="col-left">Comentarios</th>'
    '</tr></thead>'
    f'<tbody>{"".join(filas)}</tbody>'
    '</table>'
    '</div>'
)

st.markdown(tabla_html, unsafe_allow_html=True)
