# interfaz_TaxBridge.py - Chat de Consultas Tributarias EC-PE
import streamlit as st
import time
import os
from servicios_TaxBridge import consultar_tributario, PAISES, consultar_ruc_ecuador, consultar_ruc_peru

st.set_page_config(
    page_title="TaxBridge - Consultas Tributarias EC-PE",
    page_icon="📊",
    layout="centered"
)

st.title("📊 TaxBridge - Consultas Tributarias EC-PE")
st.markdown("""
**Asesor tributario, laboral y societario** para Ecuador y Perú.
Ingresa el RUC de tu empresa para respuestas personalizadas.
""")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selector de país
    pais = st.selectbox(
        "Selecciona el país:",
        options=list(PAISES.keys()),
        format_func=lambda x: PAISES[x]["nombre_pais"]
    )
    
    st.divider()
    
    # --- Campo RUC con validación dinámica según país ---
    st.subheader("🏢 Datos de tu empresa")
    
    # Determinar longitud esperada y placeholder según país
    if pais == "ecuador":
        longitud_esperada = 13
        placeholder_ruc = "Ej: 1791994191001"
    elif pais == "peru":
        longitud_esperada = 11
        placeholder_ruc = "Ej: 20607531600"
    else:
        longitud_esperada = 0
        placeholder_ruc = "Ingresa RUC"
    
    ruc_input = st.text_input(
        "RUC:",
        placeholder=placeholder_ruc,
        max_chars=longitud_esperada,
        help=f"Ingresa el RUC de tu empresa ({longitud_esperada} dígitos)."
    )
    
    # --- Mostrar información del RUC en la barra lateral ---
    if ruc_input:
        # Validar longitud y que sean solo números
        if len(ruc_input) == longitud_esperada and ruc_input.isdigit():
            with st.spinner("Consultando RUC..."):
                if pais == "ecuador":
                    datos = consultar_ruc_ecuador(ruc_input)
                elif pais == "peru":
                    # Ahora la API no necesita token obligatorio
                    PERU_API_TOKEN = os.getenv("PERU_API_TOKEN")
                    datos = consultar_ruc_peru(ruc_input, PERU_API_TOKEN)
                    if not datos.get("exito"):
                        # Si falla, mostrar mensaje más amigable
                        if "No se pudo obtener" in datos.get("error", ""):
                            datos["error"] = "No se pudo obtener información del RUC. Verifica que sea correcto."
                else:
                    datos = {"exito": False, "error": "País no soportado"}
                
                if datos and datos.get("exito"):
                    st.success("✅ RUC encontrado")
                    st.write(f"**Razón Social:** {datos.get('razon_social', 'No disponible')}")
                    
                    # Mostrar estado con color
                    estado = datos.get('estado', 'No disponible')
                    if estado.upper() == "ACTIVO":
                        st.success(f"**Estado:** ✅ {estado}")
                    elif estado.upper() == "SUSPENDIDO":
                        st.error(f"**Estado:** ⛔ {estado}")
                    else:
                        st.write(f"**Estado:** {estado}")
                    
                    st.write(f"**Tipo:** {datos.get('tipo', 'No disponible')}")
                    st.write(f"**Régimen:** {datos.get('regimen', 'No disponible')}")
                    
                    # Campos específicos de Ecuador
                    if pais == "ecuador":
                        st.write(f"**Obligado a contabilidad:** {datos.get('obligado_contabilidad', 'No disponible')}")
                        st.write(f"**Agente de Retención:** {datos.get('agente_retencion', 'No disponible')}")
                        st.write(f"**Contribuyente Especial:** {datos.get('contribuyente_especial', 'No disponible')}")
                    
                    st.session_state.datos_empresa = datos
                else:
                    st.error(f"❌ {datos.get('error', 'Error desconocido')}")
                    st.session_state.datos_empresa = None
        else:
            st.warning(f"⚠️ Ingresa {longitud_esperada} dígitos numéricos")
            st.session_state.datos_empresa = None
    else:
        st.session_state.datos_empresa = None
    
    st.divider()
    
    # Mostrar información del país
    st.subheader(f"ℹ️ {PAISES[pais]['nombre_pais']}")
    st.write(f"**Entidad:** {PAISES[pais]['entidad_rectora']}")
    st.write(f"**Sitio oficial:** [{PAISES[pais]['url_oficial']}]({PAISES[pais]['url_oficial']})")
    
    st.divider()
    st.caption("🤖 Motor de IA: **Mistral** (temperatura 0.1)")
    st.caption("📊 Tasas actualizadas manualmente desde fuentes oficiales")

