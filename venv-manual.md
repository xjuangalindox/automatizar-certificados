# CONFIGURAR PYTHON
# _______________________________________________________________________

## 1. Crear y activar entorno virtual (desde la raíz del proyecto)
```bash
python -m venv venv
venv/Scripts/activate
```

## 2. Instalar librerías necesarias
```bash
./venv/Scripts/python.exe -m pip install google-auth-httplib2 google-auth-oauthlib google-api-python-client
```

## 3. Ejecutar el script principal
```bash
python app.py
```
