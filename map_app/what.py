from selenium import webdriver
from selenium.webdriver.edge.service import Service
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import psycopg2
from psycopg2 import Error
from concurrent.futures import ThreadPoolExecutor
import re
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import DATABASE

# Configuración de la conexión a PostgreSQL (ajusta estos valores según tu base de datos)

#   f'postgresql://{DATABASE["user"]}:{DATABASE["password"]}@{DATABASE["host"]}:{DATABASE["port"]}/{DATABASE["database"]}'
print(DATABASE["host"])
DB_PARAMS = {
    "dbname": DATABASE["database"],
    "user": DATABASE["user"],
    "password": DATABASE["password"],
    "host": DATABASE["host"],
    "port": int(DATABASE["port"])
}

# Conectar a la base de datos y crear la tabla si no existe
def init_db():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket VARCHAR(50) PRIMARY KEY,
                folio VARCHAR(100),
                cuenta TEXT,
                tarea TEXT,
                usuario VARCHAR(100),
                error TEXT,
                texto TEXT,
                fecha_proceso TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Base de datos inicializada correctamente.")
    except Error as e:
        print(f"Error al conectar o crear tabla: {e}")

# Inicializar la base al inicio
init_db()

driver = webdriver.Edge()
driver.get("https://web.whatsapp.com/")
try:
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-tab="6"]'))
    )
except Exception as e:
    print(f"Error: {e}")

def mcompleto(mmen):
    try:
        lee = mmen.find_element(By.XPATH, './/div[@role="button" and contains(.,"Leer más")]')
        driver.execute_script("arguments[0].click();", lee)
        WebDriverWait(driver, 2).until(EC.invisibility_of_element_located((By.XPATH, './/div[@role="button" and contains(.,"Leer más")]')))

    except:
        pass
    full_text = mmen.find_element(By.CSS_SELECTOR, 'div.copyable-text').text
    return full_text

def guardar_en_db(datos):
    """Guarda o actualiza los datos en la base de datos PostgreSQL"""
    print(datos)
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Insertar o actualizar (UPSERT) usando ON CONFLICT
        query = """
            INSERT INTO tickets (ticket, folio, cuenta, tarea, usuario, error,texto, fecha_proceso)
            VALUES (%s, %s, %s, %s, %s, %s, %s,%s)
            ON CONFLICT (ticket) 
            DO UPDATE SET
                folio = EXCLUDED.folio,
                cuenta = EXCLUDED.cuenta,
                tarea = EXCLUDED.tarea,
                usuario = EXCLUDED.usuario,
                error = EXCLUDED.error,
                texto = EXCLUDED.texto,
                fecha_proceso = EXCLUDED.fecha_proceso;
        """
        valores = (
            datos.get('Ticket'),
            datos.get('Folio'),
            datos.get('Cuenta'),
            datos.get('Tarea'),
            datos.get('Usuario'),
            datos.get('Error'),
            datos.get('Texto'),
            datos.get('Fecha_Proceso')
        )
        cur.execute(query, valores)
        conn.commit()
        print(f"Datos guardados/actualizados para ticket: {datos.get('Ticket')}")
        
    except Error as e:
        print(f"Error al guardar en la base de datos: {e}")
    finally:
        cur.close()
        conn.close()

def ticket_ya_procesado(ticket):
    """Verifica si un ticket ya está en la base de datos"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM tickets WHERE ticket = %s;", (ticket,))
        existe = cur.fetchone() is not None
        cur.close()
        conn.close()
        return existe
    except Error as e:
        print(f"Error al consultar la base: {e}")
        return False

def procesar_ticket(inf):
    """Controla la lógica de tickets únicos consultando la base"""
    ticket = inf.get('Ticket')
    if ticket:
        if not ticket_ya_procesado(ticket):
            # Agregar marca de tiempo
            inf['Fecha_Proceso'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Guardar en la base de datos
            #print(inf)
            guardar_en_db(inf)
            print(f"Nuevo ticket procesado: {ticket}")
        else:
            print(f"Ticket {ticket} ya fue procesado anteriormente")

def limpia(text):
    return ' '.join(text.replace('\n', '  ').split())

def extrae_inf(text):

    patrones = {
        'Ticket': r'Ticket#(\d+)',
        'Folio': r'FOLIO A TRABAJAR:\s*([^\n]+)',
        'Cuenta': r'CUENTA:\s*(.*?)(?=\s*TAREA:|\nTAREA:|$)',
        'Tarea': r'TAREA:\s*(.*?)(?=\s*USUARIO:|\nUSUARIO:|$)',
        'Usuario': r'USUARIO:\s*([^\n\(]+)',
        'Error': r'ERROR:\s*([\s\S]*?)(?=\nÁREA SOLICITANTE:|$)'
    }
    resultados = {}
    for campo, patron in patrones.items():
        match = re.search(patron, text)
        if match:
            valor = limpia(match.group(1))
            resultados[campo] = valor
        else:
            resultados[campo] = None
    resultados['Texto']=text
    return resultados

def read_last_message1():
    try:
        chat_title = 'Dey'
        chat = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'//span[@title="{chat_title}"]')))
        chat.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.message-in, div.message-out')))
        messages = driver.find_elements(By.CSS_SELECTOR, 'div.message-in, div.message-out')
        if messages:
            last_message = messages[-1]
            full_text = mcompleto(last_message)
            inf = extrae_inf(full_text)
            procesar_ticket(inf)
        else:
            print("No hay mensajes en el chat.")
    except Exception:
        print(f" ")

def worker(executor):
    while True:
        executor.submit(read_last_message1())
        time.sleep(20)

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.submit(worker, executor)
    while True:
        time.sleep(20)
