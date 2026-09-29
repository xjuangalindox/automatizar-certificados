# QUE HACER SI LAS CREDENCIALES ESTÁN RASTREADAS

## 1. Crear `.gitignore` con el nombre de las credenciales
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

---

# CONFIGURAR GIT POR PRIMERA VEZ

## 1. Configurar nombre de usuario
```bash
git config --global user.name "Juan Galindo"
```

## 2. Configurar correo
```bash
git config --global user.email "xjuangalindox@gmail.com"
```

## 3. Verificar configuración
```bash
git config --list
```

## 4. Inicializar repositorio en carpeta del proyecto
```bash
git init
```

## 5. Agregar remoto (ejemplo con GitHub)
```bash
git remote add origin https://github.com/xjuangalindox/automatizar-certificados.git
git remote -v
```

## 6. Primer commit y push
```bash
git add .
git commit -m "primer commit"
git push -u origin main
```