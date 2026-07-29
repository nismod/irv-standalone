// local dev config when running the backend with docker compose
export const devProxy = {
  '/raster': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/raster/, '/raster'),
  },
  '/vector': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/vector/, '/vector'),
  },
  '/api': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '/api'),
  },
  '/admin': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/admin$/, '/admin/'),
  },
  '/static/': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/static\//, '/static/'),
  },
  '/media/': {
    target: 'http://localhost',
    changeOrigin: true,
  },
  '/martor/': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/martor\//, '/martor/'),
  },
  '/pixel': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/pixel/, '/pixel'),
  },
  '/accounts': {
    target: 'http://localhost',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/accounts$/, '/accounts/'),
  },
};
