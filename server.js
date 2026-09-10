const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8000;
const HOSTNAME = '0.0.0.0';
const DATA_DIRECTORY = path.join(__dirname, 'datos');
const EXCEL_FILE = path.join(DATA_DIRECTORY, 'data.xlsx');
fs.mkdirSync(DATA_DIRECTORY, { recursive: true });
fs.mkdirSync(path.join(DATA_DIRECTORY, 'imagenes'), { recursive: true });
fs.mkdirSync(path.join(DATA_DIRECTORY, 'documentos-pdf'), { recursive: true });
fs.mkdirSync(path.join(DATA_DIRECTORY, 'copias-seguridad'), { recursive: true });

// Mapear extensiones a content-type
const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.wav': 'audio/wav',
  '.mp4': 'video/mp4',
  '.woff': 'application/font-woff',
  '.ttf': 'application/font-ttf',
  '.eot': 'application/vnd.ms-fontobject',
  '.otf': 'application/font-otf',
  '.wasm': 'application/wasm',
  '.webmanifest': 'application/manifest+json'
};

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/api/gestion-operativa.xlsx') {
    const chunks = [];
    let totalBytes = 0;

    req.on('data', chunk => {
      totalBytes += chunk.length;
      if (totalBytes <= 25 * 1024 * 1024) chunks.push(chunk);
    });

    req.on('end', () => {
      if (totalBytes > 25 * 1024 * 1024) {
        res.statusCode = 413;
        res.end('Archivo demasiado grande');
        return;
      }

      fs.writeFile(EXCEL_FILE, Buffer.concat(chunks), err => {
        if (err) {
          res.statusCode = 500;
          res.end('No se pudo guardar el Excel');
          return;
        }
        res.statusCode = 204;
        res.end();
      });
    });
    return;
  }

  // Seguridad: no permitir acceso a directorios superiores
  let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
  const realPath = path.resolve(filePath);
  
  if (!realPath.startsWith(__dirname)) {
    res.statusCode = 403;
    res.end('Forbidden');
    return;
  }

  // Leer el archivo
  fs.readFile(filePath, (err, data) => {
    if (err) {
      // Archivo no encontrado
      if (err.code === 'ENOENT') {
        res.statusCode = 404;
        res.end('404 - Archivo no encontrado');
      } else {
        res.statusCode = 500;
        res.end(`Server Error: ${err}`);
      }
      return;
    }

    // Establecer content-type
    const ext = path.parse(filePath).ext;
    res.setHeader('Content-Type', mimeTypes[ext] || 'text/plain');
    res.statusCode = 200;
    res.end(data);
  });
});

server.listen(PORT, HOSTNAME, () => {
  console.log(`🚀 Servidor ejecutándose en: http://localhost:${PORT}`);
  console.log(`📁 Sirviendo archivos desde: ${__dirname}`);
  console.log(`🌐 Abre tu navegador y accede a http://localhost:${PORT}`);
  console.log(`\n⏹️  Presiona Ctrl+C para detener el servidor\n`);
});

// Manejar cierre gracioso
process.on('SIGINT', () => {
  console.log('\n\n✋ Servidor detenido.');
  process.exit(0);
});

// Manejar errores
process.on('uncaughtException', (err) => {
  console.error('❌ Error no capturado:', err);
  process.exit(1);
});
