import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime, timedelta
import os
import urllib.parse
import pytz 

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
        
        # PROCESO DE RESPALDO (Sin bucles infinitos)
        restore_file = st.file_uploader("2. Cargar Respaldo Historial (.csv)", type=["csv"])
        if restore_file:
            if "last_loaded_restore" not in st.session_state or st.session_state.last_loaded_restore != restore_file.name:
                df_restore = pd.read_csv(restore_file)
                df_restore.to_csv(HISTORIAL_FILE, index=False)
                st.session_state.last_loaded_restore = restore_file.name
                st.success("✅ Historial Cargado")
                st.rerun()
            
        dias_margen = st.slider("Días de anticipación", 1, 60, 8)
        st.divider()
        
        hist_actual = leer_historial(HISTORIAL_FILE)
        if not hist_actual.empty:
            csv_data = hist_actual.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Respaldo CSV", data=csv_data, file_name=f"respaldo_{user_id}.csv", mime="text/csv", use_container_width=True)
        
        with st.expander("📊 Historial Rápido"):
            st.dataframe(hist_actual, hide_index=True)
            
        st.markdown("<br>" * 2, unsafe_allow_html=True)
        # --- LOGO ASISVEM ---
        st.image("Logo Asisvem 2022 PNG (1).png", width=120)
        st.caption("**Soporte Técnico** | gerencia@asisvem.com")

    # --- PESTAÑAS PRINCIPALES ---
    tabs_principales = st.tabs(["📖 Configuración", "🔔 Gestión de Alertas", "✅ Gestionados"])

    with tabs_principales[0]:
        col_m, col_c = st.columns([2, 1])
        with col_m:
            st.header("📘 Instrucciones Rápidas")
            st.markdown("""
            1. Sube tu archivo **Excel** asegurándote de que tenga este formato exacto:
            """)
            
            # --- TABLA DE FORMATO RESTAURADA ---
            df_ejemplo = pd.DataFrame({
                "Nombre": ["Quien recibe el mensaje", "Juan Perez"],
                "Celular": ["A dónde llega el mensaje", "3001234567"],
                "Fecha": ["Cuándo vence el beneficio, la cita o el producto", "2026-05-20"],
                "Referencia": ["El objeto principal", "Placa, Carro, Pan, Libro..."],
                "Detalle": ["El motivo del mensaje", "Mantenimiento, Descuento..."]
            })
            st.table(df_ejemplo)
            
            st.markdown("""
            2. Usa el botón de **WhatsApp** para enviar el recordatorio automático.
            3. Haz clic en **Marcar ✔️** para registrar la gestión y que no vuelva a aparecer en pendientes.
            4. **IMPORTANTE:** Descarga tu respaldo al finalizar tu jornada. Si la web se reinicia, súbelo en el **Paso 2** de la barra lateral para recuperar tus datos.
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
                st.error("⚠️ Columnas incorrectas. El Excel debe tener: Nombre, Celular, Fecha, Referencia, Detalle.")
            else:
                df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
                historial = leer_historial(HISTORIAL_FILE)
                hoy = datetime.now(ZONA_HORARIA).date()
                limite = hoy + timedelta(days=dias_margen)
                
                df_rango = df[(df["Fecha"] >= hoy) & (df["Fecha"] <= limite)]
                gestionados_list = historial["Referencia"].astype(str).tolist()
                
                busq = st.text_input("🔍 Buscar cliente o placa/referencia:").upper()
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
                            hist_actualizar = leer_historial(HISTORIAL_FILE)
                            hora_act = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M")
                            nueva_g = pd.DataFrame([{"Fecha_Gestion": hora_act, "Cliente": row['Nombre'], "Referencia": row['Referencia']}])
                            df_final = pd.concat([hist_actualizar, nueva_g])
                            df_final.to_csv(HISTORIAL_FILE, index=False)
                            st.rerun()
        else:
            st.warning("👈 Carga un archivo Excel para comenzar.")

    with tabs_principales[2]:
        if uploaded_file:
            historial_view = leer_historial(HISTORIAL_FILE)
            avisados = historial_view[historial_view["Referencia"].astype(str).isin(df_rango["Referencia"].astype(str))]
            for idx, row in avisados.iterrows():
                with st.container(border=True):
                    ca, cb = st.columns([4, 1])
                    ca.write(f"✅ {row['Cliente']} ({row['Referencia']})")
                    ca.caption(f"Gestionado el: {row['Fecha_Gestion']}")
                    if cb.button("Deshacer", key=f"d_{idx}"):
                        h_edit = leer_historial(HISTORIAL_FILE)
                        h_edit = h_edit[h_edit["Referencia"].astype(str) != str(row['Referencia'])]
                        h_edit.to_csv(HISTORIAL_FILE, index=False)
                        st.rerun()
