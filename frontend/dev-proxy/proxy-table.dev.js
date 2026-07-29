export const devProxy = {
  '/tiles/raster': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
  '/tiles/vector': {
    target: 'http://localhost:8000',
    changeOrigin: true,
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
  '/media/': {
    target: 'http://localhost:8000',
    changeOrigin: true,
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
  '/accounts': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/accounts$/, '/accounts/'),
  },
};
