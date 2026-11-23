import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Operativo E-Commerce 2026",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 1. CONEXIÓN A GOOGLE SHEETS
# ==========================================
# REEMPLAZA LO QUE ESTÁ ENTRE COMILLAS POR EL ID DE TU GOOGLE SHEET
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
        df_slas = pd.DataFrame([
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2026-08-26", "Fin": "2026-08-30", "País": "PAN", "Promesa_Dias": 6, "Comentario": ""},
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2026-08-26", "Fin": "2026-08-30", "País": "GTM", "Promesa_Dias": 7, "Comentario": ""},
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2026-08-26", "Fin": "2026-08-30", "País": "COL", "Promesa_Dias": 7, "Comentario": ""},
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2026-08-26", "Fin": "2026-08-30", "País": "PER", "Promesa_Dias": 7, "Comentario": ""},
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2026-08-26", "Fin": "2026-08-30", "País": "CRI", "Promesa_Dias": 7, "Comentario": "Problemas con la pasarela"},
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2026-08-26", "Fin": "2026-08-30", "País": "PRY", "Promesa_Dias": 5, "Comentario": ""},
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2026-08-26", "Fin": "2026-08-30", "País": "ECU", "Promesa_Dias": 7, "Comentario": ""},
            {"Evento": "Mist Event Ago 2026", "Marca": "Bath & Body Works", "Inicio": "2
