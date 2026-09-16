# 📊 Gestión Operativa

Una aplicación web para recopilar datos y agilizar procesos operativos con múltiples usuarios.

## ✨ Características

- ✅ **Interfaz intuitiva** - Formulario fácil de usar
- ✅ **Almacenamiento local** - Datos guardados en IndexedDB (navegador)
- ✅ **Múltiples usuarios** - Acceso simultáneo sin conflictos
- ✅ **Velocidad** - Respuesta instantánea
- ✅ **Exportar datos** - Descarga en formato CSV
- ✅ **Estadísticas** - Total de registros y registros de hoy
- ✅ **Responsive** - Funciona en dispositivos móviles

## 🚀 Cómo usar

### Opción 1: Abrir directamente en el navegador
```bash
# En Windows, simplemente abre el archivo:
# Haz doble clic en: index.html
```

### Opción 2: Usar un servidor Python (recomendado para múltiples usuarios remotos)
```bash
# Abre PowerShell o terminal
# Navega a la carpeta del proyecto
cd "c:\Users\dadam\OneDrive\Escritorio\David\APP"

# Ejecuta el servidor
python server.py
```

Luego accede a: **http://localhost:8000**

### Opción 3: Usar un servidor simple de Python (alternativa)
```bash
# Dirección simple
python -m http.server 8000
```

## 📋 Formulario

El formulario incluye los siguientes campos:
- **Nombre** - Nombre completo del usuario
- **Email** - Correo electrónico
- **Categoría** - Tipo de dato (Retroalimentación, Encuesta, Queja, Sugerencia, Otro)
- **Mensaje** - Descripción detallada

## 📊 Vista de Datos

- **Total de registros** - Cuenta todos los datos guardados
- **Registros de hoy** - Datos ingresados en la fecha actual
- **Tabla de datos** - Visualización de todos los registros
- **Botón Actualizar** - Recarga los datos (automático cada 2 segundos)
- **Descargar CSV** - Exporta todos los datos en formato CSV
- **Limpiar todo** - Elimina todos los datos (⚠️ irreversible)

## 💾 Almacenamiento

Los datos se guardan en **IndexedDB**, que es:
- ✅ Local (no se envía a ningún servidor)
- ✅ Persistente (se mantienen incluso al cerrar el navegador)
- ✅ Rápido
- ✅ Seguro

## 🔄 Cómo acceder desde otros dispositivos

Si el servidor está ejecutándose en tu computadora:
1. Encuentra tu IP local: `ipconfig` en PowerShell
2. Otros usuarios pueden acceder a: `http://[TU_IP]:8000`

Ejemplo: `http://192.168.1.100:8000`

## 📥 Datos de múltiples usuarios

Cuando múltiples usuarios envían datos simultáneamente:
- Cada usuario ve los datos en tiempo real (actualización cada 2 segundos)
- Los datos se sincronizan automáticamente
- No hay pérdida de información

## ⚙️ Archivo de configuración para servidor Node.js

Si en el futuro deseas usar Node.js en lugar de Python, ejecuta:
```bash
npm install
npm start
```

## 🛠️ Futuras mejoras

- [ ] Backend en Node.js o Python con base de datos SQL
- [ ] Autenticación de usuarios
- [ ] Búsqueda y filtrado de datos
- [ ] Gráficos y análisis
- [ ] Notificaciones en tiempo real

## ❓ Preguntas frecuentes

**P: ¿Dónde se guardan los datos?**
A: En IndexedDB del navegador. Cada navegador/dispositivo tiene su propia base de datos.

**P: ¿Se pierden los datos si cierro el navegador?**
A: No, IndexedDB es persistente. Los datos se mantienen.

**P: ¿Puedo acceder desde mi teléfono?**
A: Sí, si el servidor está activo y accedes a la IP local de tu computadora.

**P: ¿Cómo exporto los datos?**
A: Haz clic en "💾 Descargar CSV" en la sección de datos.

---

**Creado con ❤️ para recopilar datos de forma rápida y eficiente**
