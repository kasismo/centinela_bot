import os 
from datetime import datetime
from dotenv import load_dotenv

# --- CORE WEB  Y BASE DE DATOS ---
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import time
import threading
from flask import render_template_string # Cambiá tu import de Flask para incluir esta

# --- INTEGRACIONES EXTERNAS ---
from twilio.rest import Client
from groq import Groq

# --- MOTOR DE TESTEO UI (El navegador fantasma) ---
from playwright.sync_api import sync_playwright

# ==============================================
# 1. CONFIGURACIÓN DEL ENTORNO E INFRAESTRUCTURA
# ==============================================

# Cargamos las variables ocultas desde el archivo .env
load_dotenv()

# Validación estricta e infraestructura (Fail-Fast)
# El sistema no arranca si falta alguna llave maestra.
claves_requeridas = [
    'SUPABASE_URI',
    'GROQ_API_KEY',
    'TWILIO_ACCOUNT_SID',
    'TWILIO_AUTH_TOKEN',
    'TWILIO_WHATSAPP_FROM',
    'MY_WHATSAPP_TO'
]

for clave in claves_requeridas:
    if not os.getenv(clave):
        raise ValueError(f"⚠️ ¡Error Crítico de Infraestructura! Falta configurar la variable {clave}")


# =========================================
# 2. INICIALIZACIÓN DE CLIENTES Y SERVICIOS
# =========================================

# Levantamos el servidor web Flask
app = Flask(__name__)

# Conectamos con PostgreSQL (Supabase)
URI_BD = os.getenv('SUPABASE_URI')
engine = create_engine(str(URI_BD))

# Iniciamos el cerebro analítico (Groq)
cliente_groq = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Iniciamos el motor de mensajería (Twilio)
cliente_twilio = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

print("✅ [CENTINELA] Cimientos de infraestructura inicializados con éxito. Sistema en línea.")

# ==========================================
# 3. MOTOR DE MONITOREO Y TESTEO (PINGER)
# ==========================================

def inspeccionar_aplicacion(nombre_app, url):
    """
    Levanta un navegador invisible, visita la app y diagnostica su estado.
    Incluye protocolo de reanimación autónomo blindado contra falsos positivos.
    """
    print(f"\n🔍 [CENTINELA] Desplegando navegador fantasma para inspeccionar: {nombre_app}")
    
    # Iniciamos el motor de Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        estado_detectado = "Desconocido"
        html_crudo = ""
        
        try:
            print(f"   🌐 Conectando a {url} ...")
            # Navegamos a la app con un tiempo límite de 15 segundos
            respuesta = page.goto(url, timeout=15000)
            
            # Dejamos que el JavaScript de Streamlit cargue y renderice
            page.wait_for_timeout(3000) 
            
            # Capturamos el código fuente final y el código HTTP
            html_crudo = page.content()
            status_code = respuesta.status if respuesta else 500
            
            # ==========================================
            # LÓGICA DE DETECCIÓN Y DIAGNÓSTICO
            # ==========================================
            
            # 1. CONTROL DE ERRORES HTTP CRÍTICOS
            if status_code != 200:
                estado_detectado = f"Error HTTP {status_code}"
                print(f"   ❌ [ALERTA] La página devolvió error {status_code}.")
                
            # 2. DETECCIÓN DE PANTALLA DORMIDA (Validación Estricta)
            elif "Yes, get this app back up!" in html_crudo or "due to inactivity" in html_crudo:
                print(f"   ⚠️ [DETECTADO] {nombre_app} está DORMIDA. Iniciando protocolo de reanimación...")
                
                # Buscamos el botón interactivo de Streamlit
                boton_wake_up = page.locator("text=Yes, get this app back up!")
                
                if boton_wake_up.is_visible():
                    print("   ⚡ [PLAYWRIGHT] Presionando el botón 'Wake up' automáticamente...")
                    boton_wake_up.click()
                    
                    # Los contenedores de la nube tardan en bootear, esperamos 12 segundos clavados
                    print("   ⏳ Esperando 12 segundos a que la nube levante el contenedor...")
                    page.wait_for_timeout(12000)
                    
                    # Volvemos a capturar el HTML para verificar si el re-arranque funcionó
                    html_post_click = page.content()
                    
                    if "due to inactivity" not in html_post_click:
                        estado_detectado = "Reanimada Exitosamente"
                        print(f"   💖 [ÉXITO] Aplicación {nombre_app} levantada de forma autónoma.")
                    else:
                        estado_detectado = "Dormida (Fallo Reanimación)"
                        print("   ❌ [FALLO] Se presionó el botón pero el contenedor no respondió.")
                else:
                    estado_detectado = "Dormida (Botón No Encontrado)"
                    print("   ❌ No se pudo encontrar el botón físico en la pantalla (¿Permisos privados?).")
            
            # 3. VERIFICACIÓN DE INTERFAZ ACTIVA (El Silencio de Radio)
            elif "Please wait" in html_crudo or "Iniciar" in html_crudo or "Login" in html_crudo or "Contraseña" in html_crudo:
                estado_detectado = "Activa"
                
            # 4. COMPORTAMIENTO NO RECONOCIDO
            else:
                estado_detectado = "Comportamiento Inesperado"
                
        except Exception as e:
            estado_detectado = "Caida (Timeout/Crash)"
            html_crudo = str(e)
            print(f"   🚨 [CRÍTICO] Error de acceso general: {e}")
            
        finally:
            # Siempre aseguramos cerrar el navegador invisible para liberar memoria RAM
            browser.close()
            
        return {
            "estado": estado_detectado,
            "html": html_crudo
        }

