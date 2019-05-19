
# Imagem Cinemática

**Imagem cinemática** é um projeto de Iniciação Científica desenvolvido pelo Orientando [Bruno Abude Cardoso][Bruno-Lattes], e por seu Orientador [Gustavo Voltani Von Atzingen][Gustavo-Lattes].  

## Resumo  
O projeto consiste na criação de um Software, desenvolvido na linguagem [Python](https://www.python.org/), para auxiliar em experimentos de Física Básica que envolvem a análise cinemática de objetos em movimento.

## Configuração do Ambiente de Desenvolvimento
Para executar o software é preciso configurar o ambiente de trabalho. Nesta seção é mostrado o processo passo-a-passo com as dependências necessárias para a plataforma _Windows_. Ao final há um resumo com as depêndencias necessárias (Para usuários mais experientes).

### Python 2.7.x
O primeiro passo é instalar o interpretador da linguagem [Python, versão 2.7](https://www.python.org/downloads/ "Página de Download do Interpretador").
A versão utilizada no projeto atualmente é a 2.7.13.

É aconselhável instalar o interpretador no local padrão ``C:\Python27``.

### Virtualenv
Virtualenv é um utilitário que permite criar ambientes diferentes para cada projeto desenvolvido em linguagem ``Python``. Primeiro é necessário instalar o aplicativo através da linha de comando:
```
pip install virtualenv
```
Após instalado, crie um diretório para o projeto. Acesse o diretório pelo prompt de comando e execute o seguinte comando:
```
virtualenv env
```
Este comando irá criar um novo ambiente na pasta ``env``. Caso algum dos comandos não esteja funcionando, verifique se o caminho para o diretório de instalação do Python está configurado na variável ``PATH`` do **Windows**.

Ainda no diretório onde está localizada a pasta env, execute o seguinte comando:
```
env\Scripts\activate
```

Se o comando foi executado corretamente, deve aparecer ``(env)`` antes do diretório no prompt de comando, por ex:
```
(env) D:\projeto
```

### Numpy, Matplotlib
Para instalar o [Numpy](http://www.numpy.org/) e o [Matplotlib](http://matplotlib.org/), basta executar os seguintes comandos:
```
pip install numpy
pip install matplotlib
```

### MinGW
Obtenha o instalador do ``MinGW`` no link http://www.mingw.org/ em **Download Installer**. O ``MinGW`` será necessário para a instalação do ``Qt 4.8.6``.

### Qt 4.8.6
Para instalar o Qt 4.8.6, basta acessar o link https://download.qt.io/archive/qt/4.8/4.8.6/qt-opensource-windows-x86-mingw482-4.8.6-1.exe.

### SIP/PyQT4
Basta instalar o PyQt4 (v4.11) acessando o link https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11/PyQt4-4.11-gpl-Py2.7-Qt4.8.6-x32.exe/download.

### OpenCV 3.0.0
Obtenha a versão já compilada do OpenCV 3.0.0 no link
https://sourceforge.net/projects/opencvlibrary/files/opencv-win/3.0.0/opencv-3.0.0.exe/download. Extraia os arquivos para uma pasta conhecida.
Acesse o diretório ``<opencv>\build\x86\vc12\bin` e copie o arquivo ``opencv_ffmpeg300.dll`` e cole no mesmo diretório onde o ``Python`` está instalado.

### Copiar arquivos para a pasta env
O PyQt4 é instalado por padrão no diretório onde está instalado o interpretador da linguagem Python. É necessário copiar os arquivos para a pasta ``env`` criada anteriormente.
Acesse ``C:\Python27\Lib\site-packages`` e copie os arquivos ``sip.pyd`` e o diretório ``PyQt4`` e cole na pasta ``env\Lib\site-packages``.

Acesse ``<Diretório onde o OpenCV foi extraído>\build\python\2.7\x86`` e copie o arquivo ``cv2.pyd`` também para a pasta ``env\Lib\site-packages``

## Lista completa das dependências
1. [Python 2.7.x](https://www.python.org/downloads/)
2. [MinGW](http://www.mingw.org/)
3. [Qt 4.8.x](https://download.qt.io/archive/qt/4.8/)
4. [PyQt4 e SIP](https://www.riverbankcomputing.com/software/pyqt/download)
5. [Numpy](http://www.numpy.org/)
6. [Matplotlib](http://matplotlib.org/)
7. [OpenCV 3.0](http://opencv.org/releases.html)
8. [Virtualenv](https://virtualenv.pypa.io/en/stable/)

[Bruno-Lattes]:http://lattes.cnpq.br/4417643293268234 "Currículo Lattes"
[Gustavo-Lattes]:http://lattes.cnpq.br/5173282107514295 "Currículo Lattes"
