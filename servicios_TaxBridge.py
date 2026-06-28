# -*- coding: utf-8 -*-
"""
Servicios Tributarios - TaxBridge
Versión con API alternativa para Perú (sin token)
"""

import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime
import json
import re

# ==================== CONFIGURACIÓN ====================
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TIMEOUT = int(os.getenv("TIMEOUT", 30))

if not MISTRAL_API_KEY:
    raise ValueError("Falta MISTRAL_API_KEY en el archivo .env")

print("✅ Mistral inicializado correctamente")

# ==================== TASAS ACTUALIZADAS MANUALMENTE ====================
TASAS_OFICIALES = {
    "ecuador": {
        "tasa": "15%",
        "fecha_actualizacion": "2026-06-16",
        "fuente": "Circular SRI NAC-DGECCGC25-00000006 (26/12/2025) - Decreto Ejecutivo 470",
        "url_referencia": "https://www.sri.gob.ec",
        "nota": "Tasa confirmada para 2026 según Circular del SRI"
    },
    "peru": {
        "tasa": "18%",
        "fecha_actualizacion": "2026-06-16",
        "fuente": "Ley Nº 32387 - Tasa IGV 16% + IPM 2%",
        "url_referencia": "https://www.sunat.gob.pe",
        "nota": "Tasa vigente para 2026 (18% total: 16% IGV + 2% IPM)"
    }
}

# ==================== CONFIGURACIÓN DE PAÍSES ====================
PAISES = {
    "ecuador": {
        "nombre_pais": "Ecuador",
        "entidad_rectora": "SRI",
        "legislacion_base": "Código Tributario, LRTI",
        "impuestos_clave": "IVA (15%), IR, ISD, IAE",
        "url_oficial": "https://www.sri.gob.ec",
        "url_normativa": "https://www.sri.gob.ec"
    },
    "peru": {
        "nombre_pais": "Perú",
        "entidad_rectora": "SUNAT",
        "legislacion_base": "Código Tributario, Ley IR, Ley IGV",
        "impuestos_clave": "IGV (18%), IR, ITAN, ITF",
        "url_oficial": "https://www.sunat.gob.pe",
        "url_normativa": "https://www.sunat.gob.pe"
    }
}

# ==================== CONSULTA DE RUC (API) ====================
def consultar_ruc_ecuador(ruc):
    """
    Consulta la información completa de un RUC en Ecuador usando la API de CipherByte.
    """
    url = f"https://aggregator.cipherbyte.ec/company/{ruc}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "exito": True,
            "ruc": ruc,
            "razon_social": data.get("razonSocial") or data.get("nombre", "No disponible"),
            "estado": data.get("estado") or data.get("estadoContribuyente", "No disponible"),
            "tipo": data.get("tipo") or data.get("tipoContribuyente", "No disponible"),
            "regimen": data.get("regimen") or data.get("regimenTributario", "No disponible"),
            "obligado_contabilidad": data.get("obligadoContabilidad") or data.get("obligadoContable", "No disponible"),
            "agente_retencion": data.get("agenteRetencion") or data.get("agenteRetencionIVA", "No disponible"),
            "contribuyente_especial": data.get("contribuyenteEspecial") or data.get("contribuyenteEspecialIVA", "No disponible"),
            "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fuente": "CipherByte (SRI)"
        }
    except Exception as e:
        print(f"⚠️ Error al consultar RUC {ruc}: {e}")
        return {"exito": False, "error": str(e)}

