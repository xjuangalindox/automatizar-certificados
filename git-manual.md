# QUE HACER SI LAS CREDENCIALES ESTÁN RASTREADAS

## 1. Crear `.gitignore`
```
gitignore
venv/
__pycache__/
*.pyc
credentials.json
token.json
```

## 2. Instalar `git-filter-repo` en el entorno virtual
```
./venv/Scripts/python.exe -m pip install git-filter-repo
```

## 3. Limpiar historial
```
./venv/Scripts/git-filter-repo.exe --path credentials.json --path token.json --invert-paths --force
```

## 4. Volver a agregar el remoto
```
git remote add origin https://github.com/xjuangalindox/automatizar-certificados.git
git remote -v
```

## 5. Rastrear todos los archivos
```
git add .
```

## 6. Comprometer archivos rastreados
```
git commit -m "nueva version"
```

## 5. Push forzado
```
git push origin main --force
```