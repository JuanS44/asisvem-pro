import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime, timedelta
import os
import urllib.parse
import pytz  # Para la zona horaria

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="Asisvem PRO", layout="wide", page_icon="🏢")

# Zona Horaria Colombia
ZONA_HORARIA = pytz.timezone('America/Bogota')

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
        try:
            return pd.read_csv(file)
        except:
            return pd.DataFrame(columns=["Fecha_Gestion", "Cliente", "Referencia"])
    return pd.DataFrame(columns=["Fecha_Gestion", "Cliente", "Referencia"])

# --- 4. INTERFAZ DE ACCESO ---
if not st.session_state.get("authentication_status"):
    tab_login, tab_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Solicitar Acceso"])
    with tab_login:
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
    logo_user = credentials["usernames"][user_id].get("logo", "Logo Asisvem 2022 PNG (1).png")
    
    HISTORIAL_FILE = f"historial_{user_id}.csv" 
    MSG_FILE = f"mensaje_{user_id}.txt"
    
    # Cargar mensaje guardado
    if not os.path.exists(MSG_FILE):
        with open(MSG_FILE, "w", encoding="utf-8") as f: f.write("Hola {nombre}, recordarte que tu {detalle} para {referencia} vence el {fecha}.")
    
    with open(MSG_FILE, "r", encoding="utf-8") as f: 
        msg_cargado = f.read()
    
    if 'mensaje_personalizado' not in st.session_state:
        st.session_state.mensaje_personalizado = msg_cargado

    # --- BARRA LATERAL ---
    with st.sidebar:
        try: st.image(logo_user, use_container_width=True)
        except: st.image("Logo Asisvem 2022 PNG (1).png", use_container_width=True)
            
        st.write(f"### Bienvenid@, {st.session_state['name']}")
        authenticator.logout('Cerrar Sesión', 'sidebar')
        st.divider()
        
        uploaded_file = st.file_uploader("1. Cargar Base Excel (.xlsx)", type=["xlsx"])
        
        # NUEVO: CARGAR RESPALDO CSV
        restore_file = st.file_uploader("2. Cargar Respaldo Historial (Opcional)", type=["csv"])
        if restore_file:
            respaldo = pd.read_csv(restore_file)
            respaldo.to_csv(HISTORIAL_FILE, index=False)
            st.success("Historial recuperado")
            
        dias_margen = st.slider("Días de anticipación", 1, 60, 8)
        st.divider()
        
        # NUEVO: BOTÓN DESCARGAR RESPALDO
        hist_actual = leer_historial(HISTORIAL_FILE)
        if not hist_actual.empty:
            csv_data = hist_actual.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Respaldo CSV", data=csv_data, file_name=f"respaldo_{user_id}.csv", mime="text/csv", use_container_width=True)
        
        with st.expander("📊 Historial Rápido"):
            st.dataframe(hist_actual, hide_index=True)
            
        st.markdown("<br>" * 2, unsafe_allow_html=True)
        st.caption("**Soporte Técnico**")
        st.caption("gerencia@asisvem.com")

    # --- PESTAÑAS PRINCIPALES ---
    tabs_principales = st.tabs(["📖 Configuración", "🔔 Gestión de Alertas", "✅ Gestionados"])

    with tabs_principales[0]:
        col_m, col_c = st.columns([2, 1])
        with col_m:
            st.header("📘 Instrucciones Rápidas")
            st.markdown("""
            1. Sube tu **Excel** con las columnas: Nombre, Celular, Fecha, Referencia, Detalle.
            2. Usa **WhatsApp** para avisar a tus clientes.
            3. Haz clic en **Marcar ✔️** para guardar la gestión.
            4. **IMPORTANTE:** Al final del día descarga tu respaldo en la barra izquierda. Si la página se reinicia, vuelve a subir ese archivo en el paso 2 de la barra lateral.
            """)
            
        with col_c:
            st.subheader("⚙️ Mensaje Personalizado")
            nuevo_msg = st.text_area("Editar cuerpo:", value=st.session_state.mensaje_personalizado, height=200)
            if st.button("💾 Guardar Mensaje"):
                with open(MSG_FILE, "w", encoding="utf-8") as f: f.write(nuevo_msg)
                st.session_state.mensaje_personalizado = nuevo_msg
                st.success("Guardado")

    with tabs_principales[1]:
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            if not all(c in df.columns for c in ["Nombre", "Celular", "Fecha", "Referencia", "Detalle"]):
                st.error("⚠️ Columnas incorrectas en el Excel.")
            else:
                df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
                historial = leer_historial(HISTORIAL_FILE)
                hoy = datetime.now(ZONA_HORARIA).date()
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
                        texto = st.session_state.mensaje_personalizado.format(nombre=row['Nombre'], referencia=row['Referencia'], detalle=row['Detalle'], fecha=row['Fecha'])
                        url = f"https://api.whatsapp.com/send?phone={num}&text={urllib.parse.quote(texto)}"
                        c2.link_button("🚀 WhatsApp", url, use_container_width=True)
                        
                        if c3.button("Marcar ✔️", key=f"p_{idx}", use_container_width=True):
                            # Hora de gestión con zona horaria correcta
                            hora_act = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M")
                            nueva_g = pd.DataFrame([{"Fecha_Gestion": hora_act, "Cliente": row['Nombre'], "Referencia": row['Referencia']}])
                            pd.concat([historial, nueva_g]).to_csv(HISTORIAL_FILE, index=False)
                            st.rerun()
        else:
            st.warning("👈 Carga un archivo Excel para comenzar.")

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
