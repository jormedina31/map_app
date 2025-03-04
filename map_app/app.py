from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import create_engine, text
import geopandas as gpd
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import pandas as pd
#from dotenv import load_dotenv
from shapely.geometry import Polygon
import os
from config import DATABASE
import csv
import concurrent.futures
import time
from  sqlalchemy.pool   import QueuePool

from concurrent.futures  import ThreadPoolExecutor
#load_dotenv()
app = Flask(__name__)
#@app.route('/get_polygons')
app.secret_key = 'Finanzas2025'  # Cambia esto por una clave segura



DATABASE_URL = f'postgresql://{DATABASE["user"]}:{DATABASE["password"]}@{DATABASE["host"]}:{DATABASE["port"]}/{DATABASE["database"]}'

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800
)


engine_users = create_engine(
            f'postgresql://{DATABASE["user"]}:{DATABASE["password"]}@'
            f'{DATABASE["host"]}:{DATABASE["port"]}/{DATABASE["database"]}'
        )


# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    with engine_users.connect() as conn:
        result = conn.execute(text('SELECT * FROM users WHERE id = :id'), {'id': user_id}).fetchone()
        if result:
            return User(id=result[0], username=result[1])
    return None


#funcion para mostrar la informacio de los tickets
@app.route('/get_tickets')
@login_required
def get_tickets():
    try:
        engine = create_engine(
            f'postgresql://{DATABASE["user"]}:{DATABASE["password"]}@'
            f'{DATABASE["host"]}:{DATABASE["port"]}/{DATABASE["database"]}'
        )
        query = text(str('SELECT * FROM  public.tickets  ORDER BY fecha_proceso'))
        #query = text(str(query))  # Convierte la consulta a texto con parámetros nombrados
        
       
        dato = pd.read_sql(query, engine)
        print('tickets')
        print(dato)

        #df = pd.read_excel('tickets.xlsx')
        df = dato.where(pd.notnull(dato), None)
        print(df)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Rutas de autenticación
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with engine_users.connect() as conn:
            existing_user = conn.execute(text('SELECT * FROM users WHERE username = :username'), 
                                       {'username': username}).fetchone()
            if existing_user:
                flash('El nombre de usuario ya existe')
                return redirect(url_for('signup'))
            
            hashed_password = generate_password_hash(password)
            conn.execute(text('INSERT INTO users (username, password) VALUES (:username, :password)'),
                       {'username': username, 'password': hashed_password})
            conn.commit()
            flash('Registro exitoso. Por favor inicia sesión.')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with engine_users.connect() as conn:
            user = conn.execute(text('SELECT * FROM users WHERE username = :username'), 
                              {'username': username}).fetchone()
            if user and check_password_hash(user[2], password):
                user_obj = User(id=user[0], username=user[1])
                login_user(user_obj)
                return redirect(url_for('map'))
            else:
                flash('Credenciales incorrectas')
    return render_template('login.html')


#funcion que extrae la informacion del csv  o podria ser una  bas eede datos
@app.route('/datos')
def get_data():
    data = []
    with open('C:/Users/FinanzasCDMX/Downloads/ALVARO_OBREGON.csv', 'r') as file:

        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return jsonify(data)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('map'))

def get_datos(query, params=None):   # de prueva 
    try: 
        engine = create_engine(
            f'postgresql://{DATABASE["user"]}:{DATABASE["password"]}@'
            f'{DATABASE["host"]}:{DATABASE["port"]}/{DATABASE["database"]}'
        )
        
        # Usa text() para parámetros nombrados
        
        query = text(str(query))  # Convierte la consulta a texto con parámetros nombrados
        
        if params:
            # Ejecuta con parámetros nombrados directamente (sin modificar el query)
            dato = pd.read_sql(query, engine)
        else:
            dato = pd.read_sql(query, engine)
       
        return dato


    except Exception as e:
        print(f"Error al conectar con la base de datos: {str(e)}")
        print("Query que causó el error: " + str(query))
        return None

#funcion que ajusta los poligonos 
def ajustar_poligono(poligono):
    #seaplica un dezplazamiento
    delta_x=-0.00031179042002

    delta_y=0.00065862997603
    coordenadas = list(poligono.exterior.coords)
    coordenadas_ajustadas = [(x + delta_x, y + delta_y) for x, y in coordenadas]
    return Polygon(coordenadas_ajustadas)


