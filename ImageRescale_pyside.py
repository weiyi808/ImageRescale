import sys
import os
import tempfile
import subprocess
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                           QPushButton, QLabel, QLineEdit, QGraphicsView, 
                           QGraphicsScene, QFileDialog, QGraphicsPixmapItem, 
                           QMessageBox, QGridLayout, QSizePolicy, QToolButton, QVBoxLayout)
from PIL import Image, ImageQt
import cairosvg
from pdf2image import convert_from_path

class ImageRescaleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ImageRescale Pro")
        self.setMinimumSize(800, 900)
        
        # 初始化图形场景和视图
        self.scene = QGraphicsScene(self)
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setScene(self.scene)
        
        # 初始化裁剪相关变量
        self.original_image = None
        self.current_image = None
        self.preview_image = None  # 用于预览裁剪结果
        self.image_path = ""
        self.crop_rect = None
        self.drag_start = None
        self.drag_end = None
        self.is_selecting = False  # 是否正在选择区域
        self.crop_confirmed = False  # 是否确认裁剪
        
        # 缩放相关变量
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """创建并布局所有UI组件"""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QGridLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 添加说明面板
        self.create_instructions_panel(main_layout)
        
        # 2. 添加控制面板
        self.create_control_panel(main_layout)
        
        # 3. 添加图像显示区域
        self.create_image_display(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            /* 主窗口背景 - 柔和的紫色渐变 */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 #f8f5ff, stop:1 #f0f8ff);
            }
            
            /* 标签样式 - 紫罗兰色文字 */
            QLabel {
                font-size: 16px;
                color: #6a5acd;
            }
            
            /* 输入框 - 浅紫色边框，半透明背景 */
            QLineEdit {
                padding: 6px;
                font-size: 14px;
                min-width: 80px;
                border: 1px solid #d6d2ff;
                border-radius: 4px;
                background-color: rgba(245, 242, 255, 0.7);
                color: #5d4a9a;
            }
            
            /* 输入框获取焦点效果 */
            QLineEdit:focus {
                border: 1px solid #a5a0ff;
                background-color: rgba(255, 255, 255, 0.9);
            }
            
            /* 按钮 - 紫色渐变，圆角边框 */
            QPushButton {
                padding: 8px;
                font-size: 14px;
                min-width: 100px;
                border: none;
                border-radius: 4px;
                color: #5d4a9a;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #e6e0ff, stop:1 #d0d6ff);
            }
            
            /* 按钮悬停效果 - 稍微变亮 */
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #eee8ff, stop:1 #e0e6ff);
            }
            
            /* 按钮按下效果 - 深一点的颜色 */
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #d8d2ff, stop:1 #c0c6ff);
            }
            
            /* 禁用按钮 - 灰色调 */
            QPushButton:disabled {
                color: #777777;
                background: #e0e0e0;
            }
            
            /* 图像视图 - 淡灰色背景，浅紫色边框 */
            QGraphicsView {
                border: 1px solid #d0d0ff;
                background: #f8f8ff;
            }
            
            
            /* 缩放按钮样式 */
            QToolButton {
                background: rgba(230, 230, 255, 0.9);
                border: 1px solid rgba(200, 200, 255, 0.7);
                border-radius: 4px;
                min-width: 24px;
                min-height: 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: rgba(240, 240, 255, 0.9);
            }
        """)
    
    def create_instructions_panel(self, layout):
        """创建说明面板"""
        instructions = """<b>使用说明：</b>
        1. 参数：宽度、DPI、PDF页码（单栏3.5 双栏7 ，期刊最低300dpi ， 页码从0计数）
        2. 步骤：设置参数->加载图像->选择区域->执行裁剪->保存图像
        
        <b>注意：</b>
        • 使用问题请联系作者：2207201665@qq.com。"""
        
        self.instructions_label = QLabel(instructions, self)
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.instructions_label, 0, 0, 1, 4)
    
    def create_control_panel(self, layout):
        """创建控制面板"""
        # 参数输入行 - 使用单独的网格布局
        control_grid = QGridLayout()
        control_grid.setSpacing(10)
        
        # 第一行：宽度输入
        self.width_label = QLabel("宽度 (英寸):", self)
        self.width_entry = QLineEdit("3.5", self)
        control_grid.addWidget(self.width_label, 0, 0)
        control_grid.addWidget(self.width_entry, 0, 1)
        
        # 第二行：DPI输入
        self.dpi_label = QLabel("DPI:", self)
        self.dpi_entry = QLineEdit("400", self)
        control_grid.addWidget(self.dpi_label, 1, 0)
        control_grid.addWidget(self.dpi_entry, 1, 1)
        
        # 第三行：PDF页码输入
        self.page_label = QLabel("PDF页码:", self)
        self.page_entry = QLineEdit("0", self)
        control_grid.addWidget(self.page_label, 2, 0)
        control_grid.addWidget(self.page_entry, 2, 1)
        
        # 将控制网格添加到主布局
        layout.addLayout(control_grid, 1, 0, 1, 4)
        
        # 加载按钮组
        load_buttons = [
            ("PNG", lambda: self.load_image(is_pdf=False), 2, 0),
            ("JPG", lambda: self.load_image(is_pdf=False), 2, 1),
            ("PDF", lambda: self.load_image(is_pdf=True), 2, 2),
            ("EPS", lambda: self.load_image(is_eps=True), 2, 3)
        ]
        self.create_button_group("加载", load_buttons, layout)
        
        # 保存按钮组
        save_buttons = [
            ("PNG", lambda: self.save_image("png"), 3, 0),
            ("JPG", lambda: self.save_image("jpg"), 3, 1),
            ("PDF", lambda: self.save_image("pdf"), 3, 2),
            ("EPS", lambda: self.save_image("eps"), 3, 3)
        ]
        self.create_button_group("保存", save_buttons, layout)
        
        # 裁剪控制按钮
        self.select_area_btn = QPushButton("选择区域", self)
        self.select_area_btn.clicked.connect(self.start_area_selection)
        layout.addWidget(self.select_area_btn, 4, 0)
        
        self.confirm_crop_btn = QPushButton("执行裁剪", self)
        self.confirm_crop_btn.clicked.connect(self.confirm_crop)
        self.confirm_crop_btn.setEnabled(False)
        layout.addWidget(self.confirm_crop_btn, 4, 1)
        
        self.cancel_crop_btn = QPushButton("取消裁剪", self)
        self.cancel_crop_btn.clicked.connect(self.cancel_crop)
        self.cancel_crop_btn.setEnabled(False)
        layout.addWidget(self.cancel_crop_btn, 4, 2)
        
        self.reset_btn = QPushButton("重置图像", self)
        self.reset_btn.clicked.connect(self.reset_image)
        layout.addWidget(self.reset_btn, 4, 3)
        
        # 状态显示
        self.status_label = QLabel("设置参数->加载图像->选择区域->执行裁剪->保存图像", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label, 5, 0, 1, 4)
    
    def create_labeled_input(self, label_text, default_value, layout, row, col):
        """创建带标签的输入框"""
        label = QLabel(label_text, self)
        entry = QLineEdit(default_value, self)
        entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(label, row, col)
        layout.addWidget(entry, row, col + 1)
        return entry
    
    def create_button_group(self, prefix, buttons, layout):
        """创建统一风格的按钮组"""
        for text, callback, row, col in buttons:
            btn = QPushButton(f"{prefix} {text}", self)
            btn.clicked.connect(callback)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(btn, row, col)
    
   
    def create_image_display(self, layout):
        """创建图像显示区域"""
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)  # 支持拖拽
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # 以鼠标为中心缩放
        self.graphics_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.graphics_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加缩放按钮
        self.create_zoom_buttons()
        
        # 添加鼠标事件处理
        self.graphics_view.viewport().installEventFilter(self)
        layout.addWidget(self.graphics_view, 6, 0, 1, 4)
    
    def create_zoom_buttons(self):
        """创建缩放控制按钮"""
        # 创建按钮容器
        self.zoom_widget = QWidget(self.graphics_view)
        self.zoom_widget.setObjectName("zoom_widget")
        self.zoom_widget.setStyleSheet("background: transparent;")
        
        # 按钮布局
        zoom_layout = QVBoxLayout(self.zoom_widget)
        zoom_layout.setSpacing(5)
        zoom_layout.setContentsMargins(5, 5, 5, 5)
        
        # 放大按钮
        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setText("+")
        self.zoom_in_btn.setToolTip("放大 (Ctrl++)")
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_image(1.2))
        zoom_layout.addWidget(self.zoom_in_btn)
        
        # 缩小按钮
        self.zoom_out_btn = QToolButton()
        self.zoom_out_btn.setText("-")
        self.zoom_out_btn.setToolTip("缩小 (Ctrl+-)")
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_image(0.8))
        zoom_layout.addWidget(self.zoom_out_btn)
        
        # 重置缩放按钮
        self.zoom_reset_btn = QToolButton()
        self.zoom_reset_btn.setText("↻")
        self.zoom_reset_btn.setToolTip("重置缩放 (Ctrl+0)")
        self.zoom_reset_btn.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(self.zoom_reset_btn)
        
        # 将按钮容器放置在视图右上角
        self.zoom_widget.setGeometry(-10, 10, 40, 120)
        self.zoom_widget.raise_()
    
    def zoom_image(self, factor):
        """缩放图像"""
        if not self.current_image:
            return
            
        self.zoom_factor *= factor
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))
        
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.scale(factor, factor)
    
    def reset_zoom(self):
        """重置缩放"""
        if not self.current_image:
            return
            
        self.graphics_view.resetTransform()
        self.zoom_factor = 1.0
        self.graphics_view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
    
    def resizeEvent(self, event):
        """窗口大小改变时调整缩放按钮位置"""
        super().resizeEvent(event)
        if hasattr(self, 'zoom_widget'):
            self.zoom_widget.setGeometry(0, 10, 40, 120)#self.graphics_view.width()-5
    
    def eventFilter(self, source, event):
        """处理图形视图的鼠标和键盘事件"""
        if source is self.graphics_view.viewport():
            # 鼠标滚轮缩放
            if event.type() == event.Wheel and not self.is_selecting:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.zoom_image(1.1)
                elif delta < 0:
                    self.zoom_image(0.9)
                return True
                
            # 鼠标事件处理
            if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                self.handle_mouse_press(event)
            elif event.type() == event.MouseMove and event.buttons() & Qt.LeftButton:
                self.handle_mouse_move(event)
            elif event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                self.handle_mouse_release(event)
        
        # 键盘快捷键
        if event.type() == event.KeyPress:
            if event.modifiers() & Qt.ControlModifier:
                if event.key() == Qt.Key_Equal or event.key() == Qt.Key_Plus:
                    self.zoom_image(1.2)
                    return True
                elif event.key() == Qt.Key_Minus:
                    self.zoom_image(0.8)
                    return True
                elif event.key() == Qt.Key_0:
                    self.reset_zoom()
                    return True
        
        return super().eventFilter(source, event)
    
    def start_area_selection(self):
        """开始选择区域"""
        if not self.current_image:
            QMessageBox.warning(self, "警告", "请先加载图像")
            return
        
        self.is_selecting = True
        self.crop_confirmed = False
        self.select_area_btn.setEnabled(False)
        self.confirm_crop_btn.setEnabled(False)
        self.cancel_crop_btn.setEnabled(True)
        self.status_label.setText("请拖动鼠标选择裁剪区域，可直接全图保存")
    
    def handle_mouse_press(self, event):
        """处理鼠标按下事件"""
        if self.is_selecting and not self.crop_confirmed:
            self.drag_start = self.graphics_view.mapToScene(event.pos())
            self.crop_rect = QRectF(self.drag_start, self.drag_start)
            self.update_crop_overlay()
    
    def handle_mouse_move(self, event):
        """处理鼠标移动事件"""
        if self.drag_start and self.is_selecting and not self.crop_confirmed:
            self.drag_end = self.graphics_view.mapToScene(event.pos())
            self.crop_rect = QRectF(self.drag_start, self.drag_end).normalized()
            self.update_crop_overlay()
    
    def handle_mouse_release(self, event):
        """处理鼠标释放事件"""
        if self.drag_start and self.is_selecting and not self.crop_confirmed:
            self.drag_end = self.graphics_view.mapToScene(event.pos())
            self.crop_rect = QRectF(self.drag_start, self.drag_end).normalized()
            
            # 检查选择区域是否有效
            if self.crop_rect.width() < 10 or self.crop_rect.height() < 10:
                QMessageBox.warning(self, "警告", "选择区域太小")
                # self.cancel_crop(
            else:
                self.confirm_crop_btn.setEnabled(True)
                self.status_label.setText("选择区域后，点击'执行裁剪'确认或重新选择")
    
    def update_crop_overlay(self):
        """更新裁剪选择框"""
        self.scene.clear()
        
        # 显示原始图像
        if self.current_image:
            # 修复1: 确保图像转换为RGBA模式
            if self.current_image.mode in ['1', 'L', 'P']:
                display_image = self.current_image.convert('RGBA')
            elif self.current_image.mode == 'RGB':
                display_image = self.current_image.convert('RGBA')
            else:
                display_image = self.current_image
            
            qimg = ImageQt.toqimage(display_image)
            pixmap = QPixmap.fromImage(qimg)
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.pixmap_item)
        
        # 显示选择框
        if self.crop_rect and self.is_selecting and not self.crop_confirmed:
            # 创建半透明红色边框的选择框
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            
            rect_item = self.scene.addRect(self.crop_rect, pen, QColor(255, 0, 0, 30))
            rect_item.setZValue(1)  # 确保选择框在图像上方
    
    def confirm_crop(self):
        """执行裁剪操作"""
        if not all([self.drag_start, self.drag_end, self.current_image]):
            return
        
        # 计算裁剪区域（转换为图像坐标）
        scene_rect = self.scene.itemsBoundingRect()
        img_width = self.current_image.width
        img_height = self.current_image.height
        
        # 计算比例
        scale_x = img_width / scene_rect.width()
        scale_y = img_height / scene_rect.height()
        
        # 转换为图像坐标
        left = int((self.crop_rect.left() - scene_rect.left()) * scale_x)
        top = int((self.crop_rect.top() - scene_rect.top()) * scale_y)
        right = int((self.crop_rect.right() - scene_rect.left()) * scale_x)
        bottom = int((self.crop_rect.bottom() - scene_rect.top()) * scale_y)
        
        # 确保在图像范围内
        left = max(0, min(left, img_width))
        right = max(0, min(right, img_width))
        top = max(0, min(top, img_height))
        bottom = max(0, min(bottom, img_height))
        
        if right <= left or bottom <= top:
            QMessageBox.warning(self, "警告", "无效的裁剪区域")
            return
        
        # 执行裁剪
        self.current_image = self.current_image.crop((left, top, right, bottom))
        
        # 获取当前DPI值
        try:
            dpi = int(self.dpi_entry.text())
        except:
            dpi = 300  # 默认值
        
        # 显示裁剪信息和DPI
        crop_info = f"已裁剪: {right-left}×{bottom-top} 像素 | DPI: {dpi}"
        self.status_label.setText(crop_info)
        
        # 更新显示
        self.show_image()
    
    def cancel_crop(self):
        """取消当前裁剪选择"""
        self.is_selecting = False
        self.crop_confirmed = False
        self.crop_rect = None
        self.drag_start = self.drag_end = None
        
        # 更新按钮状态
        self.select_area_btn.setEnabled(True)
        self.confirm_crop_btn.setEnabled(False)
        self.cancel_crop_btn.setEnabled(False)
        
        # 恢复显示原始图像
        if self.current_image:
            self.show_image()
            self.status_label.setText("滚轮调整缩放后点击'选择区域'")
    
    def load_image(self, is_pdf=False, is_eps=False):
        """加载图像文件"""
        if is_pdf:
            file_types = "PDF 文件 (*.pdf)"
        elif is_eps:
            file_types = "矢量文件 (*.eps *.svg)"  # 包含EPS和SVG
        else:
            file_types = "图像文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        
        path, _ = QFileDialog.getOpenFileName(self, "选择图像文件", "", file_types)
        
        if not path:
            return
        
        try:
            self.status_label.setText("正在加载...")
            QApplication.processEvents()
            
            if is_pdf:
                images = convert_from_path(path, dpi=600)
                page = int(self.page_entry.text())
                self.original_image = images[min(page, len(images)-1)]
            elif is_eps:
                # 对于SVG直接使用cairosvg
                if path.lower().endswith('.svg'):
                    temp_path = "temp_convert.png"
                    cairosvg.svg2png(url=path, write_to=temp_path)
                    self.original_image = Image.open(temp_path)
                    os.remove(temp_path)
                # 对于EPS使用Ghostscript转换
                elif path.lower().endswith('.eps'):
                    try:
                        self.original_image = Image.open(path)  # 尝试直接打开
                        self.original_image = self.original_image.convert("RGBA")
                    except Exception as e:
                        # 使用Pillow打开失败，调用Ghostscript
                        self.original_image = self.load_eps_file(path)
            else:
                self.original_image = Image.open(path)
            
            self.current_image = self.original_image.copy()
            self.image_path = path
            self.show_image()
            self.status_label.setText(f"已加载: {os.path.basename(path)}")
            
            # 重置裁剪状态
            # self.cancel_crop()
            self.start_area_selection()
            
        except Exception as e:
            self.status_label.setText("加载失败")
            QMessageBox.critical(self, "错误", f"无法加载图像:\n{str(e)}")
    
    def load_eps_file(self, path):
        """处理EPS文件加载（使用Ghostscript）"""
        # 创建临时文件路径
        temp_path = os.path.join(tempfile.gettempdir(), f"eps_convert_{os.getpid()}.png")
        
        # 检查Ghostscript是否可用
        try:
            subprocess.run(["gs", "--version"], check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            QMessageBox.critical(
                self,
                "Ghostscript未安装",
                "加载EPS文件需要Ghostscript。\n"
                "请访问 https://www.ghostscript.com/ 下载安装，并确保可执行文件在系统路径中。"
            )
            raise RuntimeError("Ghostscript not installed")
        
        # Ghostscript命令
        gs_command = [
            "gs",  # Ghostscript可执行文件
            "-dNOPAUSE", "-dBATCH",  # 无需暂停
            "-sDEVICE=pngalpha",  # 带透明度的PNG输出
            f"-sOutputFile={temp_path}",  # 输出文件
            "-r300",  # 300 DPI
            "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4",  # 抗锯齿设置
            "-q",  # 静默模式
            path  # 输入文件
        ]
        
        try:
            # 执行Ghostscript转换
            result = subprocess.run(gs_command, check=True, 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 加载转换后的图像
            img = Image.open(temp_path)
            
            # 删除临时文件
            try:
                os.remove(temp_path)
            except:
                pass
            
            return img
            
        except subprocess.CalledProcessError as e:
            # 删除临时文件
            try:
                os.remove(temp_path)
            except:
                pass
            
            error_msg = e.stderr.decode() if e.stderr else "Ghostscript转换失败"
            QMessageBox.critical(self, "EPS转换错误", f"无法转换EPS文件:\n{error_msg}")
            raise RuntimeError(f"Ghostscript error: {error_msg}")
    def calculate_target_pixels(self):
        """基于物理尺寸和DPI计算目标像素尺寸
        
        返回:
            tuple: (target_width_px, target_height_px) 或 None（计算失败时）
        """
        try:
            # 参数验证
            width_inch = float(self.width_entry.text())
            dpi = int(self.dpi_entry.text())
            
            if width_inch <= 0 or dpi <= 0:
                raise ValueError("数值必须为正数")
                
            # 计算目标宽度像素
            target_width_px = round(width_inch * dpi)
            
            # 保持宽高比计算高度
            if self.current_image:
                aspect_ratio = self.current_image.height / self.current_image.width
                target_height_px = round(target_width_px * aspect_ratio)
                return (target_width_px, target_height_px)
                
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", f"无效参数: {str(e)}")
            return None
    
    def show_image(self):
        """显示当前图像并更新状态信息
        
        功能说明：
        - 将当前图像转换为QPixmap并显示在图形场景中
        - 自动调整视图适应窗口大小
        - 在状态栏显示图像尺寸和DPI信息
        """
        if not self.current_image:
            self.status_label.setText("无有效图像")
            return
        
        try:
            # 修复2: 确保正确的图像模式转换
            if self.current_image.mode == '1':  # 1位像素，黑白
                display_image = self.current_image.convert('L')
            elif self.current_image.mode == 'P':  # 8位像素，使用调色板
                display_image = self.current_image.convert('RGBA')
            elif self.current_image.mode == 'L':  # 灰度
                display_image = self.current_image.convert('RGBA')
            elif self.current_image.mode == 'RGB':  # RGB
                display_image = self.current_image.convert('RGBA')
            else:
                display_image = self.current_image  # 已经是RGBA或其他支持模式
            
            # 转换为QImage
            qimg = ImageQt.toqimage(display_image)
            pixmap = QPixmap.fromImage(qimg)
            
            # 场景更新
            self.scene.clear()
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.pixmap_item)
            
            # 视图调整
            self.graphics_view.fitInView(
                self.scene.itemsBoundingRect(), 
                Qt.KeepAspectRatio
            )
            
            # 获取DPI设置（带错误处理）
            try:
                dpi = int(self.dpi_entry.text())
            except ValueError:
                dpi = 300  # 默认DPI值
                self.dpi_entry.setText(str(dpi))
            
            # 计算物理尺寸（英寸）
            width_inch = self.current_image.width / dpi
            height_inch = self.current_image.height / dpi
            
            # 更新状态信息（多行显示）
            status_info = f"""
            像素尺寸: {self.current_image.width}×{self.current_image.height} 像素;物理尺寸: {width_inch:.2f}×{height_inch:.2f} 英寸 (DPI: {dpi})
            """
            self.status_label.setText(status_info.strip())
            
        except Exception as e:
            self.status_label.setText(f"图像显示错误: {str(e)}")
            QMessageBox.warning(self, "错误", f"无法显示图像:\n{str(e)}")
    
    def reset_image(self):
        """重置为原始图像"""
        if self.original_image:
            self.current_image = self.original_image.copy()
            self.show_image()
            self.cancel_crop()  # 同时取消任何进行中的裁剪操作
            self.status_label.setText("已重置为原始图像")

    def save_image(self, format):
        """智能保存图像（自动处理DPI和尺寸转换）
        
        参数:
            format (str): 文件格式(png/jpg/pdf等)
            
        流程:
            1. 验证输入参数
            2. 计算目标分辨率
            3. 执行格式转换
            4. 处理元数据
        """
        # 1. 前置检查
        if not self.current_image:
            QMessageBox.warning(self, "警告", "没有可保存的图像")
            return

        # 2. 获取保存路径（自动补全扩展名）
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"保存为{format.upper()}",
            "",
            f"{format.upper()}文件 (*.{format})"
        )
        if not path:
            return
            
        if not path.lower().endswith(f".{format}"):
            path += f".{format}"

        try:
            # 3. 计算目标尺寸
            target_size = self.calculate_target_pixels()
            if not target_size:
                return
                
            target_width, target_height = target_size
            
            # 4. 格式特殊处理
            if format.lower() in ("pdf", "eps"):
                self._save_vector_format(path, format, target_size)
            else:
                self._save_raster_format(path, format, target_size)
                
            # 5. 状态更新
            self._update_after_save(path)
            
        except Exception as e:
            self.status_label.setText("保存失败")
            QMessageBox.critical(self, "错误", f"保存过程中出错:\n{str(e)}")
    
    def _save_vector_format(self, path, format, target_size):
        """处理PDF/EPS等矢量格式保存"""
        temp_path = "temp_vector.png"
        try:
            # 先保存为临时PNG
            resized_img = self.current_image.resize(
                target_size, 
                Image.LANCZOS
            )
            resized_img.save(temp_path, "PNG", dpi=(self.get_dpi(), self.get_dpi()))
            
            # 转换为目标格式
            img = Image.open(temp_path)
            if format.lower() == "pdf":
                img.save(path, "PDF", resolution=self.get_dpi())
            else:  # EPS
                img.save(path, "EPS", dpi=(self.get_dpi(), self.get_dpi()))
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _save_raster_format(self, path, format, target_size):
        """处理PNG/JPG等位图格式保存，特别优化JPG格式"""
        # 调整尺寸
        resized_img = self.current_image.resize(
            target_size,
            Image.LANCZOS  # 高质量重采样
        )
        
        # 为JPG格式提供专门的解决方案
        if format.lower() in ("jpg", "jpeg"):
            # 确保图像为RGB模式（JPG不支持透明通道）
            if resized_img.mode != 'RGB':
                # 如果原始图像是RGBA或有透明通道，创建白色背景
                if resized_img.mode in ['RGBA', 'LA', 'P', 'PA']:
                    # 创建白色背景图像
                    background = Image.new('RGB', resized_img.size, (255, 255, 255))
                    # 如果原始图像有alpha通道，使用它作为掩码
                    if 'A' in resized_img.mode:
                        mask = resized_img.split()[-1]  # 获取alpha通道
                        background.paste(resized_img.convert('RGB'), mask=mask)
                    else:
                        background.paste(resized_img.convert('RGB'))
                    resized_img = background
                # 对于其他模式，直接转换为RGB
                else:
                    resized_img = resized_img.convert('RGB')
            
            # 为JPG创建特定的保存参数
            save_args = {
                "quality": 95,  # 高质量压缩
                "dpi": (self.get_dpi(), self.get_dpi()),  # 设置DPI
                "subsampling": "4:4:4",  # 保持完整的色度信息
                "optimize": True  # 优化压缩
            }
            
            # 使用JPEG格式（PIL要求）
            save_format = "JPEG"
            
        else:  # PNG或其他格式
            # 对于PNG，保持原有的透明度
            save_args = {
                "dpi": (self.get_dpi(), self.get_dpi()) if format.lower() != "png" else (self.get_dpi(), self.get_dpi())
            }
            
            # 保持原有的模式
            if resized_img.mode == 'P' or resized_img.mode == 'PA':
                # 处理调色板图像
                resized_img = resized_img.convert('RGBA')
            
            # 使用原来的格式名
            save_format = format.upper()
            
            # 对PNG应用压缩优化
            if format.lower() == "png":
                save_args["compress_level"] = 6  # 中等压缩（0-9，0是无压缩）
                save_args["optimize"] = True
        
        try:
            # 执行保存
            resized_img.save(path, save_format, **save_args)
            return True
        except KeyError as e:
            # 某些格式不支持所有参数，尝试移除可能不支持的参数
            save_args.pop("dpi", None)
            try:
                resized_img.save(path, save_format, **save_args)
                return True
            except:
                pass
        except Exception as e:
            pass
        
        # 如果上面的方法失败，尝试最简单的保存方式
        try:
            if format.lower() in ("jpg", "jpeg"):
                resized_img.save(path, "JPEG")
            else:
                resized_img.save(path)
            return True
        except Exception as e:
            QMessageBox.critical(self, "保存错误", f"无法保存{format.upper()}文件:\n{str(e)}")
            self.status_label.setText(f"{format.upper()}保存失败")
            return False
    
    def get_dpi(self):
        """安全获取DPI值"""
        try:
            return max(72, min(int(self.dpi_entry.text()), 1200))
        except:
            return 300  # 默认值

    def _update_after_save(self, path):
        """保存后状态更新"""
        # 显示保存信息
        size_info = (
            f"实际保存尺寸: {self.current_image.width}×{self.current_image.height}px\n"
            f"目标物理尺寸: {float(self.width_entry.text()):.2f}英寸 @ {self.get_dpi()}DPI"
        )
        
        self.status_label.setText(size_info)
        QMessageBox.information(
            self, 
            "保存成功",
            f"图像已保存为:\n{path}\n\n{size_info}"
        )
        
        # 重置选择模式 (调用正确的方法)
        self.cancel_crop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageRescaleApp()
    window.show()
    sys.exit(app.exec_())