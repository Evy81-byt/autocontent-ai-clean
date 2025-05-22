

import streamlit as st
from openai import OpenAI, RateLimitError, OpenAIError
from docx import Document
from fpdf import FPDF
import base64
import csv
import os
import re
import requests
import pandas as pd
import calendar
from datetime import datetime

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="AutoContent AI", layout="wide")
st.markdown("""
<style>
body, div, input, button, textarea {
    cursor: url('https://cur.cursors-4u.net/nature/nat-10/nat974.cur'), auto !important;
}
</style>
""", unsafe_allow_html=True)


# === LOGIN SIMPLE ===
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
tipo_contenido = st.sidebar.selectbox("Tipo de contenido", [
    "Post de Instagram",
    "Carrusel de Instagram",
    "TikTok / Reel",
    "Artículo de Blog",
    "Email Marketing",
    "Descripción de Producto",
    "Guión de video"
])
tono = st.sidebar.selectbox("Tono de voz", ["Profesional", "Creativo", "Casual", "Inspirador"])
tema = st.sidebar.text_input("Tema o idea principal", "")

def generar_pdf(texto, nombre_archivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for linea in texto.split("\n"):
        linea = re.sub(r'[^\x00-\x7F]+', '', linea)
        pdf.multi_cell(0, 10, linea)
    pdf.output(nombre_archivo)

def generar_docx(texto, nombre_archivo):
    doc = Document()
    for linea in texto.split("\n"):
        doc.add_paragraph(linea)
    doc.save(nombre_archivo)

def obtener_descarga_binaria(ruta_archivo):
    with open(ruta_archivo, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def guardar_en_csv(tema, contenido, fecha, hora, tipo):
    archivo = f"historial_{usuario.lower()}.csv"
    existe = os.path.isfile(archivo)
    with open(archivo, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["Tema", "Tipo", "Fecha", "Hora", "Contenido"])
        writer.writerow([tema, tipo, fecha, hora, contenido])

if st.sidebar.button("Generar Contenido") and tema:
    with st.spinner("Generando contenido con IA..."):
        prompt = f"Escribe un {tipo_contenido.lower()} sobre el tema '{tema}' con un tono {tono.lower()}."

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en marketing y redacción de contenido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            contenido_generado = response.choices[0].message.content

            st.subheader("✍️ Contenido Generado")
            st.markdown(contenido_generado)
            st.code(contenido_generado, language="markdown")

            st.markdown("### 📤 Compartir contenido")
            st.button("📋 Copiar contenido al portapapeles", on_click=lambda: st.session_state.update({"copiar": contenido_generado}))
            twitter_text = contenido_generado[:280].replace(" ", "%20").replace("\n", "%0A")
            twitter_url = f"https://twitter.com/intent/tweet?text={twitter_text}"
            st.markdown(f"[🐦 Compartir en Twitter]({twitter_url})", unsafe_allow_html=True)
            st.info("📸 Para Instagram: Copia el texto y publícalo directamente como descripción del post o en un carrusel.")

            st.markdown("### 📑 Ver como carrusel para Instagram")
            def generate_carrusel_slides(text, max_chars=400):
                paragraphs = text.split('\n')
                slides = []
                current = ""
                for para in paragraphs:
                    if len(current) + len(para) < max_chars:
                        current += para + "\n"
                    else:
                        slides.append(current.strip())
                        current = para + "\n"
                if current.strip():
                    slides.append(current.strip())
                return slides

            slides = generate_carrusel_slides(contenido_generado)
            for i, slide in enumerate(slides, 1):
                with st.expander(f"🖼️ Slide {i} de {len(slides)}"):
                    st.write(slide)

            if st.download_button("📥 Descargar como archivo .txt (Carrusel)", contenido_generado.encode("utf-8"), file_name="carrusel.txt"):
                st.success("Descarga iniciada.")

            st.markdown("### 🧾 Vista previa estilo post")
            with st.container():
                st.markdown("""
                <div style="border:1px solid #ccc; border-radius:10px; padding:15px; background-color:#fff; max-width:600px">
                    <div style="display:flex; align-items:center;">
                        <img src="https://i.imgur.com/6VBx3io.png" width="40" height="40" style="border-radius:50%; margin-right:10px;">
                        <strong>Evy</strong>
                    </div>
                    <div style="margin-top:10px; font-size:15px; line-height:1.5; color:#333;">
                        {content}
                    </div>
                </div>
                """.replace("{content}", contenido_generado.replace("\n", "<br>")),
                unsafe_allow_html=True)

            st.info("🖼️ Generando imagen relacionada con el contenido...")
            image_response = client.images.generate(
                model="dall-e-3",
                prompt="Ambiente natural minimalista con productos de cuidado de la piel en fondo neutro elegante, estilo realista, sin logotipos ni rostros.",
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = image_response.data[0].url
            st.image(image_url, caption="🎨 Imagen generada por IA", use_container_width=True)

            st.markdown("📤 O sube tu propia imagen para acompañar la publicación:")
            uploaded_image = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])
            if uploaded_image:
                st.image(uploaded_image, caption="📌 Imagen subida", use_container_width=True)

        except RateLimitError:
            st.error("🚫 Has alcanzado el límite de uso de OpenAI. Por favor, espera unos minutos e intenta de nuevo.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error generando contenido: {e}")
            st.stop()

        nombre_pdf = "contenido_generado.pdf"
        nombre_docx = "contenido_generado.docx"
        generar_pdf(contenido_generado, nombre_pdf)
        generar_docx(contenido_generado, nombre_docx)

        pdf_encoded = obtener_descarga_binaria(nombre_pdf)
        docx_encoded = obtener_descarga_binaria(nombre_docx)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📄 Descargar como PDF", base64.b64decode(pdf_encoded), nombre_pdf, "application/pdf")
        with col2:
            st.download_button("📝 Descargar como Word", base64.b64decode(docx_encoded), nombre_docx,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        with st.expander("📈 Optimización SEO"):
            st.markdown(f"- Sugerencia de título: `Título atractivo para SEO sobre {tema}`")
            st.markdown(f"- Palabras clave: `{tema.lower()}`, `{tema.lower().split()[0]}`")
            st.markdown("- Meta descripción: Texto breve que resume el contenido de forma efectiva.")

        with st.expander("📅 Programar Publicación"):
            fecha = st.date_input("Selecciona fecha para publicación")
            hora = st.time_input("Hora de publicación")
            if st.button("📌 Guardar programación"):
                st.session_state.historial.append({
                    "tema": tema,
                    "tipo": tipo_contenido,
                    "contenido": contenido_generado,
                    "fecha": str(fecha),
                    "hora": str(hora)
                })
                guardar_en_csv(tema, contenido_generado, fecha, hora, tipo_contenido)
                st.success("✅ Contenido guardado correctamente.")
else:
    st.info("Ingresa un tema para generar contenido.")

# === Calendario visual de publicaciones ===
st.subheader("📆 Calendario de publicaciones")

if os.path.exists("historial.csv"):
    df = pd.read_csv("historial.csv")
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    hoy = datetime.now()
    mes = hoy.month
    anio = hoy.year
    dias_mes = calendar.monthrange(anio, mes)[1]

    calendario = {day: [] for day in range(1, dias_mes + 1)}
    for _, row in df[df["Fecha"].dt.month == mes].iterrows():
        dia = row["Fecha"].day
        contenido = f"- 📝 **{row['Tema']}** ({row['Tipo']}) a las {row['Hora']}"
        calendario[dia].append(contenido)

    for dia in range(1, dias_mes + 1):
        if calendario[dia]:
            with st.expander(f"📅 {dia}/{mes}/{anio} ({len(calendario[dia])} publicaciones)"):
                for item in calendario[dia]:
                    st.markdown(item)
else:
    st.info("No hay publicaciones programadas aún.")
