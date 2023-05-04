# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 11:51:32 2023

@author: Jose Andres
"""

import requests
import subprocess
import os
import platform
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import ticker
import glob
from pyproj import Proj, transform
import matplotlib.image as mpimg
import cv2

# Archivos fijos para todas las medidas
satpcv_file = "C:\IPNA\data\ANTEX\igs20.atx"
blq_folder = "C:\IPNA\data\OTL_BLQ"
antex_folder = "C:\IPNA\data\ANTEX"
rtkpost_exe = r"C:\IPNA\bin\rnx2rtkp.exe"
rtkpost_conf = r"C:\IPNA\bin\rtkpost.conf"
rtkplot_exe = r"C:\IPNA\bin\rtkplot.exe"

# Ruta fija a la carpeta de entrada que contiene los archivos Septentrio sin procesar
input_folder = 'C:\IPNA\data\your_archives'

# Define la ruta de la carpeta que contiene los ejecutables teqc
teqc_executables_path = "C:\\IPNA\\executables"

# Detecta el sistema operativo
system = platform.system()
# Establece el nombre del ejecutable teqc según el sistema operativo
if system == 'Windows':
    teqc_executable = 'teqc_WINDOWS.exe'
elif system == 'Darwin':
    teqc_executable = 'teqc_MAC'
elif system == 'Linux':
    teqc_executable = 'teqc_LINUX'
else:
    raise Exception('Sistema operativo no soportado')

# Seleccion del archivo .atx de su antena receptora. El archivo igs20.atx no cuenta dado que es el .atx para los satélites.
def select_antex_file(antex_folder):
    antex_files = glob.glob(os.path.join(antex_folder, '*.atx'))
    filtered_antex_files = [file for file in antex_files if os.path.basename(file) != 'igs20.atx']
    
    if len(filtered_antex_files) == 1:
        print(f"Archivo ANTEX único encontrado: {os.path.basename(filtered_antex_files[0])}")
        return filtered_antex_files[0]
    else:
        print("Seleccione el archivo ANTEX:")
        for idx, file in enumerate(filtered_antex_files):
            print(f"{idx + 1}: {os.path.basename(file)}")
        
        while True:
            try:
                user_input = int(input("Ingrese el número correspondiente al archivo ANTEX para su antena receptora: ")) - 1
                if 0 <= user_input < len(filtered_antex_files):
                    return filtered_antex_files[user_input]
                else:
                    print("Número inválido. Intente de nuevo.")
            except ValueError:
                print("Entrada inválida. Intente de nuevo.")

# Solicitar al usuario que seleccione el archivo ANTEX de su antena receptora (si solo hay un archivo usará automaticamente ese)
antex_file = select_antex_file(antex_folder)

# Seleccion del archivo .blq.
def select_otl_file(otl_folder):
    otl_files = glob.glob(os.path.join(otl_folder, '*.blq'))
    
    if len(otl_files) == 1:
        print(f"Archivo OTL único encontrado: {os.path.basename(otl_files[0])}")
        return otl_files[0]
    else:
        print("Seleccione el archivo OTL:")
        for idx, file in enumerate(otl_files):
            print(f"{idx + 1}: {os.path.basename(file)}")
        
        while True:
            try:
                user_input = int(input("Ingrese el número correspondiente al archivo OTL para su antena receptora: ")) - 1
                if 0 <= user_input < len(otl_files):
                    return otl_files[user_input]
                else:
                    print("Número inválido. Intente de nuevo.")
            except ValueError:
                print("Entrada inválida. Intente de nuevo.")

# Solicitar al usuario que seleccione el archivo .blq de la ubicacion de interes (si solo hay un archivo usará automaticamente ese)
blq_file = select_otl_file(blq_folder)

# Itera sobre todos los archivos crudos en la carpeta de entrada.
for filename in os.listdir(input_folder):
    
    # Funcion para procesar los archivos septentrio y obtener los rinex (.o y .n)
    def convert_septentrio_to_rinex(input_folder):
        # Crea las subcarpetas para los archivos de salida (.o y .n) si no existen
        base_folder = os.path.dirname(input_folder)
        obs_output_folder = os.path.join(base_folder, 'OBS')
        if not os.path.exists(obs_output_folder):
            os.makedirs(obs_output_folder)
        nav_output_folder = os.path.join(base_folder, 'NAV')
        if not os.path.exists(nav_output_folder):
            os.makedirs(nav_output_folder)
        # Divide el nombre del archivo en su nombre base y su extensión
        file_base, file_ext = os.path.splitext(filename)
        # Construye las rutas completas a los archivos de entrada y salida
        input_file = os.path.join(input_folder, filename)
        obs_output_file = os.path.join(obs_output_folder, file_base + '.o')
        nav_output_file = os.path.join(nav_output_folder, file_base + '.n')
        # Construye el comando Teqc
        teqc_command = [os.path.join(teqc_executables_path, teqc_executable), '+obs', obs_output_file, '+nav', nav_output_file, input_file]
        # Ejecuta el comando Teqc
        subprocess.run(teqc_command)
        # Devuelve el nombre base del archivo para su posterior utilizacion.    
        return file_base
    
    # Ejecutar la función convert_septentrio_to_rinex y obtener el nombre base del archivo Septentrio
    septentrio_filename_base = convert_septentrio_to_rinex(input_folder)
    # Encontrar el archivo .o en la carpeta de archivos de observación y el archivo .n en la de navegación
    observation_file = os.path.join('C:\IPNA\data', 'OBS', f"{septentrio_filename_base}.o")
    navigation_file = os.path.join('C:\IPNA\data', 'NAV', f"{septentrio_filename_base}.n")
    
    # Función que obtiene la fecha que se tomaron las medidas desde el archivo de observación
    def get_date_from_rinex(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                if 'TIME OF FIRST OBS' in line:
                    year, month, day, hour, minute, second = [int(x) if i != 5 else float(x) for i, x in enumerate(line.strip().split()[0:6])]
                    return datetime(year, month, day, hour, minute, int(second))
    
    # Función que obtiene el año en el que se tomaron las medidas
    def get_day_of_year(date_observation):
        return date_observation.timetuple().tm_yday
    
    # Función que obtiene el trimestre del año al que pertenece el dia de las medidas, para la descarga del archivo .dcb
    def get_quarter(day_of_year):
        quarter = (day_of_year - 1) // 91 + 1
        quarter_start_day = (quarter - 1) * 91 + 1
        return quarter, quarter_start_day
    
    # Función que obtiene/convierte el tiempo en calendario GPS para la descargas de los archivos GNSS
    def datetime_to_gps_week_day(dt):
        # Fecha de referencia del GPS (1980-01-06 00:00:00)
        gps_epoch = datetime(1980, 1, 6)
        delta = dt - gps_epoch
        # Calcular la semana y el día GPS
        gps_week = delta.days // 7
        gps_day = delta.days % 7
        return gps_week, gps_day
    
    # Leer la fecha de la observación
    date_observation = get_date_from_rinex(observation_file)
    # Tiempo en calendario GPS
    gps_week, gps_day = datetime_to_gps_week_day(date_observation)
    print(f"Semana GPS: {gps_week}, Día GPS: {gps_day}")
    
    # Función para descargar y descomprimir archivsos
    def download_and_uncompress_file(url, output_folder, output_file, compressed_file):
        # Verifica si el archivo ya existe en la carpeta de destino
        if os.path.exists(output_file):
            print(f"El archivo {output_file} ya existe en la carpeta de destino. Omitiendo la descarga.")
            return output_file
        try:
            print("Descargando el archivo: {}".format(url))
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Lanza una excepción si hay algún error HTTP
            with open(compressed_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            print("Error al descargar el archivo: {} - Error: {}".format(url, e))
            return None
        # Descomprimir el archivo
        if platform.system() == "Windows":
            subprocess.run(['WinRAR.exe', 'e', '-y', compressed_file], cwd=output_folder)
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            subprocess.run(['uncompress', compressed_file], cwd=output_folder)
        else:
            raise Exception('Sistema operativo no soportado')
        # Renombrar el archivo descomprimido y eliminar el archivo comprimido
        os.rename(os.path.join(output_folder, os.path.basename(compressed_file[:-2])), output_file)
        os.remove(compressed_file)
        return output_file
    
    # Función para descargar los archivos gnss necesarios para su posterior uso en RTKPOST
    def download_gnss_files(gps_week, gps_day, date_observation):
        url_base = "https://cddis.nasa.gov"
        
        # Calcular el día del año y el trimestre correspondiente
        day_of_year = get_day_of_year(date_observation)
        quarter, quarter_start_day = get_quarter(day_of_year)
        
        print(f"Día del año: {day_of_year}, Trimestre: {quarter}")
        # Crear las carpetas CLOCK, ERP, DCB, IONEX y SP3 si no existen
        sp3_output_folder = os.path.join('C:\IPNA\data', 'SP3')
        if not os.path.exists(sp3_output_folder):
            os.makedirs(sp3_output_folder)
        cls_output_folder = os.path.join('C:\IPNA\data', 'CLOCK')
        if not os.path.exists(cls_output_folder):
            os.makedirs(cls_output_folder)
        erp_output_folder = os.path.join('C:\IPNA\data', 'ERP')
        if not os.path.exists(erp_output_folder):
            os.makedirs(erp_output_folder)
        dcb_output_folder = os.path.join('C:\IPNA\data', 'DCB')
        if not os.path.exists(dcb_output_folder):
            os.makedirs(dcb_output_folder)
        ionex_output_folder = os.path.join('C:\IPNA\data', 'IONEX')
        if not os.path.exists(ionex_output_folder):
            os.makedirs(ionex_output_folder)
            
        # Construir el nombre del archivo de salida sp3 utilizando el nombre base del archivo Septentrio
        sp3_output_filename = "{}.sp3".format(septentrio_filename_base)
        
        # Descargar y descomprimir archivo sp3
        sp3_url_path = "/archive/gnss/products/{}/igs{}{}.sp3.Z".format(gps_week, gps_week, gps_day)
        sp3_url = url_base + sp3_url_path
        sp3_compressed_file = os.path.join(sp3_output_folder, "igs{}{}.sp3.Z".format(gps_week, gps_day))
        sp3_uncompressed_file = os.path.join(sp3_output_folder, sp3_output_filename)
        download_and_uncompress_file(sp3_url, sp3_output_folder, sp3_uncompressed_file, sp3_compressed_file)
        
        # Descargar y descomprimir archivo .cls
        cls_url_path = "/archive/gnss/products/{}/igs{}{}.clk.Z".format(gps_week, gps_week, gps_day)
        cls_url = url_base + cls_url_path
        cls_compressed_file = os.path.join(cls_output_folder, "{}.clk.Z".format(septentrio_filename_base))
        cls_uncompressed_file = os.path.join(cls_output_folder, "{}.clk".format(septentrio_filename_base))
        download_and_uncompress_file(cls_url, cls_output_folder, cls_uncompressed_file, cls_compressed_file)
        
        # Descargar y descomprimir archivo .erp
        erp_url_path = "/archive/gnss/products/{}/igs{}7.erp.Z".format(gps_week, gps_week)
        erp_url = url_base + erp_url_path
        erp_compressed_file = os.path.join(erp_output_folder, "{}.erp.Z".format(gps_week))
        erp_uncompressed_file = os.path.join(erp_output_folder, "{}.erp".format(gps_week))
        download_and_uncompress_file(erp_url, erp_output_folder, erp_uncompressed_file, erp_compressed_file)
        
        # Descargar y descomprimir el archivo DCB
        dcb_output_file = os.path.join(dcb_output_folder, f"{quarter}_trimestre.dcb")
        dcb_url = "https://cddis.nasa.gov/archive/gnss/products/bias/{}/DLR0MGXFIN_{}{}0000_03L_01D_DCB.BSX.gz".format(date_observation.year, date_observation.year, quarter_start_day)
        compressed_dcb_file = os.path.join(dcb_output_folder, "DLR0MGXFIN_{}{}0000_03L_01D_DCB.BSX.gz".format(date_observation.year, quarter_start_day))
        download_and_uncompress_file(dcb_url, dcb_output_folder, dcb_output_file, compressed_dcb_file)
        
        # Descargar y descomprimir el archivo de ionosfera
        two_digit_year = date_observation.year % 100
        day_of_year = get_day_of_year(date_observation)
        ionex_output_file = os.path.join(ionex_output_folder, f"{septentrio_filename_base}.{two_digit_year}i")
        ionex_url = f"https://cddis.nasa.gov/archive/gnss/products/ionosphere/{date_observation.year}/{day_of_year:03}/igsg{day_of_year:03}0.{two_digit_year}i.Z"
        compressed_ionex_file = os.path.join(ionex_output_folder, f"igsg{day_of_year:03}0.{two_digit_year}i.Z")
        download_and_uncompress_file(ionex_url, ionex_output_folder, ionex_output_file, compressed_ionex_file)

        return sp3_uncompressed_file, cls_uncompressed_file, erp_uncompressed_file, dcb_output_file, ionex_output_file
    
    # Descarga de los archivos desde GNSS
    sp3_file, cls_file, erp_file, dcb_file, ionex_file = download_gnss_files(gps_week, gps_day, date_observation)
     
    # Función que modifica el archivo de configuracion (rtkpost.conf) del RTKPOST
    def update_rtkpost_conf(rtkpost_conf, satpcv_file, antex_file, ionex_file, dcb_file, erp_file, blq_file):
        with open(rtkpost_conf, 'r') as f:
            content = f.read()
            
        content = content.replace('file-satantfile    = {}', f'file-satantfile    ={satpcv_file}')
        content = content.replace('file-rcvantfile    = {}', f'file-rcvantfile    ={antex_file}')
        content = content.replace('file-ionofile      = {}', f'file-ionofile      ={ionex_file}')
        content = content.replace('file-dcbfile       = {}', f'file-dcbfile       ={dcb_file}')
        content = content.replace('file-eopfile       = {}', f'file-eopfile       ={erp_file}')
        content = content.replace('file-blqfile       = {}', f'file-blqfile       ={blq_file}')

        with open(rtkpost_conf, 'w') as f:
            f.write(content)
    
    # Actualizar el archivo de configuración
    update_rtkpost_conf(rtkpost_conf, satpcv_file, antex_file, ionex_file, dcb_file, erp_file, blq_file)

    # Función rtkpost para obtener el archivo .pos y guardarlo en la carpeta POS
    def run_rtkpost(rtkpost_exe, rtkpost_conf, observation_file, navigation_file, sp3_file, clk_file, output_file):
        cmd = [rtkpost_exe, "-k", rtkpost_conf, "-o", output_file, observation_file, navigation_file, sp3_file, clk_file]
        subprocess.run(cmd, capture_output=True, text=True)
    
    # Ruta y nombre del archivo de salida que se obtendrá al ejecutar rtkpost
    output_file = os.path.join(r"C:\\IPNA\\data\\POST", f"{septentrio_filename_base}.pos")
    # Ejecucion de rtkpost
    run_rtkpost(rtkpost_exe, rtkpost_conf, observation_file, navigation_file, sp3_file, cls_file, output_file)
    
    # Obtencion de un valor promedio para cada coordenada en ese día
    # Funcion para convertir de grados minutos y segundos a solo grados
    def dms2dd(d, m, s):
         return d + m / 60 + s / 3600
    
    # Funcion para pasar de grados a grados minutos y segundos
    def dd2dms(coord):
        degrees = int(coord)
        minutes = int((coord - degrees) * 60)
        seconds = (coord - degrees - minutes / 60) * 3600
        return degrees, minutes, seconds
    
    # Esta funcion calcula la velocidad a la que cambian los datos de coordenadas
    def velocidad(valores):
        return [valores[i+1] - valores[i] for i in range(len(valores) - 1)]
    
    # Funcion que calcula el promedio de una cantidad de valores
    def promedio(valores):
        return sum(valores) / len(valores)
    
    # Funcion que selecciona los valores a promediar una vez estos se estabilizan.
    def estabilizacion_modificada(valores, umbral_velocidad, return_indice=False):
        vels = velocidad(valores)
        ultimo_indice_superado = None

        for i, v in enumerate(vels):
            if abs(v) > umbral_velocidad:
                ultimo_indice_superado = i

        if ultimo_indice_superado is not None:
            valores_estables = valores[ultimo_indice_superado + 1 :]
            indice_estabilizacion = ultimo_indice_superado + 1
        else:
            valores_estables = valores
            indice_estabilizacion = 0
        
        if return_indice:
            return promedio(valores_estables), indice_estabilizacion
        else:
            return promedio(valores_estables)
    
    # Grafica las coordenadas y el promedio
    def plot_coords(fig, ax, tiempos, coords, ylabel, promedio, subplot_idx, formatter=None):
        ax[subplot_idx].plot(tiempos, coords, marker='o', linestyle='-', linewidth=0.7, markersize=2)
        ax[subplot_idx].axhline(promedio, color='r', linestyle='--', linewidth=0.7, label="Promedio")
        ax[subplot_idx].set_xlabel('Tiempo')
        ax[subplot_idx].set_ylabel(ylabel)
        ax[subplot_idx].set_title(f'{ylabel} frente al tiempo')
        ax[subplot_idx].grid()
        ax[subplot_idx].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
        if formatter:
            ax[subplot_idx].yaxis.set_major_formatter(formatter)
    
        primer_tiempo = tiempos[0]
        minutos = primer_tiempo.minute
        if minutos < 30:
            primer_tiempo = primer_tiempo.replace(minute=0, second=0, microsecond=0)
        else:
            primer_tiempo = primer_tiempo.replace(minute=30, second=0, microsecond=0)
    
        ax[subplot_idx].set_xlim(primer_tiempo)
        ax[subplot_idx].xaxis.set_major_locator(mdates.HourLocator())
        ax[subplot_idx].xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[30]))
        ax[subplot_idx].xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
        ax[subplot_idx].tick_params(axis='x', which='minor', bottom=True)
        ax[subplot_idx].legend()
    
    # Funciones para modificar el formato de escala los valores
    def coord_tick_formatter(x, pos):
        d, m, s = dd2dms(x)
        return f"{d:.0f}°{m:.0f}'{s:.2f}\""

    def altitude_tick_formatter(x, pos):
        return f'{x:.4f}'
    
    # Cambio a proyeccion UTM
    def latlon_to_utm(lat, lon):
        utm_zone = int((lon + 180) / 6) + 1
        is_northern = lat >= 0

        wgs84 = Proj(proj="latlong", datum="WGS84", ellps="WGS84")
        utm = Proj(proj="utm", zone=utm_zone, north=is_northern, ellps="WGS84")

        utm_x, utm_y = transform(wgs84, utm, lon, lat)
    
        return utm_x, utm_y
    
    coord_ticks = ticker.FuncFormatter(coord_tick_formatter)
    altitude_ticks = ticker.FuncFormatter(altitude_tick_formatter)
    
    # Ruta al archivo .pos obtenido con rtkpost para calcular el valor promedio para ese dia
    position_file = os.path.join('C:\IPNA\data', 'POST', f"{septentrio_filename_base}.pos")
    # Ruta a la carpeta donde se guardará el archivo con los promedios
    ruta_resultados = "C:\\IPNA\\data\\your_results"
    
    # Umbrales de velocidad angular y metrica para establecer un valor minimo de estabilizacion de los datos a promediar
    umbral_angular = 4e-08
    umbral_metrico = 0.015
    
    # Abrir el archivo pos para su lectura y procesamiento de datos con las anteriores funciones.
    with open(position_file, "r") as archivo_pos:
        lines = archivo_pos.readlines()
        # Extraigo los datos latitudes, longitudes y alturas y los meto en listas
        latitudes, longitudes, alturas, sdn, sde, sdu = [], [], [], [], [], []
        tiempos = []
        # Obtengo los valores del día dado que son los que mayor presicion tiene por el método en que se obtienen las coordenadas
        lat_ult, lon_ult, alt_ult, sdn_ult, sde_ult, sdu_ult = 0, 0, 0, 0, 0, 0
        for line in reversed(lines):
            if line.strip() and not line.startswith('%'):
                data = line.split()
                if len(data) == 19:  # Hay 20 columnas
                    fecha_ult, hora_ult, *coords = data
                    lat_d_ult, lat_m_ult, lat_s_ult, lon_d_ult, lon_m_ult, lon_s_ult, alt_ult, *_ = map(float, coords[:7])
                    lat_ult = dms2dd(lat_d_ult, lat_m_ult, lat_s_ult)
                    lon_ult = dms2dd(lon_d_ult, lon_m_ult, lon_s_ult)
                    sdn_ult, sde_ult, sdu_ult = map(float, data[11:14])
                    break
        # Guardo los valores de latitudes, longitudes, altura y desviaciones en las listas definidas al comienzo.
        for line in lines:
            if line.strip() and not line.startswith('%'):
                data = line.split()
                fecha, hora, *coords = data
                lat_d, lat_m, lat_s, lon_d, lon_m, lon_s, alt, *_ = map(float, coords[:7])
                lat = dms2dd(lat_d, lat_m, lat_s)
                lon = dms2dd(lon_d, lon_m, lon_s)
                latitudes.append(lat)
                longitudes.append(lon)
                alturas.append(alt)
                tiempos.append(datetime.strptime(f'{fecha} {hora}', '%Y/%m/%d %H:%M:%S.%f'))
                sdn.append(float(data[11]))
                sde.append(float(data[12]))
                sdu.append(float(data[13]))
                
        # Calculo con el promedio de cada una de las listas una vez esten estabilizados.
        promedio_lat, indice_estabilizacion_lat = estabilizacion_modificada(latitudes, umbral_angular, return_indice=True)
        promedio_lon, indice_estabilizacion_lon = estabilizacion_modificada(longitudes, umbral_angular, return_indice=True)
        promedio_alt, indice_estabilizacion_alt = estabilizacion_modificada(alturas, umbral_metrico, return_indice=True)
        promedio_sdn = promedio(sdn[indice_estabilizacion_lat:])
        promedio_sde = promedio(sde[indice_estabilizacion_lon:])
        promedio_sdu = promedio(sdu[indice_estabilizacion_alt:])

        # Representación gráfica de las coordenadas y promedios en tres graficas distintas
        #fig, ax = plt.subplots(3, 1, figsize=(8, 12), sharex=True)
        #plot_coords(fig, ax, tiempos, latitudes, 'N-S', promedio_lat, 0, coord_ticks)
        #plot_coords(fig, ax, tiempos, longitudes, 'E-W', promedio_lon, 1, coord_ticks)
        #plot_coords(fig, ax, tiempos, alturas, 'U-D [m]', promedio_alt, 2)
    
        # Ajuste de los ticks en el eje Y
        #ax[0].yaxis.set_major_formatter(coord_ticks)
        #ax[1].yaxis.set_major_formatter(coord_ticks)
        #ax[1].invert_yaxis()  # Invertir la escala vertical de longitudes
        #ax[2].yaxis.set_major_formatter(altitude_ticks)

        #plt.gcf().autofmt_xdate()
        #plt.savefig(os.path.join(ruta_resultados, f"{septentrio_filename_base}.png"))
        #plt.show()
        #plt.tight_layout()
        
        # Cambio a coordendas en la zona UTM
        utm_x_best, utm_y_best = latlon_to_utm(lat_ult, lon_ult)
        utm_x_avg, utm_y_avg = latlon_to_utm(promedio_lat, promedio_lon)

        # Guarda los promedios, las desviaciones y los errores de las desviaciones en un archivo.
        archivo_resultados_path = os.path.join(ruta_resultados, "posiciones.txt")
        if not os.path.exists(archivo_resultados_path):
            with open(archivo_resultados_path, "w") as archivo_resultados:
                archivo_resultados.write("#  UTC       Northing(best)   Easting(best)   Altitude(best)   sdn(best)   sde(best)   sda(best)  |  Northing(avg)   Easting(avg)   Altitude(avg)   sdn(avg)   sde(avg)   sda(avg)\n")

        with open(archivo_resultados_path, "a") as archivo_resultados:
            archivo_resultados.write(f"{fecha}   {utm_y_best:.4f}      {utm_x_best:.4f}      {alturas[-1]:.4f}         {sdn[-1]:.4f}      {sde[-1]:.4f}      {sdu[-1]:.4f}    |  {utm_y_avg:.4f}    {utm_x_avg:.4f}      {promedio_alt:.4f}        {promedio_sdn:.4f}     {promedio_sde:.4f}     {promedio_sdu:.4f}\n")

# Codigo para graficar los datos
# Cargar imágenes de logotipos
ipna_logo = mpimg.imread('C:\IPNA\logo_IPNA.png')
ull_logo = mpimg.imread('C:\IPNA\logo_facultad_fisica.png')

ruta_resultados = "C:\\IPNA\\data\\your_results"
archivo_resultados_path = os.path.join(ruta_resultados, "posiciones.txt")

# Leer el archivo posiciones.txt
with open(archivo_resultados_path, "r") as archivo_resultados:
    lines = archivo_resultados.readlines()

# Saltar la primera línea (encabezado) y procesar las líneas de datos
data = [line.strip().split() for line in lines[1:]]

# Extraer las fechas, valores de Northing, Easting y Altitude, y sus respectivas desviaciones
fechas = [datetime.strptime(d[0], "%Y/%m/%d") for d in data]
northing_best = [float(d[1]) for d in data]
easting_best = [float(d[2]) for d in data]
altitude_best = [float(d[3]) for d in data]
sdn_best = [float(d[4]) for d in data]
sde_best = [float(d[5]) for d in data]
sdu_best = [float(d[6]) for d in data]

northing_avg = [float(d[8]) for d in data]
easting_avg = [float(d[9]) for d in data]
altitude_avg = [float(d[10]) for d in data]
sdn_avg = [float(d[11]) for d in data]
sde_avg = [float(d[12]) for d in data]
sdu_avg = [float(d[13]) for d in data]

# Convertir los valores y las desviaciones estándar a milimetros
northing_best = [(n - northing_best[0]) * 1000 for n in northing_best]
easting_best = [(e - easting_best[0]) * 1000 for e in easting_best]
altitude_best = [(a - altitude_best[0]) * 1000 for a in altitude_best]
sdn_best = [sd * 1000 for sd in sdn_best]
sde_best = [sd * 1000 for sd in sde_best]
sdu_best = [sd * 1000 for sd in sdu_best]

northing_avg = [(n - northing_avg[0]) * 1000 for n in northing_avg]
easting_avg = [(e - easting_avg[0]) * 1000 for e in easting_avg]
altitude_avg = [(a - altitude_avg[0]) * 1000 for a in altitude_avg]
sdn_avg = [sd * 1000 for sd in sdn_avg]
sde_avg = [sd * 1000 for sd in sde_avg]
sdu_avg = [sd * 1000 for sd in sdu_avg]

# Crear gráficas
fig, ax = plt.subplots(3, 1, figsize=(12, 15))
fig.subplots_adjust(top=0.92)

# Ajustar el espacio en la parte superior del gráfico
fig.subplots_adjust(top=0.85)

# Calcular el tamaño y las coordenadas de los logotipos
ipna_logo_height = 70
ull_logo_height = 50
logo_width = 100

ipna_logo_x, ipna_logo_y = 1.5 * fig.bbox.xmax / 3 - logo_width / 2, fig.bbox.ymax - ipna_logo_height - 20
ull_logo_x, ull_logo_y = 2.2 * fig.bbox.xmax / 3 - logo_width / 2, fig.bbox.ymax - ull_logo_height - 30

# Calcular factores de escala para los logotipos
ipna_logo_scale = ipna_logo_height / ipna_logo.shape[0]
ull_logo_scale = ull_logo_height / ull_logo.shape[0]

# Redimensionar logotipos
ipna_logo_resized = cv2.resize(ipna_logo, None, fx=ipna_logo_scale, fy=ipna_logo_scale, interpolation=cv2.INTER_AREA)
ull_logo_resized = cv2.resize(ull_logo, None, fx=ull_logo_scale, fy=ull_logo_scale, interpolation=cv2.INTER_AREA)

# Agregar logotipos a la gráfica
fig.figimage(ipna_logo_resized, ipna_logo_x, ipna_logo_y, zorder=3)
fig.figimage(ull_logo_resized, ull_logo_x, ull_logo_y, zorder=3)

# Añadir texto adicional debajo de los logotipos
fig.text(0.2, 0.92, 'Prácticas Externas, Grado en Física\nJosé Andrés Ramos Mendoza\nFechas: Del {} al {}'.format(fechas[0].strftime("%Y/%m/%d"), fechas[-1].strftime("%Y/%m/%d")),
         ha='center', va='bottom', fontsize=12)

# Configurar el formato del eje x
for axis in ax:
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
    axis.xaxis.set_major_locator(mdates.DayLocator(interval=1))

    # Establecer la longitud personalizada de las marcas de graduación mayores
    axis.tick_params(axis='x', which='major', direction='inout', length=15, width=1.5)
    axis.tick_params(axis='x', which='minor', direction='inout', length=5, width=1)

    # Añadir grid horizontal
    axis.grid(True, axis='y')  # Cambiar esto para mostrar solo líneas de cuadrícula horizontales
    axis.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
    
    # Agregar cuadrícula y ajustar espaciado
    axis.tick_params(axis='x', which='minor', length=3, direction='in', top=True, width=1.5)
    axis.tick_params(axis='x', which='major', length=5, direction='in', top=True, width=1.5)

    # Aumentar el grosor del marco del gráfico
    for spine in axis.spines.values():
        spine.set_linewidth(1.5)
        
# Función para centrar el eje y=0 en el medio de la gráfica con un margen del 10%
def center_yaxis(ax, data1, data2, margin=0.1):
    min_val = min(min(data1), min(data2))
    max_val = max(max(data1), max(data2))
    max_range = max(abs(min_val), abs(max_val))
    max_range = max_range * (1 + margin)
    ax.set_ylim(-max_range, max_range)

# Centrar y ajustar los ejes Y para las tres gráficas
center_yaxis(ax[0], northing_best, northing_avg)
center_yaxis(ax[1], easting_best, easting_avg)
center_yaxis(ax[2], altitude_best, altitude_avg)

# Northing
ax[0].errorbar(fechas, northing_best, yerr=sdn_best, fmt='o', color='navy', label='última medida', capsize=3)
ax[0].errorbar(fechas, northing_avg, yerr=sdn_avg, fmt='o', color='r', label='promedio', capsize=3)
ax[0].set_ylabel('Northing [mm]')
ax[0].legend()

# Easting
ax[1].errorbar(fechas, easting_best, yerr=sde_best, fmt='o', color='navy', label='última medida', capsize=3)
ax[1].errorbar(fechas, easting_avg, yerr=sde_avg, fmt='o', color='r', label='promedio', capsize=3)
ax[1].set_ylabel('Easting [mm]')
ax[1].legend()

# Altitude
ax[2].errorbar(fechas, altitude_best, yerr=sdu_best, fmt='o', color='navy', label='última medida', capsize=3)
ax[2].errorbar(fechas, altitude_avg, yerr=sdu_avg, fmt='o', color='r', label='promedio', capsize=3)
ax[2].set_ylabel('Altitude [mm]')
ax[2].legend()

# Establecer el límite del eje Y en cada gráfico
ax[0].set_ylim(-70, 70)
ax[1].set_ylim(-70, 70)
ax[2].set_ylim(-70, 70)
fig.tight_layout(rect=[0, 0.03, 1, 0.92])  # Ajustar el rectángulo del layout para dejar espacio al suptitle

# Guardar y mostrar la gráfica
plt.savefig(os.path.join(ruta_resultados, "grafico_resultados.png"))
plt.show()