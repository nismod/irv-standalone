export const devProxy = {
  '/raster': {
    target: 'http://localhost:5001',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/raster/, ''),
  },
  '/vector': {
    target: 'http://localhost:8800',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/vector/, ''),
  },
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ''),
  },
  '/admin': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/admin$/, '/admin/'),
  },
  '/static/': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/static\//, '/static/'),
  },
  '/martor/': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/martor\//, '/martor/'),
  },
  '/pixel': {
    target: 'http://localhost:5080',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/pixel/, ''),
  },
};
