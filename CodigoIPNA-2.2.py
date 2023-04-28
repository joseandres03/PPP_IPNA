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

# Solicitar al usuario que seleccione el archivo ANTEX de su antena receptora
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

# Solicitar al usuario que seleccione el archivo .blq de la ubicacion de interes
blq_file = select_otl_file(blq_folder)


# Itera sobre todos los archivos en la carpeta de entrada
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
        cls_url_path = "/archive/gnss/products/{}/igs{}{}.cls.Z".format(gps_week, gps_week, gps_day)
        cls_url = url_base + cls_url_path
        cls_compressed_file = os.path.join(cls_output_folder, "{}.cls.Z".format(septentrio_filename_base))
        cls_uncompressed_file = os.path.join(cls_output_folder, "{}.cls".format(septentrio_filename_base))
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

        content = content.replace('file-satantfile    = ', f'file-satantfile    ={satpcv_file}')
        content = content.replace('file-rcvantfile    = ', f'file-rcvantfile    ={antex_file}')
        content = content.replace('file-ionofile      = ', f'file-ionofile      ={ionex_file}')
        content = content.replace('file-dcbfile       = ', f'file-dcbfile       ={dcb_file}')
        content = content.replace('file-eopfile       = ', f'file-eopfile       ={erp_file}')
        content = content.replace('file-blqfile       = ', f'file-blqfile       ={blq_file}')

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
    def dms2dd(d, m, s):
         return d + m / 60 + s / 3600
    
    def dd2dms(coord):
        degrees = int(coord)
        minutes = int((coord - degrees) * 60)
        seconds = (coord - degrees - minutes / 60) * 3600
        return degrees, minutes, seconds
    
    def velocidad(valores):
        return [valores[i+1] - valores[i] for i in range(len(valores) - 1)]

    def promedio(valores):
        return sum(valores) / len(valores)

    def estabilizacion_modificada(valores, umbral_velocidad):
        vels = velocidad(valores)
        ultimo_indice_superado = None

        for i, v in enumerate(vels):
            if abs(v) > umbral_velocidad:
                ultimo_indice_superado = i

        if ultimo_indice_superado is not None:
            valores_estables = valores[ultimo_indice_superado + 1 :]
        else:
            valores_estables = valores

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

    def coord_tick_formatter(x, pos):
        d, m, s = dd2dms(x)
        return f"{d:.0f}°{m:.0f}'{s:.2f}\""

    def altitude_tick_formatter(x, pos):
        return f'{x:.4f}'

    coord_ticks = ticker.FuncFormatter(coord_tick_formatter)
    altitude_ticks = ticker.FuncFormatter(altitude_tick_formatter)

    position_file = os.path.join('C:\IPNA\data', 'POST', f"{septentrio_filename_base}.pos")
    ruta_resultados = "C:\\IPNA\\data\\your_results"

    umbral_angular = 4e-08
    umbral_metrico = 0.015

    with open(position_file, "r") as archivo_pos:
        lines = archivo_pos.readlines()
        
        # Extraigo los datos latitudes, longitudes y alturas y los meto en listas
        latitudes, longitudes, alturas = [], [], []
        tiempos = []
        
        # Obtengo los valores de desviacion estandar y error de la ultima medida del día y la tomo como error y desviacion del día
        sdn, sde, sdu, sdne, sdeu, sdue = 0, 0, 0, 0, 0, 0
        for line in reversed(lines):
            if line.strip() and not line.startswith('%'):
                data = line.split()
                if len(data) == 19:  # Hay 20 elementos en lugar de 18 debido a la estructura de latitud y longitud
                    sdn, sde, sdu, sdne, sdeu, sdue = map(float, data[11:17])  # Cambiar aquí el índice inicial a 14 y final a 19
                    break

        for line in lines:
            if line.strip() and not line.startswith('%'):
                data = line.split()
                fecha, hora, *coords = data
                lat_d, lat_m, lat_s, lon_d, lon_m, lon_s, alt, *_ = map(float, coords)

                lat = dms2dd(lat_d, lat_m, lat_s)
                lon = dms2dd(lon_d, lon_m, lon_s)

                latitudes.append(lat)
                longitudes.append(lon)
                alturas.append(alt)
                tiempos.append(datetime.strptime(f'{fecha} {hora}', '%Y/%m/%d %H:%M:%S.%f'))

        promedio_lat = estabilizacion_modificada(latitudes, umbral_angular)
        promedio_lon = estabilizacion_modificada(longitudes, umbral_angular)
        promedio_alt = estabilizacion_modificada(alturas, umbral_metrico)
        promedio_lat_dms = dd2dms(promedio_lat)
        promedio_lon_dms = dd2dms(promedio_lon)
        
        # Representación gráfica de las coordenadas y promedios
        fig, ax = plt.subplots(3, 1, figsize=(8, 12), sharex=True)
    
        plot_coords(fig, ax, tiempos, latitudes, 'N-S', promedio_lat, 0, coord_ticks)
        plot_coords(fig, ax, tiempos, longitudes, 'E-W', promedio_lon, 1, coord_ticks)
        plot_coords(fig, ax, tiempos, alturas, 'U-D [m]', promedio_alt, 2)
    
        # Ajuste de los ticks en el eje Y
        ax[0].yaxis.set_major_formatter(coord_ticks)
        ax[1].yaxis.set_major_formatter(coord_ticks)
        ax[1].invert_yaxis()  # Invertir la escala vertical de longitudes
        ax[2].yaxis.set_major_formatter(altitude_ticks)

        plt.tight_layout()
        plt.gcf().autofmt_xdate()
        plt.savefig(os.path.join(ruta_resultados, "coordenadas_tiempo.png"))
        plt.show()
        plt.tight_layout()
        
        with open(os.path.join(ruta_resultados, "posiciones.txt"), "w") as archivo_resultados:
            archivo_resultados.write("#  UTC            latitude            longitude            height(m)    sdn(m)   sde(m)   sdu(m)   sdne(m)  sdeu(m)  sdue(m)\n")
            archivo_resultados.write(f"{fecha}        {promedio_lat_dms[0]:.0f}°{promedio_lat_dms[1]:.0f}'{promedio_lat_dms[2]:.5f}\"     {promedio_lon_dms[0]:.0f}°{promedio_lon_dms[1]:.0f}'{promedio_lon_dms[2]:.5f}\"    {promedio_alt:.4f}      {sdn:.4f}   {sde:.4f}   {sdu:.4f}   {sdne:.4f}  {sdeu:.4f}   {sdue:.4f}\n")

    
    # Gráfica en 3D
    latitudes_deg, latitudes_min, latitudes_sec = zip(*[dd2dms(lat) for lat in latitudes])
    longitudes_deg, longitudes_min, longitudes_sec = zip(*[dd2dms(lon) for lon in longitudes])

    latitudes_dms = [(lat_d, lat_m, lat_s) for lat_d, lat_m, lat_s in zip(latitudes_deg, latitudes_min, latitudes_sec)]
    longitudes_dms = [(lon_d, lon_m, lon_s) for lon_d, lon_m, lon_s in zip(longitudes_deg, longitudes_min, longitudes_sec)]

    def plot_3d_path(latitudes, longitudes, alturas, promedio_lat, promedio_lon, promedio_alt):
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')
    
        latitudes_decimal = [dms2dd(*lat) for lat in latitudes]
        longitudes_decimal = [dms2dd(*lon) for lon in longitudes]
    
        ax.plot(longitudes_decimal, latitudes_decimal, alturas, marker='o', linestyle='-', linewidth=0.7, markersize=2)

        # Agregar el punto promedio al gráfico 3D
        ax.scatter(promedio_lon, promedio_lat, promedio_alt, c='r', marker='o', s=100, label="Promedio")

        ax.set_xlabel('Longitud [°]')
        ax.set_ylabel('Latitud [°]')
        ax.set_zlabel('Altura [m]')
        ax.legend()  # Agregar la leyenda

        plt.show()

    # Llamar a la función con los valores promedio
    plot_3d_path(latitudes_dms, longitudes_dms, alturas, promedio_lat, promedio_lon, promedio_alt)

    