# ==================== CONSULTA DE RUC PERÚ (SIN TOKEN) ====================
def consultar_ruc_peru(ruc, api_token=None):
    """
    Consulta la información de un RUC en Perú usando múltiples APIs gratuitas.
    NO requiere token de API.
    """
    # Intento 1: apis.net.pe (gratuita, sin token)
    try:
        url = f"https://api.apis.net.pe/v1/ruc?numero={ruc}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Verificar que los datos sean válidos
        if data.get("razonSocial") or data.get("nombre"):
            return {
                "exito": True,
                "ruc": ruc,
                "razon_social": data.get("razonSocial") or data.get("nombre", "No disponible"),
                "estado": data.get("estado", "No disponible"),
                "tipo": data.get("tipo", data.get("tipo_empresa", "No disponible")),
                "regimen": data.get("regimen", "No disponible"),
                "fuente": "apis.net.pe (gratuita)"
            }
    except Exception as e:
        print(f"⚠️ Error en API 1 (apis.net.pe): {e}")
    
    # Intento 2: ruc.com.pe (gratuita, sin token)
    try:
        url = f"https://ruc.com.pe/api/ruc/{ruc}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("nombre") or data.get("razon_social"):
            return {
                "exito": True,
                "ruc": ruc,
                "razon_social": data.get("nombre") or data.get("razon_social", "No disponible"),
                "estado": data.get("estado", "No disponible"),
                "tipo": data.get("tipo", "No disponible"),
                "regimen": data.get("regimen", "No disponible"),
                "fuente": "ruc.com.pe (gratuita)"
            }
    except Exception as e:
        print(f"⚠️ Error en API 2 (ruc.com.pe): {e}")
    
    # Intento 3: api.sunat.cloud (gratuita, sin token)
    try:
        url = f"https://api.sunat.cloud/ruc/{ruc}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("nombre") or data.get("razon_social"):
            return {
                "exito": True,
                "ruc": ruc,
                "razon_social": data.get("nombre") or data.get("razon_social", "No disponible"),
                "estado": data.get("estado", "No disponible"),
                "tipo": data.get("tipo", "No disponible"),
                "regimen": data.get("regimen", "No disponible"),
                "fuente": "api.sunat.cloud (gratuita)"
            }
    except Exception as e:
        print(f"⚠️ Error en API 3 (sunat.cloud): {e}")
    
    # Intento 4: PeruAPI (con token si existe)
    if api_token:
        try:
            url = f"https://peruapi.com/api/ruc/{ruc}?api_token={api_token}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("razon_social"):
                return {
                    "exito": True,
                    "ruc": ruc,
                    "razon_social": data.get("razon_social", "No disponible"),
                    "estado": data.get("estado", "No disponible"),
                    "tipo": data.get("tipo_empresa", "No disponible"),
                    "regimen": data.get("regimen", "No disponible"),
                    "fuente": "PeruAPI (con token)"
                }
        except Exception as e:
            print(f"⚠️ Error en API 4 (PeruAPI): {e}")
    
    # Si todo falla
    return {
        "exito": False,
        "error": "No se pudo obtener información del RUC. Verifica que sea correcto."
    }

# ==================== OBTENER TASA ====================
def obtener_tasa_actualizada(pais):
    config = TASAS_OFICIALES.get(pais)
    if not config:
        return "No disponible", "Fuente no disponible"
    tasa = config["tasa"]
    fuente = f"{config['fuente']} (Actualizado: {config['fecha_actualizacion']})"
    return tasa, fuente

