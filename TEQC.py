# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 22:38:31 2023

@author: Jose 1
"""

import os
import subprocess

# Solicita al usuario la ubicación de la carpeta que contiene los archivos de entrada y el ejecutable teqc
input_folder = input('Introduce la ubicación de la carpeta que contiene los archivos de entrada y el ejecutable teqc: ')

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
    if file_base == 'teqc' and file_ext == '.exe':
        continue

    # Construye las rutas completas a los archivos de entrada y salida
    input_file = os.path.join(input_folder, filename)
    obs_output_file = os.path.join(obs_output_folder, file_base + '.o')
    nav_output_file = os.path.join(nav_output_folder, file_base + '.n')

    # Construye el comando Teqc
    teqc_command = ['teqc', '+obs', obs_output_file, '+nav', nav_output_file, input_file]

    # Ejecuta el comando Teqc
    subprocess.run(teqc_command)
