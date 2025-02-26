from selenium import webdriver
from selenium.webdriver.edge.service import Service
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime
import os
import glob
import shutil
from concurrent.futures import ThreadPoolExecutor
import re
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

driver = webdriver.Edge() 

driver.get("https://web.whatsapp.com/")
#time.sleep(20)  # Espera para que el usua
# Navega a WhatsApp Web
try:
    # Aumenta el tiempo de espera a 60 segundos
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-tab="6"]'))
    )
    #print("Elemento encontrado, puede continuar.")
except Exception as e:
    print(f"Error: {e}")

def mcompleto(mmen):
    try:
        lee=mmen.find_element(By.XPATH,' .//div[@role="button"   and contains(.,"Leer más")]')
        driver.execute_script("arguments[0].click();",lee)
        WebDriverWait(driver,2).until(EC.invisibility_of_element_located((By.XPATH,  './/div[@role="button"  and contains(.,"Leer  más"")]')))

    except:
        pass
    full_text=mmen.find_element(By.CSS_SELECTOR,  'div.copyable-text').text
    return full_text

tickets_procesados = set()

def guardar_en_excel(datos):
    """Guarda los datos en un archivo Excel, actualizando si ya existe"""
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    nombre_archivo = os.path.join(directorio_actual,'tickets.xlsx')
    
    try:
        # Leer archivo existente
        df_existente = pd.read_excel(nombre_archivo)
    except FileNotFoundError:
        # Crear nuevo DataFrame si el archivo no existe
        df_existente = pd.DataFrame()

    # Crear nuevo DataFrame con los datos actuales
    nuevo_df = pd.DataFrame([datos])
   
    df_final = pd.concat([df_existente, nuevo_df], ignore_index=True) 
    df_final = df_final.drop_duplicates(subset=['Ticket'], keep='last')
    
    # Guardar en Excel
    try:
        df_final.to_excel(nombre_archivo, index=False, engine='openpyxl')
        print(f"Datos guardados/actualizados en {nombre_archivo}")
    except Exception  as e:
        print(f"Error al guardar: {str(e)}")

def procesar_ticket(inf):
    """Controla la lógica de tickets únicos"""
    global tickets_procesados
    
    ticket = inf.get('Ticket')
    #print('jj',ticket)
    if ticket and ticket not in tickets_procesados:
        # Agregar marca de tiempo
        inf['Fecha_Proceso'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #print('ww')
        # Guardar en Excel
        guardar_en_excel(inf)
        
        # Agregar a registros procesados
        tickets_procesados.add(ticket)
        print(f"Nuevo ticket procesado: {ticket}")
    else:
        print(f"Ticket {ticket} ya fue procesado anteriormente")


#hasta aqui las modificaciobes 
def limpia(text):
    return ' '.join(text.replace('\n', '  ').split())

def extrae_inf(text):
    patrones = {
        'Ticket': r'Ticket#(\d+)',
        'Folio': r'FOLIO A TRABAJAR:\s*([^\n]+)',
        'Cuenta': r'CUENTA:\s*(.*?)(?=\s*TAREA:|\nTAREA:|$)',  # Modificado
        'Tarea': r'TAREA:\s*(.*?)(?=\s*USUARIO:|\nUSUARIO:|$)',  # Modificado
        'Usuario': r'USUARIO:\s*([^\n\(]+)',
        'Error': r'ERROR:\s*([\s\S]*?)(?=\nÁREA SOLICITANTE:|$)'  # Modificado para capturar multilínea
    }
    resultados = {}
    for campo, patron in patrones.items():
        match = re.search(patron, text)
        if match:
            valor=limpia(match.group(1))
            resultados[campo] = valor
        else:
            resultados[campo]=None
    
    return resultados   

def read_last_message1():
    
    try:
        # Encuentra el chat deseado (puedes ajustar el selector para encontrar el chat específico)
        chat_title = 'Dey'
        chat = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'//span[@title="{chat_title}"]')))
        chat.click()
        #print('hfh',chat)
        # Espera a que se carguen los mensajes
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.message-in, div.message-out')))
        # Encuentra los mensajes en el chat abierto y selecciona el último
        messages = driver.find_elements(By.CSS_SELECTOR, 'div.message-in, div.message-out')
        if messages:
            last_message = messages[-1]
            full_text=mcompleto(last_message)

            inf=extrae_inf(full_text)
            #print(inf)
            procesar_ticket(inf)

        else:
            print("No hay mensajes en el chat.")

    except Exception :
        print(f" ")

def worker(executor):
    while True:
        executor.submit(read_last_message1())
        time.sleep(20)

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.submit(worker, executor)
    
    while True:
        time.sleep(20)