# ==================== CONSTRUCCIÓN DE PROMPT ====================
def construir_prompt_consulta_tributaria(pregunta, pais, tasa_actualizada, url_tasa, datos_empresa, datos_proveedores):
    config = PAISES[pais]
    nombre_impuesto = "IVA" if pais == "ecuador" else "IGV"
    
    # --- Datos de la empresa consultante ---
    info_empresa = ""
    es_contribuyente_especial = False
    if datos_empresa and datos_empresa.get("exito"):
        es_contribuyente_especial = datos_empresa.get("contribuyente_especial") == "SI"
        info_empresa = f"""
EMPRESA CONSULTANTE:
- Razón Social: {datos_empresa.get('razon_social', 'No disponible')}
- RUC: {datos_empresa.get('ruc', 'No disponible')}
- Estado: {datos_empresa.get('estado', 'No disponible')}
- Tipo: {datos_empresa.get('tipo', 'No disponible')}
- Régimen: {datos_empresa.get('regimen', 'No disponible')}
- Obligado a llevar contabilidad: {datos_empresa.get('obligado_contabilidad', 'No disponible')}
- Agente de Retención: {datos_empresa.get('agente_retencion', 'No disponible')}
- Contribuyente Especial: {datos_empresa.get('contribuyente_especial', 'No disponible')}
"""
    
    # --- Datos de proveedores ---
    info_proveedores = ""
    if datos_proveedores:
        info_proveedores = "\nPROVEEDORES MENCIONADOS:\n"
        for ruc, data in datos_proveedores.items():
            if data.get("exito"):
                info_proveedores += f"""
RUC: {ruc}
- Razón Social: {data.get('razon_social', 'No disponible')}
- Estado: {data.get('estado', 'No disponible')}
- Tipo: {data.get('tipo', 'No disponible')}
- Régimen: {data.get('regimen', 'No disponible')}
- Obligado a contabilidad: {data.get('obligado_contabilidad', 'No disponible')}
- Agente de Retención: {data.get('agente_retencion', 'No disponible')}
"""
            else:
                info_proveedores += f"RUC: {ruc} - No se pudo obtener información: {data.get('error', 'Error desconocido')}\n"
    
    # --- Instrucciones específicas para retenciones (corregidas) ---
    instrucciones_retencion = ""
    if pais == "ecuador":
        instrucciones_retencion = f"""
**REGLAS ESPECÍFICAS PARA RETENCIONES EN ECUADOR:**

**1. Retención de IVA (Art. 11 LRTI, Resolución SRI NAC-DGERCGC20-00000045):**
- Proveedor PERSONA NATURAL NO OBLIGADA A CONTABILIDAD: retención del **100%** del IVA facturado.
- Proveedor PERSONA NATURAL OBLIGADA A CONTABILIDAD o SOCIEDAD: retención del **10%** del IVA facturado.
- Proveedor CONTRIBUYENTE ESPECIAL: NO se aplica retención de IVA (0%).
- Si la operación está exenta de IVA: NO se aplica retención.

**2. Retención de Impuesto a la Renta (IR) - Art. 39 LRTI:**
- Para arrendamiento de bienes inmuebles (locales, oficinas): **8%** sobre el valor del arriendo.
- Para otras operaciones, aplicar según la tabla de retenciones del SRI.

**3. Plazos de declaración:**
- Contribuyentes NO ESPECIALES: hasta el día **28** del mes siguiente al de la retención.
- Contribuyentes ESPECIALES: plazos establecidos en el **calendario tributario del SRI** (generalmente los **primeros 5 días hábiles** del mes).
- La empresa consultante {'ES' if es_contribuyente_especial else 'NO ES'} Contribuyente Especial, por lo que debe regirse por {'el calendario especial del SRI' if es_contribuyente_especial else 'el plazo general (día 28)'}.
"""
    
    prompt = f"""
Eres un asesor tributario, laboral y societario experto en {config['nombre_pais']} ({config['legislacion_base']}).

{info_empresa}

{info_proveedores}

DATOS OFICIALES ACTUALES (verificados al 16/06/2026):
- {nombre_impuesto}: {tasa_actualizada}
- Fuente: {url_tasa}

{instrucciones_retencion}

REGLAS GENERALES:
- Solo responder consultas tributarias, laborales (con SUNAFIL/IESS) o societarias.
- Si NO es tributaria, responde: "Gracias por utilizar este servicio, sin embargo no puedo contestar tu consulta, estoy diseñado solo para consultas tributarias, laborales y societarias"

CONSULTA: "{pregunta}"

INSTRUCCIONES PARA TU RESPUESTA:
1. Usa la tasa de {nombre_impuesto} proporcionada ({tasa_actualizada}).
2. Fundamenta en leyes de {config['nombre_pais']} (cita artículos).
3. Menciona a {config['entidad_rectora']}.
4. Si la consulta involucra retenciones, usa las reglas específicas detalladas arriba.
5. Sé claro y conciso. Usa viñetas.
6. Incluye plazos y montos (menciona los plazos especiales si el consultante es Contribuyente Especial).
7. Si no estás seguro, sugiere consultar a un contador.
8. Finaliza con: "🔗 Verifica en: {config['url_normativa']}"

Respuesta:
"""
    return prompt

