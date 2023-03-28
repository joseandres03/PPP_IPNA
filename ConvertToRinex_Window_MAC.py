# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 11:20:25 2023

@author: Jose 1
"""

import platform
import os
import subprocess

sistema = platform.system()

if sistema == 'Windows':
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

if sistema == 'Darwin':

    from pathlib import Path
    import shutil

    def convertToRinex():
        filesDirectory = input("Escribe el directorio completo a la carpeta que solamente contiene los archivos a convertir a RINEX: ")
        filesToConvert = os.listdir(filesDirectory)
        rinexFilesFolder = os.path.join(filesDirectory, "rinexFiles")
    
        # We create a folder in our directorh where the RINEX files will be saved
        try:
            os.makedirs(rinexFilesFolder)
        except FileExistsError:
            pass
        # Inside the folder of RINEX files we create 2 folders for navegation files and observation files:
        navFilesFolderDir = os.path.join(rinexFilesFolder, "navFiles")
        obsFilesFolderDir = os.path.join(rinexFilesFolder, "obsFiles")

        try:
            os.makedirs(navFilesFolderDir)
        except FileExistsError:
            pass

        try:
            os.makedirs(obsFilesFolderDir)
        except FileExistsError:
            pass

        # Process to convert our raw data to RINEX 2.11 files and save them in the corresponding folders:
        for file in filesToConvert:
            if file != "teqc" or file != "teqc.exe":
                fileName = file.split(".")[0]
                os.chdir(filesDirectory)
                obsFile = fileName + ".o"
                navFile = fileName + ".n"
                teqc_command = ['teqc', '+obs', obsFile, '+nav', navFile, file]
                subprocess.run(teqc_command)
                obsFileDir = os.path.join(filesDirectory, obsFile)
                obsFileNewDir = os.path.join(obsFilesFolderDir, obsFile)
                navFileDir = os.path.join(filesDirectory, navFile)
                navFileNewDir = os.path.join(navFilesFolderDir, navFile)
                shutil.move(obsFileDir, obsFileNewDir)
                shutil.move(navFileDir,navFileNewDir)
            if file == "teqc" or file == "teqc.exe":
                continue