# ==========================================
# 4. MOTOR DE DIAGNÓSTICO IA Y ALERTAS
# ==========================================

def analizar_y_alertar(nombre_app, estado, html_crudo):
    """
    Se activa SOLO cuando hay un problema. Pide diagnóstico a Groq,
    manda el WhatsApp y guarda la evidencia en la BD.
    """
    print(f"\n🧠 [IA] Iniciando diagnóstico de {nombre_app}...")
    
    # 1. Le pasamos el contexto a Groq para que actúe como Ingeniero DevOps
    prompt = f"""
    Sos un Ingeniero SRE (Site Reliability Engineer) Senior. 
    Nuestra aplicación '{nombre_app}' acaba de fallar en producción.
    El scraper detectó el siguiente estado: {estado}.
    
    Si el estado es 'Dormida (Zzzz)', explicá brevemente que es el comportamiento normal de Streamlit Community Cloud por inactividad y que el Pinger ya la está despertando.
    Si es un Error HTTP o Caída, da una hipótesis técnica corta de qué pudo haber pasado.
    
    Sé conciso, directo y profesional. Máximo 4 líneas.
    """
    
    try:
        respuesta = cliente_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        diagnostico = respuesta.choices[0].message.content
        print(f"   ✅ Diagnóstico listo: {str(diagnostico)[:60]}...")
    except Exception as e:
        diagnostico = f"Falla en el motor de IA: {e}"
        print(f"   ❌ Error IA: {e}")

    # 2. Disparamos la alerta por WhatsApp vía Twilio
    print("📲 [TWILIO] Disparando alerta de WhatsApp...")
    mensaje_whatsapp = f"🚨 *ALERTA DEL CENTINELA* 🚨\n\n*App:* {nombre_app}\n*Estado:* {estado}\n\n*Diagnóstico SRE:*\n{diagnostico}"
    
    try:
        message = cliente_twilio.messages.create(
            from_=str(os.getenv('TWILIO_WHATSAPP_FROM') or ""),
            body=str(mensaje_whatsapp),
            to=str(os.getenv('MY_WHATSAPP_TO') or "")
        )
        print(f"   ✅ WhatsApp enviado exitosamente (SID: {message.sid})")
    except Exception as e:
        print(f"   ❌ Error al enviar WhatsApp. ¿Configuraste bien Twilio? Detalle: {e}")

    # 3. Persistencia: Guardamos el historial en PostgreSQL (Supabase)
    print("💾 [BD] Registrando incidente en PostgreSQL...")
    try:
        query = text("""
            INSERT INTO diagnosticos_ia (tipo_falla, analisis_groq, notificado_whatsapp)
            VALUES (:falla, :diagnostico, TRUE)
        """)
        with engine.begin() as conn:
            conn.execute(query, {"falla": estado, "diagnostico": diagnostico})
        print("   ✅ Incidente guardado en la base de datos de auditoría.")
    except Exception as e:
        print(f"   ⚠️ Error al guardar en BD (¿Creaste las tablas del script SQL?): {e}")


