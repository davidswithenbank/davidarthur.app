const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const DIR = __dirname;

const MIME = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.json': 'application/json',
};

http.createServer((req, res) => {
  let url = req.url.split('?')[0];

  // Try the exact path, then directory/index.html, then path.html
  const candidates = [
    url === '/' ? '/index.html' : url,
    url.endsWith('/') ? url + 'index.html' : url + '/index.html',
    url + '.html',
  ];

  function tryNext(i) {
    if (i >= candidates.length) { res.writeHead(404); res.end('Not found'); return; }
    const filePath = path.join(DIR, candidates[i]);
    const ext = path.extname(filePath);
    fs.readFile(filePath, (err, data) => {
      if (err) return tryNext(i + 1);
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      res.end(data);
    });
  }
  tryNext(0);
}).listen(PORT, () => console.log(`Serving on http://localhost:${PORT}`));
