# PhotoViewer360 - wersja polska
Wtyczka umożliwiająca import i wizualizację zdjęć panoramicznych w programie QGIS. Oparta na wtyczce EquirectangularViewer.

## Funkcjonalność wtyczki
* import folderu ze zdjęciami posiadającymi georeferencję i utworzenie z nich pliku GeoPackage 
* przeglądanie zdjęć panoramicznych poprzez narzędzia do nawigacji oraz przy użyciu "łapki" oraz scrolla myszki
* wyświetlanie informacji nt. przeglądanego zdjęcia, tj: nr drogi, nazwa ulicy, nr odcinka, kilometraż i data wykonania
* przechodzenie pomiędzy zdjęciami poprzez wybór punktu na mapie bądź kliknięcie na hotspot podczas przeglądania zdjęcia
* możliwość wykanania zrzutu ekranu z aktualnym widokiem zdjęcia 

## Wymagania dot. importowanych zdjęć
* format JPG
* dane EXIF zawierające: szerokość i długość geograficzną, azymut kierunku głównego, datę wykonania
* nazwa zdjęć wg schematu: nrDrogi_nazwaUlicy_nrOdcinka_kilometraż

## Uwaga
Warunkiem koniecznym do prawidłowego działania wtyczki jest posiadanie  wersji QGIS 3.22 lub wyższej.

# PhotoViewer360 - english version
QGIS Plugin for importing and visualising local panoramic images. Based on EquirectangularViewer.

## Plugin functionality
* importing folder with geotagged panoramic photos and creating GeoPackage file with them
* viewing panoramic photos by navigation tool or with Pan Tool and mouse scroll
* dispalying informations about: road number, name of the street, number of section, mileage and date the photo was taken
* switching between photos by selecting a point on the map or clicking on the hotspot while viewing the photo
* ability of taking a creenshot with current view of photo

## Photo requirements
* JPG format
* EXIF data containing: latitude and longitude, main direction azimuth, date the photo was taken
* name of photo according to the scheme: roadNumber_streetName_sectionNumber_mileage
