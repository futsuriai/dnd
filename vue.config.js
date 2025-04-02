module.exports = {
  publicPath: process.env.NODE_ENV === 'production'
    ? '/dnd/'
    : '/',
  outputDir: 'dist'
}
