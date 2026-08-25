# BCRAonline — Guía de Arquitectura y Desarrollo

Este archivo sirve como mapa y manual de referencia rápido para desarrolladores y asistentes de IA. **Léase antes de realizar cualquier edición o modificación en el código.**

---

## 🗺️ Mapa de Archivos (¿Dónde editar?)

Dependiendo del cambio que desees realizar, edita el archivo correspondiente:

| Objetivo del Cambio | Archivo a Modificar | Descripción |
|---|---|---|
| **Agregar/quitar variables de la API** | [fetch_data.py](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/fetch_data.py) | Modifica la lista `VARIABLE_IDS` con los IDs de la API v4.0. |
| **Registrar nuevas variables en el frontend** | [assets/js/app.js](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/assets/js/app.js) | Modifica el array `window.VARIABLES` y el objeto `PANELS` para asignarla a una pestaña. |
| **Cambiar colores, fuentes o diseño general** | [assets/css/style.css](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/assets/css/style.css) | Administra los estilos visuales, variables CSS (`:root`), layouts responsivos y menús. |
| **Modificar el gráfico o la descarga del CSV** | [assets/js/main_chart.js](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/assets/js/main_chart.js) | Controla la inicialización de Chart.js, colores de línea y la estructura de exportación CSV. |
| **Modificar la barra de navegación o estructura base** | [index.html](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/index.html) | Define el esqueleto del sitio, los links de navegación lateral y los contenedores del gráfico/tabla. |
| **Cambiar la frecuencia de actualización diaria** | [.github/workflows/update_data.yml](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/.github/workflows/update_data.yml) | Ajusta el cron de ejecución automática en los servidores de GitHub. |
| **Ajustar el comportamiento offline o caché** | [sw.js](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/sw.js) | Gestiona los archivos cacheados para el soporte Progressive Web App (PWA). |
| **Cambiar el nombre de la app instalable en móvil** | [manifest.json](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/manifest.json) | Modifica los metadatos PWA (nombre, colores, accesos directos). |

---

## 🛠️ Flujo de Trabajo Recomendado

### Para agregar una nueva variable económica:
1. **Paso 1 (Backend)**: Busca el ID de la variable en el catálogo [variables_disponibles.md](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/variables_disponibles.md). Añade el ID al array `VARIABLE_IDS` en [fetch_data.py](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/fetch_data.py).
2. **Paso 2 (Frontend)**: Declara la variable en `window.VARIABLES` dentro de [assets/js/app.js](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/assets/js/app.js) con su unidad de medida y formato.
3. **Paso 3 (Paneles)**: Asigna el ID de la variable a uno de los arreglos del objeto `PANELS` en [assets/js/app.js](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/assets/js/app.js) para que se renderice en la sección adecuada.
4. **Paso 4 (Opcional - Gráfico)**: Si quieres que aparezca como pestaña rápida en el gráfico dinámico, agrega el `<button>` en [index.html](file:///c:/Users/Camurri/Documents/Antigravity/12_Bcraonline/index.html) bajo el div `#chart-tabs`.

---

## 🚀 Despliegue en Producción
Todos los datos son auto-actualizados mediante **GitHub Actions**. Para desplegar cambios de diseño o lógica:
1. Sube los archivos locales al repositorio en GitHub.
2. La web pública en GitHub Pages se actualizará automáticamente en un par de minutos tras el commit.
