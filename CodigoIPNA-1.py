# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 11:51:32 2023

@author: Jose Andres
"""

import requests
import georinex as gr
import subprocess
import os
import platform
from datetime import datetime
import urllib.request

def convert_septentrio_to_rinex(input_folder):
    
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

    # Crea las subcarpetas para los archivos de salida si no existen
    obs_output_folder = os.path.join(input_folder, 'obs_output')
    if not os.path.exists(obs_output_folder):
        os.makedirs(obs_output_folder)

    nav_output_folder = os.path.join(input_folder, 'nav_output')
    if not os.path.exists(nav_output_folder):
        os.makedirs(nav_output_folder)

    # Itera sobre todos los archivos en la carpeta de entrada
    for filename in os.listdir(input_folder):
        # Divide el nombre del archivo en su nombre base y su extensión
        file_base, file_ext = os.path.splitext(filename)

        # Ignora el ejecutable teqc
        if filename == teqc_executable:
            continue

        # Construye las rutas completas a los archivos de entrada y salida
        input_file = os.path.join(input_folder, filename)
        obs_output_file = os.path.join(obs_output_folder, file_base + '.o')
        nav_output_file = os.path.join(nav_output_folder, file_base + '.n')

        # Construye el comando Teqc
        teqc_command = [os.path.join(input_folder, teqc_executable), '+obs', obs_output_file, '+nav', nav_output_file, input_file]

        # Ejecuta el comando Teqc
        subprocess.run(teqc_command)

def get_date_from_rinex(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if 'TIME OF FIRST OBS' in line:
                year, month, day, hour, minute, second = [int(x) if i != 5 else float(x) for i, x in enumerate(line.strip().split()[0:6])]
                return datetime(year, month, day, hour, minute, int(second))

if __name__ == "__main__":
    # Solicita al usuario la ubicación de la carpeta que contiene los archivos de entrada y el ejecutable teqc
    input_folder = input('Introduce la ubicación de la carpeta que contiene los archivos de entrada y el ejecutable teqc: ')

    # Ejecutar la función convert_septentrio_to_rinex
    convert_septentrio_to_rinex(input_folder)

    # Establecer la ruta a la carpeta de archivos de observación
    obs_output_folder = os.path.join(input_folder, 'obs_output')

    # Encontrar el archivo .o en la carpeta de archivos de observación
    rinex_obs_file = os.path.join(obs_output_folder, os.listdir(obs_output_folder)[0])

    # Leer la fecha de la primera observación
    date_observation = get_date_from_rinex(rinex_obs_file)
    print(f"Fecha y hora de la primera observación: {date_observation}")
