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
