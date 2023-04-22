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
import glob

# Archivos fijos para todas las medidas
satpcv_file = "C:\IPNA\data\ANTEX\igs20.atx"
blq_file = "C:\IPNA\data\OTL_BLQ\La_Palma_Volcano.blq"
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

def select_antex_file(antex_folder):
    antex_files = glob.glob(os.path.join(antex_folder, '*.atx'))
    print("Seleccione el archivo ANTEX:")
    for idx, file in enumerate(antex_files):
        print(f"{idx + 1}: {os.path.basename(file)}")
    
    while True:
        try:
            user_input = int(input("Ingrese el número correspondiente al archivo ANTEX para su antena receptora: ")) - 1
            if 0 <= user_input < len(antex_files):
                return antex_files[user_input]
            else:
                print("Número inválido. Intente de nuevo.")
        except ValueError:
            print("Entrada inválida. Intente de nuevo.")

# Solicitar al usuario que seleccione el archivo ANTEX de su antena receptora
antex_file = select_antex_file(antex_folder)

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
    
    # Función rtkplot para representar el archivo .pos
    def run_rtkplot(rtkplot_exe, pos_file):
        cmd = [rtkplot_exe, pos_file]
        subprocess.run(cmd)
    
    def ask_user_to_plot():
        while True:
            user_input = input("¿Desea ver gráficamente los resultados? (0: No, 1: Sí): ")
            if user_input in ['0', '1']:
                return int(user_input)
            else:
                print("Entrada no válida. Por favor, ingrese 0 o 1.")

    # Llamada a la función para preguntar al usuario
    plot_choice = ask_user_to_plot()

    if plot_choice == 1:
        # Encuentro el archivo .pos a representar
        pos_file = os.path.join('C:\IPNA\data', 'POST', f"{septentrio_filename_base}.pos")
        run_rtkplot(rtkplot_exe, pos_file)
    
    
    
    
    
    