# ==================== INICIALIZAR HISTORIAL ====================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"¡Hola! Soy tu asesor tributario, laboral y societario para {PAISES[pais]['nombre_pais']}. ¿En qué puedo ayudarte hoy?"
        }
    ]

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==================== EFECTO MÁQUINA DE ESCRIBIR ====================
def stream_response(texto, delay=0.02):
    for char in texto:
        yield char
        time.sleep(delay)

# ==================== INPUT DEL USUARIO ====================
if pregunta := st.chat_input("Escribe tu consulta aquí..."):
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)
    
    # Generar respuesta
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # Pasar el RUC solo si es válido
            ruc_valido = None
            if ruc_input and len(ruc_input) == longitud_esperada and ruc_input.isdigit():
                ruc_valido = ruc_input.strip()
            
            resultado = consultar_tributario(
                pregunta=pregunta,
                pais=pais,
                ruc_empresa=ruc_valido,
                temperatura=0.1
            )
            
            if resultado.get("exito") and resultado["respuesta"]["exito"]:
                respuesta_texto = resultado["respuesta"]["respuesta"]
                tiempo_ms = resultado["respuesta"]["tiempo_ms"]
                tasa_usada = resultado.get("tasa_utilizada", "No disponible")
                fuente_tasa = resultado.get("fuente_tasa", "")
                
                # --- INFO DE EMPRESA (desde datos consultados) ---
                info_empresa = ""
                datos_emp = resultado.get("datos_empresa")
                if datos_emp and datos_emp.get("exito"):
                    info_empresa = f"""
🏢 **Empresa:** {datos_emp.get('razon_social', 'No disponible')}
📌 **RUC:** {datos_emp.get('ruc', 'No disponible')}
📋 **Estado:** {datos_emp.get('estado', 'No disponible')}
📋 **Tipo:** {datos_emp.get('tipo', 'No disponible')}
📋 **Régimen:** {datos_emp.get('regimen', 'No disponible')}
"""
                    # Campos específicos de Ecuador
                    if pais == "ecuador":
                        info_empresa += f"""
📊 **Obligado a contabilidad:** {datos_emp.get('obligado_contabilidad', 'No disponible')}
🔄 **Agente de Retención:** {datos_emp.get('agente_retencion', 'No disponible')}
⭐ **Contribuyente Especial:** {datos_emp.get('contribuyente_especial', 'No disponible')}
"""
                elif ruc_input:
                    info_empresa = f"📌 **RUC ingresado:** {ruc_input} (No se pudo obtener información)"
                
                # --- INFO DE PROVEEDORES (si existen) ---
                info_proveedores = ""
                datos_prov = resultado.get("datos_proveedores")
                if datos_prov:
                    info_proveedores = "\n📌 **Proveedores detectados:**\n"
                    for ruc, data in datos_prov.items():
                        if data.get("exito"):
                            info_proveedores += f"- **{data.get('razon_social', 'No disponible')}** (RUC: {ruc}) - {data.get('tipo', 'Tipo no disponible')}\n"
                        else:
                            info_proveedores += f"- RUC: {ruc} (No se pudo obtener información)\n"
                
                # --- Construir respuesta completa ---
                texto_completo = respuesta_texto
                texto_completo += f"\n\n⏱️ *Tiempo de respuesta: {tiempo_ms} ms*"
                if tasa_usada:
                    texto_completo += f"\n\n📊 *Tasa utilizada: {tasa_usada}*"
                if info_empresa:
                    texto_completo += f"\n\n{info_empresa}"
                if info_proveedores:
                    texto_completo += f"\n\n{info_proveedores}"
                
                # Mostrar con efecto máquina de escribir
                placeholder.write_stream(stream_response(texto_completo, delay=0.02))
                
                # Guardar en historial (solo respuesta principal)
                st.session_state.messages.append(
                    {"role": "assistant", "content": respuesta_texto}
                )
                
            else:
                error_msg = resultado.get("error") or resultado["respuesta"].get("error", "Error desconocido")
                placeholder.error(f"❌ Error: {error_msg}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Lo siento, ocurrió un error: {error_msg}"}
                )
                
        except Exception as e:
            placeholder.error(f"❌ Error inesperado: {str(e)}")
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Lo siento, ocurrió un error inesperado: {str(e)}"}
            )
