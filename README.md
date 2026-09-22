# StartTrucks

Aplicación web para la agilizar los procesos y la gestión operativa de vehículos, maquinaria y personal de obra.

## Estado actual

- Login y registro de usuarios.
- Roles internos para permisos: `Administrativo`, `Mecánico` y otros puestos operativos.
- Identidad configurable por empresa. Por defecto se muestra `StartTrucks`.
- Logo y nombre de empresa configurables desde Administración.
- Diseño responsive para ordenador, tablet y móvil.
- Menú para repostajes, mantenimientos, partes, daños, compras, vehículos, usuarios e informes.

- Botón de inicio funcional para volver al menú principal.

## Revisiones preventivas

La sección está disponible únicamente para usuarios con rol `Administrativo` o `Mecánico`.

| Columna | Campo |
| --- | --- |
| A | Matrícula |
| B | Vehículo o alias |
| C | Clasificación: Camión, Bañera, Remolque, Coche o Máquina |
| D | Fecha de la última revisión |
| E | Mantenimiento: Cambio de aceite y filtros, Aceites u Otros |
| F | Email |
| G | Días para el vencimiento |
| H | Fecha de vencimiento |
| I | Estado |
| J | Estado del email |
| K | Estado operativo: Operativo o Inactivo |
| L | Observaciones |

Los campos G, H, I y J son automáticos. En una ficha existente solo se puede modificar la fecha de la última revisión.

Cada cambio de fecha genera un histórico con matrícula, vehículo, fecha anterior, fecha nueva, usuario y fecha/hora del cambio. Las tarjetas de próximos vencimientos y vencidos filtran directamente el listado.

## Fórmulas de referencia

### Columna G

```excel
=SI(D5="";"";H5-HOY())
```

### Columna H

```excel
=SI(D5="";"";SI(C5="";"";D5+BUSCARV(MINUSC(C5);{"coche"\180;"Camion"\150;"Bañera"\70;"Remolque"\365;"Maquina"\60};2;FALSO)))
```

### Columna I

```excel
=SI(H9="";"";SI(H9-HOY()<0;"Vencido";SI(H9-HOY()<=7;"Próximo a vencer";"OK")))
```

## Históricos y permisos

- Los usuarios normales solo visualizan sus propios registros.
- El administrador puede consultar todos los registros.
- La descarga de informes está limitada al administrador.
- El módulo preventivo filtra también su histórico por usuario.
- El rol se usa para permisos, pero la interfaz muestra el nombre y el puesto.
- Revisiones preventivas: acceso para `Administrativo` y `Mecánico`.
- ITV y Seguros: acceso reservado a `Administrativo`.

## Correos de vencimiento

La columna J queda preparada para mostrar `Enviado` después de enviar un aviso. El envío con `GmailApp` se realizará mediante un Google Apps Script independiente con `doPost`, usando el email de cada registro y la copia definida en el script. La misma lógica podrá aplicarse a mantenimientos, ITV y seguros sin mezclar clientes.

## Identidad y PDFs

- Paleta: grafito `#1A1A1A`, azul medianoche `#212239`, amarillo tráfico `#FFB800` y blanco `#FFFFFF`.
- Logo de StartTrucks como marca predeterminada.
- Logo de empresa configurable desde Administración.
- Los nuevos PDFs pueden incorporar logo, nombre, teléfono y email de la empresa configurada.
- Los PDFs ya generados no se modifican.

## Arquitectura y almacenamiento

- Frontend: `index.html` con HTML, CSS y JavaScript.
- Backend local: `server.py`.
- Base de datos local: SQLite en `datos/gestion_operativa.db`.
- Datos operativos locales: IndexedDB del navegador.
- Archivos y fotos: carpetas dentro de `datos/`.
- Excel preventivo: separado del Excel general y preparado para alojarse en la nube.
- No se utilizará Google Drive como almacenamiento de la aplicación.

## Ejecución local

```powershell
cd "C:\Users\dadam\OneDrive\Escritorio\APP"
python server.py
```

Abrir `http://localhost:8000`.

Durante el desarrollo se puede usar un túnel temporal para probar desde el móvil. No es un enlace permanente de producción.

## Publicación prevista

La aplicación se publicará en Azure cuando el módulo preventivo, permisos, históricos, correos y almacenamiento estén preparados y probados.

```text
Azure App Service
└── Azure Storage
	└── Archivos separados por cliente
```

## Pendiente

- Conectar el `doPost` de Google Apps Script para los avisos.
- Terminar las pantallas de ITV y Seguros.
- Sustituir el almacenamiento local por almacenamiento cloud al publicar en Azure.
- Completar pruebas con varios usuarios y clientes.
