const { defineConfig } = require('@vue/cli-service');
const staticDir = "../static/travel";
const templatePath = "../../templates/travel/index.html";

module.exports = defineConfig({
  transpileDependencies: true,
  outputDir: process.env.NODE_ENV === 'production' ? staticDir : 'dist/',
  // Куда пойдёт шаблон проекта
  indexPath: process.env.NODE_ENV === 'production' ? templatePath : 'index.html',
  // Куда пойдут ассеты (относительно outputDir)
  assetsDir: '', // ассеты храним там же, где и JS/CSS
  // Путь по которому можно достать статику
  // Нужно указать тот, который прописан в STATIC_URL настроек django
  publicPath: process.env.NODE_ENV === 'production' ? '/static/travel' : '/',
});
