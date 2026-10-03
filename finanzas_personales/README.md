# ActividadInvestigativa-Grupo2

## Cómo ejecutar el proyecto

Abre la carpeta `finanzas_personales` en VS Code, abre una terminal y ejecuta, en este orden:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Esto se hace **una sola vez**. Después, cada vez que quieras trabajar:

```
.venv\Scripts\activate
python main.py
```

> Si PowerShell muestra un error de "ejecución de scripts deshabilitada", ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Estructura del proyecto

```
finanzas_personales/
├── main.py              # Punto de entrada
├── requirements.txt     # Librerías del proyecto
├── database/            # Conexión y tablas (SQLite)
├── modulos/             # Lógica: transacciones, metas, reportes
├── servicios/           # Envío de correos
├── interfaz/            # Menú
└── datos/               # Base de datos local (no se sube)
```