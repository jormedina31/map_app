proyecto cartografico CDMX
requerimientos:
tener instalado 
python 3.10  
git 2.37

pasos para  la instalacion del proyecto

clona el proyecto con el siguiente comando:

-  git clone  https://github.com/jormedina31/map_app.git
-  cd map_app

crea un entorno virtual(opcional) para no crear conflicto con librerias 
instaladas en un entorno global

-  python -m venv nombre_del_entorno

  
  ej:  python -m venv mapp
en cmd


-  mapp\Scripts\activate

  
power shell



-  .\mapp\Scripts\Activate



la salida  debe verse algo  como:
(mapp) C:\ruta\al\proyecto\map_app


ejecuta:


-  pip install -r requeriments.txt



esto instalara las librerias que ocupa python

una vez instalado  dirijete  al donde esta el proyecto principal app.py
deberia verse algo como '(mapp) C:\ruta\al\proyecto\map_app\map_app'
estando ahi  ejecuta


- python  app.py

se desglosara la pagina  al inicio con un sistema de login para poder registrarce 
una vez echo el registro pulse 'iniciarciar sesion' donde se desglozara ell mapa principal





