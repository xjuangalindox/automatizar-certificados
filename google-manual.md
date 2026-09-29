# GOOGLE MANUAL
# _______________________________________________________________________

## 1. Crear proyecto en Google Cloud Console
- Ir a [https://console.cloud.google.com](https://console.cloud.google.com)
- Crear un nuevo proyecto o seleccionar uno existente.

---

## 2. Habilitar APIs necesarias
- Menú → **APIs y servicios → Biblioteca**
- Buscar y habilitar:
  - **Google Drive API**
  - **Gmail API**

---

## 3. Configurar pantalla de consentimiento OAuth
- Menú → **APIs y servicios → Pantalla de consentimiento OAuth**
- Completar datos básicos de la aplicación.
- En sección **Usuarios de prueba**, agregar tu correo institucional y personal.

---

## 4. Crear credenciales OAuth
- Menú → **APIs y servicios → Credenciales**
- Crear credencial tipo **ID de cliente OAuth** → Aplicación de escritorio.
- Descargar el archivo `credentials.json`.
- Guardar en la raíz del proyecto (pero en `.gitignore`).

---

## 5. Autenticación inicial
- Ejecutar tu script con los SCOPES necesarios:
  ```python
  SCOPES = [
      'https://www.googleapis.com/auth/drive',
      'https://www.googleapis.com/auth/gmail.send'
  ]
  ```