# ==================== CONSULTA A MISTRAL ====================
def consultar_mistral(prompt, temperatura=0.1):
    inicio = time.time()
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperatura,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        if response.status_code == 200:
            resultado = response.json()
            contenido = resultado["choices"][0]["message"]["content"]
            return {
                "exito": True,
                "respuesta": contenido,
                "error": None,
                "tiempo_ms": tiempo_ms,
                "modelo": "Mistral"
            }
        else:
            return {
                "exito": False,
                "respuesta": None,
                "error": f"HTTP {response.status_code}",
                "tiempo_ms": tiempo_ms,
                "modelo": "Mistral"
            }
    except Exception as e:
        return {
            "exito": False,
            "respuesta": None,
            "error": str(e),
            "tiempo_ms": int((time.time() - inicio) * 1000),
            "modelo": "Mistral"
        }

# ==================== FUNCIÓN PRINCIPAL ====================
def consultar_tributario(pregunta, pais, ruc_empresa=None, temperatura=0.1):
    if pais not in PAISES:
        return {"exito": False, "error": f"País '{pais}' no válido"}
    
    if ruc_empresa:
        ruc_empresa = ruc_empresa.strip()
    
    # Detectar RUCs en la pregunta
    rucs_encontrados = re.findall(r'\b\d{13}\b', pregunta)
    print(f"🔍 RUCs encontrados: {rucs_encontrados}")
    
    datos_empresa = None
    datos_proveedores = {}
    
    if pais == "ecuador":
        if ruc_empresa:
            datos_empresa = consultar_ruc_ecuador(ruc_empresa)
            if datos_empresa.get("exito"):
                print(f"✅ Datos empresa: {datos_empresa['razon_social']}")
        
        for ruc in rucs_encontrados:
            if ruc_empresa and ruc == ruc_empresa:
                continue
            datos = consultar_ruc_ecuador(ruc)
            if datos.get("exito"):
                datos_proveedores[ruc] = datos
            else:
                datos_proveedores[ruc] = {"exito": False, "error": datos.get("error", "Error desconocido")}
    
    elif pais == "peru":
        # Obtener token de PeruAPI (opcional, solo si existe)
        PERU_API_TOKEN = os.getenv("PERU_API_TOKEN")
        
        if ruc_empresa:
            # Ahora consultar_ruc_peru no requiere token obligatorio
            datos_empresa = consultar_ruc_peru(ruc_empresa, PERU_API_TOKEN)
            if datos_empresa.get("exito"):
                print(f"✅ Datos empresa: {datos_empresa['razon_social']}")
            else:
                print(f"⚠️ Error consultando RUC empresa: {datos_empresa.get('error')}")
        
        # Detectar RUCs de Perú (11 dígitos)
        rucs_peru = re.findall(r'\b\d{11}\b', pregunta)
        for ruc in rucs_peru:
            if ruc_empresa and ruc == ruc_empresa:
                continue
            datos = consultar_ruc_peru(ruc, PERU_API_TOKEN)
            if datos.get("exito"):
                datos_proveedores[ruc] = datos
            else:
                datos_proveedores[ruc] = {"exito": False, "error": datos.get("error", "Error desconocido")}
    
    tasa_actualizada, url_tasa = obtener_tasa_actualizada(pais)
    
    prompt = construir_prompt_consulta_tributaria(
        pregunta, pais, tasa_actualizada, url_tasa,
        datos_empresa, datos_proveedores
    )
    
    respuesta = consultar_mistral(prompt, temperatura)
    
    return {
        "exito": True,
        "pais": pais,
        "configuracion_pais": PAISES[pais],
        "pregunta": pregunta,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tasa_utilizada": tasa_actualizada,
        "fuente_tasa": url_tasa,
        "datos_empresa": datos_empresa,
        "datos_proveedores": datos_proveedores,
        "respuesta": respuesta
    }
