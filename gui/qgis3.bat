@ECHO OFF

set OSGEO4W_ROOT=C:\Program Files\QGIS 3.26.1

set PATH=%OSGEO4W_ROOT%\bin;%PATH%
set PATH=%PATH%;%OSGEO4W_ROOT%\apps\qgis\bin

@echo off
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\bin\qt5_env.bat"
call "%OSGEO4W_ROOT%\bin\py3_env.bat"
@echo off
path %OSGEO4W_ROOT%\apps\qgis\bin;%PATH%

cd /d %~dp0

@ECHO ON
call pyuic5 first_window_geo360_base.ui --from-imports -o first_window_geo360_base.py
REM komentarz - call pyrcc5 resources.qrc -o resources.py
@ECHO OFF
GOTO END

:ERROR
   echo "Failed!"
   set ERRORLEVEL=%ERRORLEVEL%
   pause

:END
@ECHO ON