def get_pol1(query, params=None):   # de prueva 
    try:
        query=text(str(query))
        with engine.connect() as conn:
            gdf=gpd.read_postgis(query,conn,params=params,geom_col='geometry')
            if gdf.crs is None:
                gdf=gdf.set_crs(epsg=4326)
            else:
                gdf=gdf.to_crs(epsg=4326)
            return  gdf
    except  Exception as e:
        print(f"error   en get_pol1:   {str(e)}")
        return  None
    
@app.route('/get_polygons')
def get_polygons():
    query =  """SELECT *, ST_AsText(geometry) as geom_text  FROM public.poligonos_alcaldias  WHERE geometry IS NOT NULL LIMIT 20""" # Reemplaza con tu tabla
    #query= """SELECT *, ST_AsText(geometry) as geom_text  FROM public.poligonos_alcaldias_cdmx  WHERE "NOMGEO"='Azcapotzalco'"""
    gdf = get_pol1(query)
    if gdf is not None:
        polyg=gdf.to_json()
        #print(polyg)
        return polyg,200
    else:
        return jsonify({"error": "No se pudieron obtener los datos de la base de datos"}), 500
#extrae los poligonos de las delegacions
@app.route('/get_delegacion')
def get_delegacion():
    delegacion=request.args.get('nombre',None)
    print(delegacion)
    #query = """SELECT *, ST_AsText(geometry) as geom_text  FROM public.poligonos_alcaldias_cdmx  WHERE "NOMGEO"= %(param_nombre)s """
    query = """SELECT *, ST_AsText(geometry) as geom_text  FROM public.poligonos_alcaldias_cdmx  WHERE "CVE_MUN" = :param_nombre"""
    gdf=get_pol1(query,params={"param_nombre":delegacion})
    #print(gdf)
    if gdf is not None and not gdf.empty:
        return gdf.to_json(),200
    else:
        return jsonify({"error":"no se encontro delegacion"}),404
    

def process_table(tabla, delegacion, claves, clave):
    try:
        query = text(f'''
            SELECT *, ST_AsText(geometry) as geom_text 
            FROM public."{tabla}" 
            WHERE {claves} = :clave
        ''')
        gdf = get_pol1(query, {'clave': clave})
        
        if not gdf.empty:
            gdf['geometry'] = gdf['geometry'].apply(ajustar_poligono)
            gdf['delegacion'] = delegacion
            gdf['manzana'] = 'mna'
            return gdf.to_json()
        return None
    except Exception as e:
        print(f"Error en tabla {tabla}: {str(e)}")
        return None




