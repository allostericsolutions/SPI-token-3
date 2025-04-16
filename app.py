import streamlit as st
import os
import re
import pandas as pd
import dns.resolver  # AÑADIDO: Para validar dominios con registros MX

# CSS para imagen de fondo en la barra lateral
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-image: url("https://storage.googleapis.com/allostericsolutionsr/Allosteric_Solutions.png");
        background-repeat: no-repeat;
        background-position: center;
        background-size: 64% auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Función para cargar claves desde archivos de texto
def cargar_claves(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r') as archivo:
            return archivo.read().splitlines()
    return []

# Cargar listas de claves desde archivos
claves_muestra = cargar_claves('muestra_claves/muestra.txt')
claves_completo = cargar_claves('completo_claves/completo.txt')

# Códigos de autorización
AUTORIZACION_VALIDA = "echosonomovil&%$#"

# Cargar registros desde archivos CSV
def cargar_registros(tipo):
    archivo = f'registros_{tipo}.csv'
    if os.path.isfile(archivo):
        return pd.read_csv(archivo).to_dict(orient='records')
    return []

# Guardar registros en archivos CSV
def guardar_registro_csv(tipo, registro):
    archivo = f'registros_{tipo}.csv'
    df_nuevo = pd.DataFrame([registro])
    if not os.path.isfile(archivo):
        df_nuevo.to_csv(archivo, index=False)
    else:
        df_nuevo.to_csv(archivo, mode='a', header=False, index=False)

# Inicializar registros en la sesión
if "registros_muestra" not in st.session_state:
    st.session_state.registros_muestra = cargar_registros('muestra')

if "registros_completo" not in st.session_state:
    st.session_state.registros_completo = cargar_registros('completo')

# Indexación de claves
def siguiente_clave(tipo_examen):
    if tipo_examen == 'Muestra':
        registros = st.session_state.registros_muestra
        claves = claves_muestra
    else:
        registros = st.session_state.registros_completo
        claves = claves_completo

    return claves[len(registros) % len(claves)]

# Validación de email y dominio
def es_email_valido(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def dominio_existe(correo):
    try:
        # Extraer el dominio del correo
        dominio = correo.split('@')[1]
        # Verificar registros MX del dominio
        registros_mx = dns.resolver.resolve(dominio, 'MX')
        return True if registros_mx else False
    except Exception as e:
        return False

def es_nombre_valido(nombre):
    return bool(re.match(r"^[A-Za-z\s]+$", nombre))

# Guardar en sesión y archivo
def guardar_registro(email, nombre, clave, tipo_examen, codigo_autorizacion=None):
    registro = {
        'Email': email,
        'Nombre': nombre,
        'ClaveAsignada': clave,
        'TipoExamen': tipo_examen
    }

    if tipo_examen == 'Completo':
        registro['CodigoAutorizacion'] = codigo_autorizacion
        st.session_state.registros_completo.append(registro)
        guardar_registro_csv('completo', registro)
    else:
        st.session_state.registros_muestra.append(registro)
        guardar_registro_csv('muestra', registro)

# Interfaz principal
st.sidebar.title("ARDMS TOKEN")
st.title("🔐 Token SPI ARDMS")

email_usuario = st.text_input("Introduce tu correo electrónico:")
nombre_usuario = st.text_input("Introduce tu nombre completo:")
tipo_examen = st.selectbox("Selecciona el tipo de examen:", ["Examen Muestra", "Examen Completo"])

if tipo_examen == "Examen Completo":
    codigo_autorizacion = st.text_input("Introduce el código de autorización:", type="password")

if st.button("Generar clave"):
    if es_email_valido(email_usuario) and dominio_existe(email_usuario) and es_nombre_valido(nombre_usuario):
        if tipo_examen == "Examen Completo" and codigo_autorizacion != AUTORIZACION_VALIDA:
            st.warning("Código de autorización inválido.")
        else:
            clave_asignada = siguiente_clave(tipo_examen.split()[1])
            guardar_registro(email_usuario, nombre_usuario, clave_asignada, tipo_examen.split()[1], codigo_autorizacion if tipo_examen == "Examen Completo" else None)
            st.success("Tu clave asignada es:")
            st.code(clave_asignada)
    else:
        if not es_email_valido(email_usuario) or not dominio_existe(email_usuario):
            st.warning("Por favor, introduce un correo con formato válido y dominio existente.")
        else:
            st.warning("Por favor, introduce un nombre válido.")

# Barra lateral protegida para admin
if "access_granted" not in st.session_state:
    st.session_state.access_granted = False

def autenticar_clave(contraseña):
    contraseña_correcta = "francisco14%"
    return contraseña == contraseña_correcta

clave_chronoshift = st.sidebar.text_input("ChronoShift:", type="password")

if st.sidebar.button("Acceder"):
    if autenticar_clave(clave_chronoshift):
        st.sidebar.success("Acceso concedido.")
        st.session_state.access_granted = True
    else:
        st.sidebar.error("🛑 Buen intento, aquí no, es allá ➡")

if st.session_state.access_granted:
    with st.sidebar.expander("ChronoShift Admi"):
        st.write("Registros Muestra")
        st.dataframe(st.session_state.registros_muestra)

        st.write("Registros Completo")
        st.dataframe(st.session_state.registros_completo)

        if st.button("Borrar registros"):
            os.remove('registros_muestra.csv') if os.path.exists('registros_muestra.csv') else None
            os.remove('registros_completo.csv') if os.path.exists('registros_completo.csv') else None
            st.session_state.registros_muestra.clear()
            st.session_state.registros_completo.clear()
            st.success("Se han borrado todos los registros.")
            st.experimental_rerun()

# Botón para acceder al examen
url_examen = "https://spiardmstest.streamlit.app"

if st.button("Acceder al examen"):
    st.markdown(f"[Haz clic aquí para ir al examen]({url_examen})", unsafe_allow_html=True)

# Leyenda
st.warning("Cada correo queda registrado, así como la IP para el uso del sistema. Monitoreamos el uso para prevenir abusos.")
