# PPP_IPNA
## José Andrés Ramos Mendoza

PPP_IPNA es un repositorio de procesamiento GNSS de código abierto, que emplea otros softwares como TEQC y RTKlib.

## Introducción
Este repositorio surgió a partir del trabajo realizado durante la estancia de 2 meses que realicé en el IPNA-CSIC, para la asignatura de prácticas externas del grado en física de la ULL. Mi objetivo en estos meses fue el de desarrollar un código Python que fuese capaz de procesar archivos propietarios que contengan información sobre la geolocalización de un receptor GNSS, que fue instalado en el volcán de La Palma en 2021 con la finalidad de hacer un estudio geodésico durante su erupción.

PPP_IPNA se diseñó tomando como base las herramientas que proporcionan los softwares/librerias TEQC y RTKlib. Concretamente, se desarrolló para obtener soluciones de geoposicionamiento usando la técnica PPP-Static que ofrece el RTKlib, aunque su código (de acceso público) puede modificarse para emplear otras técnicas como PPP-Fixed, PPP-Dinamic, etc.

Por otro parte, el código está preparado para realizar de forma automática la descarga de los archivos de corrección (SP3, CLK, DCB, etc) necesarios desde la web de CDDIS, haciendo que el uso por parte del usuario sea lo más fácil y cómodo posible.

## Características
¿Cuáles son las características principales del código PPP_IPNA?
- Conversión automatizada de archivos propietarios a formato estandarizado RINEX.
- Procesado de los datos mediante RTKlib y los archivos de correción SP3, CLK, ERP, DCB, IONEX, BLQ y ANTEX.
- Representación gráfica de series temporales para un día o para un intervalo de tiempo mayor.

## Requisitos previos
- Usar un equipo con sistema Windows (RTKlib solo proporciona los ejecutables para este sistema).
- Tener instalado WinRAR e intrucida la ruta al ejecutable WinRAR.exe en el PATH de las variables de entorno.
- Descargar las librerias necesarias en su entorno Python/Conda (se recomienda usar un entorno independiente).
- Regístrese en la web del CDDIS (https://urs.earthdata.nasa.gov/users/new?client_id=gDQnv1IO0j9O2xXdwS8KMQ&redirect_uri=https%3A%2F%2Fcddis.nasa.gov%2Fproxyauth&response_type=code&state=aHR0cDovL2NkZGlzLm5hc2EuZ292L2FyY2hpdmUvZ25zcy9wcm9kdWN0cy8)
- Cree un archivo de texto en la carpeta \Usuarios\Usuario que contenga la siguiente:
machine urs.earthdata.nasa.gov login "username" password "password"
 Sustituya "username" y "password" por sus credenciales de acceso a la web del CDDIS (Por ejemplo: machine urs.earthdata.nasa.gov login MIKE password Gnss00).
 Con este paso el código descargará automaticamente los archivos de correción necesarios.

## Instalación
Si cumple con los requisitos enumerados en la sección previa, puede proceder a la instalación del proyecto.
Descarga el ZIP del repositorio PPP-IPNA. Al descomprimirlo se generará una carpeta que contendrá las subcarpetas bin, data, executables y demás. Esa carpeta principal debe estar en su disco local C llamada IPNA, de tal manera que la ruta a la carpeta data (por ejemplo) sea "C:\IPNA\data".
Abre el código Python (CodigoIPNA.py) dentro del entorno donde estan descargadas las librerias necesarias (ver archivo Requirements)

## Uso
Una vez haya instalado el proyecto podrá usarlo de la siguiente manera:
1) Por defecto, en las subcarpetas contenidas en \data habrá un archivo para usar como version de prueba, recuerde borrarlos (los archivos) antes de usar el código para su proyecto.
2) En la subcarpeta *ANTEX* habrá dos archivos por defecto: igs20.atx ; Tallysman_Wireless_VP6050C.atx  . El primero no debe borrarlo, pues contiene informacion de calibración sobre los satélites. EL segundo es el archivo de calibracion para la antena que usamos en el volcan de La Palma. Busque el archivo archivo de su antena en la web https://www.ngs.noaa.gov/ANTCAL/ e introdúzcalo en esta carpeta (recuerde que el formato es .atx).
3) Obtenga el archivo BLQ asociado a la localización donde instaló su antena GNSS. Puede obtenerlo en la herramienta de la Chalmers University of Tecnology (http://holt.oso.chalmers.se/loading/). Introdúzcalo en la subcarpeta *OTL_BLQ*.
4) Si ya borró los archivos de prueba dentro de las carpetas *POST*, *your_archives* y *your_results*, introduzca en la subcarpeta *your_archives* (contenida en la carpeta data) sus archivos generados por la antena receptora de señales GNSS.
5) Ejecute el código Python proporcionado (IPNA\CodigoIPNA.py). Al comienzo le pedirá por pantalla qué archivo de la carpeta .atx y .blq quiere usar (solo si hay varios de estos en sus respectivas carpetas).
6) Al terminar de ejecutarse, en la carpeta *your_results* tendrá las gráficas con los resultados.
