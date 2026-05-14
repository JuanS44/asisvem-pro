import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime, timedelta
import os
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from PIL import Image

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="Asisvem PRO", layout="wide", page_icon="🏢")

# --- 2. GESTIÓN DE USUARIOS ---
credentials = {
    "usernames": {
        "juan_asisvem": {"name": "Juan Rodriguez", "password": "asisvem2026", "logo": "Logo JSRM.jpeg"},
        "usuario_demo": {"name": "Demo Test", "password": "123", "logo": "Logo Asisvem 2022 PNG (1).png"},
        "Benar": {"name": "Julio Benavides", "password": "lubricentro2026", "logo": "Logo Asisvem 2022 PNG (1).png"},
    }
}

authenticator = stauth.Authenticate(credentials, "asisvem_session", "clave_secreta_asisvem", cookie_expiry_days=1)

# --- 3. FUNCIONES DE APOYO ---
def leer_historial(file):
    if os.path.exists(file):
        df = pd.read_csv(file)
        if "Referencia" not in df.columns: 
            return pd.DataFrame(columns=["Fecha_Gestion", "Cliente", "Referencia"])
        return df
    return pd.DataFrame(columns=["Fecha_Gestion", "Cliente", "Referencia"])

# --- 4. INTERFAZ DE ACCESO ---
if not st.session_state.get("authentication_status"):
    tab_login, tab_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Solicitar Acceso"])
    with tab_login:
        # LOGO DE ASISVEM CENTRADO EN LOGIN
        try:
            col_izq, col_centro, col_der = st.columns([2, 1, 2])
            with col_centro:
                st.image("Logo Asisvem 2022 PNG (1).png", use_container_width=True)
        except: pass
        authenticator.login(location='main')
    with tab_reg:
        st.info("Formulario de solicitud de acceso activo.")

