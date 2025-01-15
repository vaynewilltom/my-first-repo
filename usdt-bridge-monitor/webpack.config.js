const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: {
    renderer: './src/renderer/index.tsx',
    preload: './src/preload.ts'
  },
  target: 'electron-renderer',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name]/[name].js'
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    alias: {
      '@types': path.resolve(__dirname, 'src/types')
    }
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-typescript',
              '@babel/preset-react'
            ]
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/renderer/index.html',
      filename: 'renderer/index.html',
      chunks: ['renderer']
    })
  ]
};
