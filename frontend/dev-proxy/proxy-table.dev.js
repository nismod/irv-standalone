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
  '/static/admin': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/static\/admin/, '/static/admin/'),
  },
  '/pixel': {
    target: 'http://localhost:5080',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/pixel/, ''),
  },
};
