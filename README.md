# ImageRescale
dist文件夹中有编译好文件，双击运行即可。
或者终端中使用：
./ImageRescale_(版本号)
打包成程序（ubuntu）：
pyinstaller -F -w --hidden-import=PIL._tkinter_finder  ImageRescale.py --icon=icon.ico

ubuntun打包win和mac：
# 1. 安装 Docker
sudo apt install docker.io

# 2. Windows 打包
docker run -v "$PWD:/src" cdrx/pyinstaller-windows

# 3. macOS 打包
docker run -v "$PWD:/src" cdrx/pyinstaller-darwin



需要依赖总结：
pip install pyinstaller
pip install PyQt5 pillow cairosvg pdf2image