# --- 5. PANEL DE CONTROL ---
if st.session_state["authentication_status"]:
    user_id = st.session_state["username"]
    # Obtener logo personalizado del usuario
    logo_user = credentials["usernames"][user_id].get("logo", "Logo Asisvem 2022 PNG (1).png")
    
    HISTORIAL_FILE = f"historial_{user_id}.csv" 
    MSG_FILE = f"mensaje_{user_id}.txt"
    
    MSG_DEFAULT = "Hola {nombre}, recordarte que tu {detalle} para {referencia} vence el {fecha}."
    if not os.path.exists(MSG_FILE):
        with open(MSG_FILE, "w", encoding="utf-8") as f: f.write(MSG_DEFAULT)
    
    with open(MSG_FILE, "r", encoding="utf-8") as f: 
        msg_cargado = f.read()
        msg_cargado = msg_cargado.replace("{servicio}", "{detalle}").replace("{placa}", "{referencia}")
    
    if 'mensaje_personalizado' not in st.session_state:
        st.session_state.mensaje_personalizado = msg_cargado

    # --- BARRA LATERAL ---
    with st.sidebar:
        # LOGO DEL CLIENTE EN LA PARTE SUPERIOR
        try:
            st.image(logo_user, use_container_width=True)
        except:
            st.image("Logo Asisvem 2022 PNG (1).png", use_container_width=True)
            
        st.write(f"### Bienvenid@, {st.session_state['name']}")
        authenticator.logout('Cerrar Sesión', 'sidebar')
        st.divider()
        uploaded_file = st.file_uploader("📂 Cargar Base de Datos (.xlsx)", type=["xlsx"])
        dias_margen = st.slider("Días de anticipación", 1, 60, 8)
        st.divider()
        with st.expander("📊 Historial Rápido"):
            st.dataframe(leer_historial(HISTORIAL_FILE), hide_index=True)
            
        # LOGO DE ASISVEM Y SOPORTE EN LA PARTE INFERIOR
        st.markdown("<br>" * 5, unsafe_allow_html=True)
        st.divider()
        col_asis_logo, col_asis_txt = st.columns([1, 4])
        with col_asis_logo:
            try: st.image("Logo Asisvem 2022 PNG (1).png", width=35)
            except: pass
        with col_asis_txt:
            st.caption("**Soporte Técnico**")
            st.caption("gerencia@asisvem.com")

    # --- PESTAÑAS PRINCIPALES ---
    tabs_principales = st.tabs(["📖 Manual y Configuración de Mensaje", "🔔 Gestión de Alertas", "✅ Gestionados"])

    with tabs_principales[0]:
        col_m, col_c = st.columns([2, 1])
        with col_m:
            st.header("📘 Manual de Estandarización Asisvem PRO")
            st.markdown("""
            Para que el sistema funcione, tu Excel **DEBE** tener estas columnas exactas:
            1. **Nombre**: Quién recibe el mensaje.
            2. **Celular**: Número con código de país (ej: 573...).
            3. **Fecha**: Cuándo vence el beneficio o cita.
            4. **Referencia**: El objeto (Carro, Zapato, ID de contrato).
            5. **Detalle**: El motivo (Mantenimiento, Descuento, Cobro).
            """)
            
            manual_data = {
                "Columna": ["Nombre", "Celular", "Fecha", "Referencia", "Detalle"],
                "Ejemplo": ["Erasmo Ceron", "3103906891", "2026-05-13", "Nike Air Force", "Promoción 20%"]
            }
            st.table(manual_data)
            
            st.subheader("💡 Instrucciones de la Herramienta")
            st.markdown("""
            * **Barra de Progreso:** Muestra cuántos clientes del rango seleccionado ya fueron avisados.
            * **Buscador:** Filtra por nombre o referencia en tiempo real.
            * **Botón WhatsApp:** Abre el chat con el mensaje preconfigurado.
            * **Botón Marcar ✔️:** Mueve al cliente a 'Gestionados' y lo guarda en el historial (archivo CSV local).
            """)

        with col_c:
            st.subheader("⚙️ Mensaje a Enviar")
            st.caption("Etiquetas: {nombre}, {referencia}, {detalle}, {fecha}")
            nuevo_msg = st.text_area("Editar cuerpo:", value=st.session_state.mensaje_personalizado, height=200)
            if st.button("💾 Guardar Mensaje"):
                with open(MSG_FILE, "w", encoding="utf-8") as f: f.write(nuevo_msg)
                st.session_state.mensaje_personalizado = nuevo_msg
                st.success("Mensaje actualizado")

    with tabs_principales[1]:
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            if not all(c in df.columns for c in ["Nombre", "Celular", "Fecha", "Referencia", "Detalle"]):
                st.error("⚠️ El Excel no cumple con el manual de columnas. Revisa la pestaña anterior.")
            else:
                df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
                historial = leer_historial(HISTORIAL_FILE)
                hoy = datetime.now().date()
                limite = hoy + timedelta(days=dias_margen)
                
                df_rango = df[(df["Fecha"] >= hoy) & (df["Fecha"] <= limite)]
                gestionados_list = historial["Referencia"].astype(str).tolist()
                
                busq = st.text_input("🔍 Buscar cliente o referencia:").upper()
                pendientes = df_rango[~df_rango["Referencia"].astype(str).isin(gestionados_list)]
                
                if busq:
                    pendientes = pendientes[pendientes["Nombre"].str.contains(busq, na=False) | 
                                            pendientes["Referencia"].astype(str).str.contains(busq, na=False)]
                
                progreso = len(df_rango) - len(df_rango[~df_rango["Referencia"].astype(str).isin(gestionados_list)])
                st.write(f"**Progreso de hoy:** {progreso} de {len(df_rango)}")
                st.progress(progreso/len(df_rango) if len(df_rango)>0 else 0)

                for idx, row in pendientes.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        c1.write(f"👤 **{row['Nombre']}** | 📦 {row['Referencia']}")
                        c1.caption(f"📅 Vence: {row['Fecha']} | 📝 {row['Detalle']}")
                        
                        num = "".join(filter(str.isdigit, str(row['Celular']).split('.')[0]))
                        texto = st.session_state.mensaje_personalizado.format(
                            nombre=row['Nombre'], referencia=row['Referencia'], 
                            detalle=row['Detalle'], fecha=row['Fecha']
                        )
                        url = f"https://api.whatsapp.com/send?phone={num}&text={urllib.parse.quote(texto)}"
                        c2.link_button("🚀 Enviar WhatsApp", url, use_container_width=True)
                        
                        if c3.button("Marcar ✔️", key=f"p_{idx}", use_container_width=True):
                            nueva_g = pd.DataFrame([{"Fecha_Gestion": datetime.now().strftime("%Y-%m-%d %H:%M"), "Cliente": row['Nombre'], "Referencia": row['Referencia']}])
                            pd.concat([historial, nueva_g]).to_csv(HISTORIAL_FILE, index=False)
                            st.rerun()
        else:
            st.warning("👈 Carga un archivo Excel en la barra lateral para ver los pendientes.")

    with tabs_principales[2]:
        if uploaded_file:
            historial = leer_historial(HISTORIAL_FILE)
            avisados = historial[historial["Referencia"].astype(str).isin(df_rango["Referencia"].astype(str))]
            for idx, row in avisados.iterrows():
                with st.container(border=True):
                    ca, cb = st.columns([4, 1])
                    ca.write(f"✅ {row['Cliente']} ({row['Referencia']})")
                    ca.caption(f"Gestionado el: {row['Fecha_Gestion']}")
                    if cb.button("Deshacer", key=f"d_{idx}"):
                        historial = historial[historial["Referencia"].astype(str) != str(row['Referencia'])]
                        historial.to_csv(HISTORIAL_FILE, index=False)
                        st.rerun()