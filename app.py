
import streamlit as st
from openai import OpenAI
from docx import Document
from fpdf import FPDF
import base64
import os
import re
from datetime import date, time
import gspread
import json
from google.oauth2.service_account import Credentials

# Leer las credenciales desde st.secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client_sheets = gspread.authorize(creds)
sheet = client_sheets.open("historial_autocontent_ai").sheet1

def guardar_en_hoja(usuario, tema, contenido, fecha, hora):
    fila = [usuario, tema, str(fecha), str(hora), contenido]
    sheet.append_row(fila)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="AutoContent AI", layout="wide")

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

st.sidebar.title("👤 Iniciar sesión")
usuario_input = st.sidebar.text_input("Tu nombre de usuario", value=st.session_state.usuario)
if st.sidebar.button("Entrar") and usuario_input.strip():
    st.session_state.usuario = usuario_input.strip()

if not st.session_state.usuario:
    st.warning("Por favor, ingresa tu nombre de usuario para acceder a la app.")
    st.stop()

usuario = st.session_state.usuario
st.success(f"Bienvenido, {usuario} 👋")
st.title("🧠 AutoContent AI - Generador de Contenido Automatizado")

if "historial" not in st.session_state:
    st.session_state.historial = []

st.sidebar.header("Configuración del contenido")
tipo_contenido = st.sidebar.selectbox("Tipo de contenido", ["Post de Instagram", "Artículo de Blog", "Email Marketing", "Guión de video", "TikTok / Reel"])
tono = st.sidebar.selectbox("Tono de voz", ["Profesional", "Creativo", "Casual", "Inspirador"])
tema = st.sidebar.text_area("Tema o idea principal", "")

def generar_pdf(texto, nombre_archivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for linea in texto.split("\n"):
        try:
            linea = re.sub(r'[^\x00-\x7F\u00A1-\u00FF]+', '', linea)
            pdf.multi_cell(0, 10, linea)
        except:
            continue
    pdf.output(nombre_archivo)