# ==========================================
# 5. EL ORQUESTADOR (Patrulla 24/7)
# ==========================================

# Tu catálogo de aplicaciones a monitorear
MIS_APLICACIONES = [
    {"nombre": "Virtual CRM", "url": "https://virtualcrm.streamlit.app/"},
    # Podés seguir sumando todas las que quieras...
]

def patrulla_infinita():
    """
    Controla el flujo de alertas basado en la respuesta inteligente del scraper.
    """
    print("\n🚁 [ORQUESTADOR] Hilo de patrullaje activo.")
    
    while True:
        for app in MIS_APLICACIONES:
            if "AQUI_" in app["url"]:
                continue
                
            resultado = inspeccionar_aplicacion(app["nombre"], app["url"])
            estado = resultado['estado']
            
            # FILTRO INTELIGENTE DE REACCIONES:
            if estado == "Activa":
                # Silencio absoluto, el sistema funciona bien
                continue
                
            elif estado == "Reanimada Exitosamente":
                # La app fallaba pero el script la arregló. Notificamos el éxito del bot.
                analizar_y_alertar(app["nombre"], "Dormida (Reparación Automática)", resultado['html'])
                
            elif estado in ["Error HTTP 404", "Caida (Timeout/Crash)", "Dormida (Fallo Reanimación)"]:
                # Problemas reales que requieren tu intervención humana inmediata
                analizar_y_alertar(app["nombre"], estado, resultado['html'])
                
            time.sleep(5) 
            
        print("\n💤 [ORQUESTADOR] Ronda finalizada. Próxima patrulla en 10 minutos...")
        time.sleep(600)

# ==========================================
# 6. DASHBOARD DE COMANDO (FLASK)
# ==========================================

# Un HTML simple incrustado para no tener que armar carpetas extra ahora mismo
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Centinela | Centro de Comando</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e1e2e; color: #cdd6f4; padding: 20px; }
        .card { background: #313244; padding: 15px; margin-bottom: 15px; border-left: 5px solid #f38ba8; border-radius: 5px; }
        h1 { color: #89b4fa; }
        .fecha { color: #a6adc8; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>🛡️ Centro de Comando: El Centinela</h1>
    <p>Historial de incidentes detectados en producción:</p>
    
    {% for incidente in incidentes %}
    <div class="card">
        <h3>Falla Detectada: {{ incidente.tipo_falla }}</h3>
        <p class="fecha">Fecha del registro: {{ incidente.fecha_incidente }}</p>
        <p><strong>Diagnóstico SRE:</strong> <br> {{ incidente.analisis_groq }}</p>
        <p><em>Notificado por WhatsApp: {% if incidente.notificado_whatsapp %}✅ Sí{% else %}❌ No{% endif %}</em></p>
    </div>
    {% else %}
    <div class="card" style="border-left-color: #a6e3a1;">
        <h3>🟢 Sistemas Operativos</h3>
        <p>No se registran incidentes en la base de datos.</p>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def panel_control():
    """
    Ruta principal de Flask. Consulta a PostgreSQL y renderiza la web.
    """
    try:
        query = text("SELECT tipo_falla, analisis_groq, notificado_whatsapp, fecha_incidente FROM diagnosticos_ia ORDER BY fecha_incidente DESC LIMIT 20")
        with engine.connect() as conn:
            resultados = conn.execute(query).fetchall()
            
        return render_template_string(HTML_DASHBOARD, incidentes=resultados)
    except Exception as e:
        return f"Error conectando a la base de datos de auditoría: {e}"

# ==========================================
# PUNTO DE IGNICIÓN (Preparado para la Nube)
# ==========================================
if __name__ == "__main__":
    # 1. Desprendemos el patrullero en un hilo paralelo (Background worker)
    hilo_scraper = threading.Thread(target=patrulla_infinita, daemon=True)
    hilo_scraper.start()
    
    # 2. Capturamos el puerto dinámico de Render (o 5000 en local)
    puerto = int(os.environ.get("PORT", 5000))
    
    # 3. Encendemos el servidor web Flask exponiéndolo hacia afuera
    print(f"🌐 [FLASK] Encendiendo Centro de Comando en el puerto {puerto}")
    app.run(host='0.0.0.0', port=puerto, debug=False, use_reloader=False)


