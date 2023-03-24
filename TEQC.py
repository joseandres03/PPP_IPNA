# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 22:38:31 2023

@author: Jose Andres Ramos Mendoza
"""

import os
import subprocess

# Solicita al usuario la ubicación de las carpetas de entrada y salida
input_folder = input('Introduce la ubicación de la carpeta que contiene los archivos de entrada: ')
output_folder = input('Introduce la ubicación de la carpeta donde se guardarán los archivos convertidos: ')

# Itera sobre todos los archivos en la carpeta de entrada
for filename in os.listdir(input_folder):
    # Divide el nombre del archivo en su nombre base y su extensión
    file_base, file_ext = os.path.splitext(filename)

    # Construye las rutas completas a los archivos de entrada y salida
    input_file = os.path.join(input_folder, filename)
    obs_output_file = os.path.join(output_folder, file_base + '.21o')
    nav_output_file = os.path.join(output_folder, file_base + '.21n')

    # Construye el comando Teqc
    teqc_command = ['teqc', '+obs', obs_output_file, '+nav', nav_output_file, input_file]

    # Ejecuta el comando Teqc
    subprocess.run(teqc_command)