#funcion que busca los predios de forma global
@app.route('/buscar_predio_global')
def buscar_predio_global():
    TABLAS_PREDIOS={'rpred01':'Alvaro Obregon','rpred02':'Azcapotzalco','rpred03':'Benito Juarez',
                    'rpred04':'Coyoacan', 'rpred05':'Cuajimalpa','rpred06':'Cuauhtemoc',
                    'rpred07':'Gustavo A. Madero','rpred08':'Iztacalco','rpred09':'Iztapalapa',
                    'rpred10':'Magdalena Contreras','rpred11':'Miguel Hidalgo','rpred12':'Milpa Alta',
                    'rpred13':'Tlahuac','rpred14':'Tlalpan','rpred15':'Venustiano Carranza','rpred16':'Xochimilco'}
    TABLAS_CO={'rcontr01':'Alvaro Obregon','rcontr02':'Azcapotzalco','rcontr03':'Benito Juarez',
                    'rcontr04':'Coyoacan', 'rcontr05':'Cuajimalpa','rcontr06':'Cuauhtemoc',
                    'rcontr07':'Gustavo A. Madero','rcontr08':'Iztacalco','rcontr09':'Iztapalapa',
                    'rcontr10':'Magdalena Contreras','rcontr11':'Miguel Hidalgo','rcontr12':'Milpa Alta',
                    'rcontr13':'Tlahuac','rcontr14':'Tlalpan','rcontr15':'Venustiano Carranza','rcontr16':'Xochimilco'}
    clave=request.args.get('clave')
    pc=request.args.get('pc')
    
    if (pc=='predio'):
        tablas=TABLAS_PREDIOS
        claves='clave'
    else:
        tablas=TABLAS_CO
        claves='idpredio'
    i=time.time()

    #inicio=time.time()
    print(clave,pc)
    query_parts = [
        f"(SELECT *, ST_AsText(geometry) as geom_text, '{delegacion}' AS delegacion FROM public.\"{tabla}\" WHERE {claves} = :clave)"
        for tabla, delegacion in tablas.items()
    ]
    query = " UNION ALL ".join(query_parts) + " LIMIT 20"
    #print (query)
    try:
        result = get_pol1(text(query), {'clave': clave})
        if not result.empty:
            result['geometry'] = result['geometry'].apply(ajustar_poligono)
            result['manzana'] = 'mna'
            f=time.time()
            print('tiempo',f-i)
            return result.to_json(), 200
        return jsonify({"error": "Predio no encontrado"}), 404
    except Exception as e:
        print(f"Error en la consulta: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    """
   # with ThreadPoolExecutor(max_workers=8) as executor:
   #     futures=[executor.submit(process_table,tabla,delegacion,claves,clave) for tabla,delegacion in  tablas.items()]

        for future in concurrent.futures.as_completed(futures):
            result=future.result()
            if result:
                for  f   in futures:
                    f.cancel()
                fin=time.time()
                print('tiempo',fin-inicio)
                return result, 200
    return  jsonify({"error":  "predio no encontrado"}), 404
    """



@app.route("/predio")
def mostrar_predio():
    fid = request.args.get('fid')
    dele=request.args.get('del')
    print('predios',fid,dele)

    corre={'10':'datos_ALVARO_OBREGON','02':'datos_AZCAPOTZALCO','14':'datos_BENITO_JUAREZ','03':'datos_COYOACAN','04':'datos_CUAJIMALPA','15':'datos_CUAUHTEMOC','05':'datos_GUSTAVO_A_MADERO','06':'datos_IZTACALCO','07':'datos_IZTAPALAPA','08':'datos_MAGDALENA_CONTRERAS','16':'datos_MIGUEL_HIDALGO','09':'datos_MILPA_ALTA','11':'datos_TLAHUAC','12':'datos_TLALPAN','17':'datos_VENUSTIANO_CARRANZA','13':'datos_XOCHIMILCO'} #agregar las demas delegaciones

    if not fid or not dele:
        return "Faltan parámetros", 400
    
    try:
        del_co=corre.get(dele[1:3], dele[1:3])
       # print('pre',del_co)
        query = f'''SELECT * FROM public."{del_co}" WHERE fid='{fid}' '''
        sq = get_datos(query)
    
        if not sq.empty:
            datos1 = {'alcaldia': sq['alcaldia'].iloc[0],'colonia': sq['colonia'].iloc[0],'calle': sq['calle_numero'].iloc[0],'superficiet': sq['sup_terreno'].iloc[0],'superficiec': sq['sup_construccion'].iloc[0],'valorT': sq['valor_suelo'].iloc[0],'fi2':sq['fid_2'].iloc[0]}
            return render_template("index.html", datos=datos1)
        else:
            return "Predio no encontrado", 404    
    except Exception as e:
        print(f"Error: {str(e)}")
        return "Error al obtener datos del predio", 500
@app.route('/buscar')
def buscar():
    delegacion = request.args.get('delegacion')
    tipo_busqueda = request.args.get('tipo')
    valor = request.args.get('valor')
    print(delegacion[1:3],tipo_busqueda,valor,type(valor))
    if tipo_busqueda =='colonia':   #funcion para agregar la capa de la colonia
       # query="SELECT geometry FROM public.colonias  WHERE cve_col=:valor"    este funciona

        query ="""SELECT *,ST_AsText(geometry) as geom_text FROM public.colonias WHERE  cve_col=:valor"""
        #query = """SELECT * FROM tu_tabla WHERE delegacion = :delegacion AND {} = :valor""".format(tipo_busqueda)  # ¡Usar con precaución! Mejor usar diccionario de mapeo
    
        params = {'valor': delegacion+'-'+valor}
         
        gdf = get_pol1(query,params)
        #print(gdf)
        print(gdf.to_json)
        return gdf.to_json(),200 if not gdf.empty else jsonify({"error": "sin resultados"})

    if tipo_busqueda=='predio':  #los nuemros de carpeta de predio no corresponden con el nuemro de delegacion   y las cpas que se extraen se dezfazan
        #corre={'10':'ALVARO_OBREGON','02':'AZCAPOTZALCO','14':'BENITO_JUAREZ','03':'COYOACAN','04':'CUAJIMALPA','15':'CUAUHTEMOC','05':'GUSTAVO_A_MADERO','06':'IZTACALCO','07':'IZTAPALAPA','08':'MAGDALENA_CONTRERAS','16':'MIGUEL_HIDALGO','09':'MILPA_ALTA','11':'TLAHUAC','12':'TLALPAN','17':'VENUSTIANO_CARRANZA','13':'XOCHIMILCO'}
        corre={'10':'01','02':'02','14':'03','03':'04','04':'05','15':'06','05':'07','06':'08','07':'09','08':'10','16':'11','09':'12','11':'13','12':'14','17':'15','13':'16'}
        valor=str(valor)
        deleg = corre.get(delegacion[1:3], delegacion[1:3])
        print(deleg)
        #query=f"""SELECT  * FROM  public."{deleg}"   WHERE fid=:valor"""  # prueva funcional con otros datos
        query="SELECT * FROM public.rpred"+deleg+" WHERE clave=:valor "   #cartogarfia real
        
        param={'valor': valor}
        gdf=get_pol1(query,param)
        gdf['geometry']=gdf['geometry'].apply(ajustar_poligono)   #llama la funcion que ajusta los poligonos de los predios
        #print(gdf.to_json)
        return  gdf.to_json(),200 if not gdf.empty else jsonify({"error": "sin resultados"})
    
    if tipo_busqueda=='construccion':    #funcion para agregar la capa  de construccion   las capas que se extraen de la base se dezfazan
        valor=str(valor)
        print('construccion',valor,type(valor))
        i=time.time()
        corre1={'10':'01','02':'02','14':'03','03':'04','04':'05','15':'06','05':'07','06':'08','07':'09','08':'10','16':'11','09':'12','11':'13','12':'14','17':'15','13':'16'}
        dele=delegacion[1:3]
        deleg=corre1[dele]
        query="SELECT * FROM public.rcontr"+deleg+"  WHERE  idpredio=:val  "#carga geometria de construccion construcion
        #query="SELECT * FROM public.rcontr"+deleg+" LIMIT 100"#  WHERE  clave=:val  " #geometry o *
        param={'val':valor}
        gdf=get_pol1(query,param)
        
        
        gdf['geometry']=gdf['geometry'].apply(ajustar_poligono)
        print(gdf.to_json)
        f=time.time()
        print('tiempo',f-i)
        return gdf.to_json(),200 if not gdf.empty else jsonify({"error":"sin resultados"})
    if tipo_busqueda=='manzana':  #funcion para agrega r la capa de manzana la pondre solo si la solicitan   funciona
        delegacion=delegacion
        valor=str(valor)
           
        query=""" SELECT * FROM public."rman"  WHERE clave =:vall"""  
        #query="""SELECT geometry FROM public."Manzanas"  WHERE "CVEGEO" =:vall """
  
        para1={'vall':valor}
        gdf=get_pol1(query,para1)
        print(gdf)
        gdf['geometry']=gdf['geometry'].apply(ajustar_poligono)
        return gdf.to_json(),200 if not gdf.empty else jsonify({"error":"sin resultados "})
    if tipo_busqueda=='segmentacion':
        #print(838)
        valor=valor
        corre={'10':'ALVARO_OBREGON','02':'AZCAPOTZALCO','14':'BENITO_JUAREZ','03':'COYOACAN','04':'CUAJIMALPA','15':'CUAUHTEMOC','05':'GUSTAVO_A_MADERO','06':'IZTACALCO','07':'IZTAPALAPA','08':'MAGDALENA_CONTRERAS','16':'MIGUEL_HIDALGO','09':'MILPA_ALTA','11':'TLAHUAC','12':'TLALPAN','17':'VENUSTIANO_CARRANZA','13':'XOCHIMILCO'}
        deleg=corre.get(delegacion[1:3],delegacion[1:3])
        print('segmentacion',deleg)
        query= f"""SElECT *  FROM (SELECT   g.fid, g.geometry, d.valor_suelo, d.cuartil FROM  public."{deleg}" g JOIN  (SELECT fid::text, valor_suelo, NTILE(10) OVER (ORDER BY valor_suelo) AS cuartil  FROM public."datos_{deleg}") d ON  g.fid::text = d.fid) WHERE cuartil={valor} """
        #print(query)
        gdf=get_pol1(query)
        print(gdf)
        return gdf.to_json(), 200 if not gdf.empty else jsonify({"error":"sin resultados"})
         



@app.route('/')
@app.route('/map')
@login_required
def map():
    return render_template('mapprueva.html') #mapprueva.html    original  map.html


@app.route('/data')
@login_required
def data():
    return render_template('data.html')  # Página de datos estadísticos

@app.route('/info')
@login_required
def info():
    return "<h1>Página de información</h1>"  # Página de información

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
