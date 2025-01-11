import tkinter as tk
from tkinter import  filedialog, messagebox
from PIL import Image, ImageTk
import cairosvg
# import pyautogui
from pdf2image import convert_from_path

class CropImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ImageRescale")
        
        # 固定窗口大小
        self.root.geometry("1080x900")  # 宽900，高700像素
        self.root.resizable(True, True)  # 允许调整窗口大小
        
        # 初始化变量
        self.image = None
        self.image_path = None
        self.original_image = None  # 保存原始图像
        self.canvas = None
        self.rect = None  # 用于裁剪的矩形框
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.max_width = 800  # 图像显示最大宽度
        self.max_height = 480  # 图像显示最大高度
        # self.dpi = 150  # 默认DPI设置为150
        self.scale_factor = 1  # 缩放比例

        # 添加按钮和画布
        self.create_widgets()

    def create_widgets(self):
        """创建 UI 元素"""

        # 创建图标和说明框架
        header_frame = tk.Frame(self.root)
        header_frame.pack(pady=10, anchor="w")  # 让它靠左显示

        # 加载图标
        icon_image = Image.open("icon.jpeg")
        icon_image = icon_image.resize((150, 150))  # 修改为你希望的大小，例如 32x32
        icon_image = ImageTk.PhotoImage(icon_image)

        # 设置窗口图标
        root.iconphoto(True, icon_image)

        # 创建图标
        icon_label = tk.Label(header_frame, image=icon_image)
        icon_label.image = icon_image  # 保持引用，防止图标被垃圾回收
        icon_label.pack(side="left", padx=5)

        # 创建说明文字
        text_notation = "" \
                        "1、请先在宽度标签后面输入最终显示的尺寸（例如：单栏3.5in）；\n" \
                        "2、点击对应格式的加载按钮，选择图片；\n" \
                        "3、如果需要裁剪，请先点击裁剪按钮，之后在图中选择裁剪区域；\n" \
                        "4、输入需要保存的dpi；\n" \
                        "5、点击想要保存的格式，点击对应保存格式按钮\n\n" \
                        "注意事项:" \
                        "- 预览时会降低分辨率，裁剪后的图片显示原始分辨率的左上方.load_pdf函数可增加pdf读取分辨率。"
        instructions_label = tk.Label(header_frame, text= text_notation, font=("Arial", 12), justify="left", anchor="w")
        instructions_label.pack(side="left", padx=10)

        # 创建按钮框架来横向排列按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        # 创建加载按钮
        self.load_png_button = tk.Button(button_frame, text="加载 PNG", command=self.load_png_image, width=8, height=1)
        self.load_png_button.grid(row=0, column=0, padx=3, pady=5)

        self.load_jpg_button = tk.Button(button_frame, text="加载 JPG", command=self.load_jpg_image, width=8, height=1)
        self.load_jpg_button.grid(row=0, column=1, padx=3, pady=5)

        self.load_pdf_button = tk.Button(button_frame, text="加载 PDF", command=self.load_pdf_image, width=8, height=1)
        self.load_pdf_button.grid(row=0, column=2, padx=3, pady=5)

        self.load_eps_button = tk.Button(button_frame, text="加载 EPS", command=self.load_eps_image, width=8, height=1)
        self.load_eps_button.grid(row=0, column=3, padx=3, pady=5)

        self.load_svg_button = tk.Button(button_frame, text="加载 SVG", command=self.load_svg_image, width=8, height=1)
        self.load_svg_button.grid(row=0, column=4, padx=3, pady=5)

        # 创建保存按钮
        self.save_png_button = tk.Button(button_frame, text="保存为 PNG", command=lambda: self.save_image("png"), width=8, height=1)
        self.save_png_button.grid(row=1, column=0, padx=5, pady=5)

        self.save_jpg_button = tk.Button(button_frame, text="保存为 JPG", command=lambda: self.save_image("jpg"), width=8, height=1)
        self.save_jpg_button.grid(row=1, column=1, padx=5, pady=5)

        self.save_pdf_button = tk.Button(button_frame, text="保存为 PDF", command=lambda: self.save_image("pdf"), width=8, height=1)
        self.save_pdf_button.grid(row=1, column=2, padx=5, pady=5)

        self.save_eps_button = tk.Button(button_frame, text="保存为 EPS", command=lambda: self.save_image("eps"), width=8, height=1)
        self.save_eps_button.grid(row=1, column=3, padx=5, pady=5)

        self.save_svg_button = tk.Button(button_frame, text="保存为 SVG", command=lambda: self.save_image("svg"), width=8, height=1)
        self.save_svg_button.grid(row=1, column=4, padx=5, pady=5)

        # 创建裁剪按钮
        self.crop_button = tk.Button(button_frame, text="裁剪图像", command=self.start_crop, width=8, height=1)
        self.crop_button.grid(row=2, column=0, padx=5, pady=5)

        # 创建桌面截图按钮
        # self.screenshot_button = tk.Button(button_frame, text="截取桌面截图", command=self.take_screenshot, width=8, height=1)
        # self.screenshot_button.grid(row=2, column=1, padx=5, pady=5)

        # 创建输入框来获取尺寸和DPI

        # 创建宽度输入框
        self.width_label = tk.Label(button_frame, text="宽度 (英寸):")
        self.width_label.grid(row=3, column=0, padx=5)
        self.width_entry = tk.Entry(button_frame, width=10)
        self.width_entry.grid(row=3, column=1, padx=5)
        self.width_entry.insert(0, "3.5")  # 默认值

        # # 创建高度输入框
        # self.height_label = tk.Label(button_frame, text="高度 (英寸):")
        # self.height_label.grid(row=4, column=0, padx=5)
        # self.height_entry = tk.Entry(button_frame, width=10)
        # self.height_entry.grid(row=4, column=1, padx=5)
        # self.height_entry.insert(0, "3.5")  # 默认值

        # 创建 DPI 输入框
        self.dpi_label = tk.Label(button_frame, text="DPI:")
        self.dpi_label.grid(row=3, column=2, padx=5)
        self.dpi_entry = tk.Entry(button_frame, width=10)
        self.dpi_entry.grid(row=3, column=3, padx=5)
        self.dpi_entry.insert(0, "400")  # 默认值

        self.dpi_show_label = tk.Label(button_frame, text="DPI: 未知", font=("Arial", 10))
        self.dpi_show_label.grid(row=3, column=4, padx=5)
        # self.dpi_show_label.pack(pady=10)

    def no_op(self):
        """空操作，暂时不实现裁剪功能"""
        messagebox.showinfo("裁剪", "裁剪功能暂未实现！")
    
    def start_crop(self):
        """开始裁剪图像"""
        if not self.original_image:
            messagebox.showerror("错误", "没有加载图像！")
            return

        # 创建裁剪矩形框
        self.rect = None
        self.start_x = self.start_y = None
        self.end_x = self.end_y = None  # 确保这两个变量初始化为空
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        """鼠标按下时记录起始点"""
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_drag(self, event):
        """拖动时更新矩形框的大小"""
        self.end_x = event.x
        self.end_y = event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.end_x, self.end_y)

    def on_release(self, event):
        """鼠标释放时进行裁剪"""
        self.end_x = event.x
        self.end_y = event.y
        self.canvas.delete(self.rect)

        # 如果没有设置裁剪区域，默认使用整个图像的大小
        if self.start_x is None or self.start_y is None or self.end_x is None or self.end_y is None:
            # 使用整个图像的尺寸
            left = 0
            top = 0
            right = self.original_image.width
            bottom = self.original_image.height
        else:
            # 计算缩放后的坐标
            left = min(self.start_x, self.end_x) / self.scale_factor
            top = min(self.start_y, self.end_y) / self.scale_factor
            right = max(self.start_x, self.end_x) / self.scale_factor
            bottom = max(self.start_y, self.end_y) / self.scale_factor

        # 在原图上进行裁剪
        cropped_image = self.original_image.crop((left, top, right, bottom))

        # 显示裁剪后的图像
        self.image = cropped_image  # 这里保留了原始分辨率
        self.tk_image = ImageTk.PhotoImage(self.image)

        # 更新画布
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")

    def load_png_image(self):
        """加载 PNG 图像"""
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.load_image(file_path)

    def load_jpg_image(self):
        """加载 JPG 图像"""
        file_path = filedialog.askopenfilename(filetypes=[("JPG files", "*.jpg;*.jpeg")])
        if file_path:
            self.load_image(file_path)

    def load_pdf_image(self):
        """加载 PDF 图像"""
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.load_image(file_path, is_pdf=True)

    def load_eps_image(self):
        """加载 EPS 图像"""
        file_path = filedialog.askopenfilename(filetypes=[("EPS files", "*.eps")])
        if file_path:
            self.load_image(file_path, is_eps=True)

    def load_svg_image(self):
        """加载 SVG 图像"""
        file_path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg")])
        if file_path:
            self.load_svg(file_path)

    def load_image(self, file_path, is_pdf=False, is_eps=False):
        """根据文件类型加载图像"""
        try:
            self.image_path = file_path
            if is_pdf:
                self.original_image = self.load_pdf(file_path)
            elif is_eps:
                self.original_image = self.load_eps(file_path)
            else:
                self.original_image = Image.open(file_path)
        # 获取并显示图片的 DPI
            width, height = self.original_image.size

            # 获取用户输入的打印宽度（英寸）
            try:
                print_width_inch = float(self.width_entry.get())  # 获取输入的宽度值
                print_height_inch = (height / width) * print_width_inch # 获取输入的宽度值
            except ValueError:
                messagebox.showerror("错误", "请输入有效的打印宽度！")
                return

            # 计算 DPI：DPI = 像素 / 英寸
            dpiw = width / print_width_inch
            dpih = height / print_height_inch
            self.dpi = dpiw
            self.dpih = dpih


            # 更新 DPI 显示标签
            self.dpi_show_label.config(text=f"Now DPI: {int(self.dpi)}", font=("Arial", 10),fg="red")  # 将 DPI 显示为整数  ,int(self.dpih)

            print(f"图像原始尺寸: {self.original_image.size}")  # 打印原图尺寸
        except Exception as e:
            messagebox.showerror("错误", f"加载图像失败: {e}")
            return

        # 等比例缩放图像以适应显示
        self.image = self.resize_image(self.original_image)

        print(f"图像缩放后的尺寸: {self.image.size}")  # 打印缩放后的尺寸

        # 将图像转换为适合 Tkinter 显示的格式
        self.tk_image = ImageTk.PhotoImage(self.image)

        # 创建画布来显示图像
        if self.canvas:
            self.canvas.destroy()
        self.canvas = tk.Canvas(self.root, width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.pack(pady=10)

        # 在画布上显示图像
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")

        # 计算缩放比例
        self.scale_factor = self.image.width / self.original_image.width

    def load_pdf(self, file_path):
        """处理 PDF 格式图像"""
        images = convert_from_path(file_path, dpi=600)  # 可以根据需要调整DPI
        images = convert_from_path(file_path)  # 可以根据需要调整DPI
        return images[0]  # 只获取第一页，或者根据需求处理多页

    def load_eps(self, file_path):
        """处理 EPS 格式图像"""
        return Image.open(file_path)

    def load_svg(self, file_path):
        """处理 SVG 格式图像"""
        cairosvg.svg2png(url=file_path, write_to="temp.png")
        return Image.open("temp.png")

    def resize_image(self, image):
        """按比例缩放图像以适应最大显示区域"""
        max_width = self.max_width
        max_height = self.max_height
        width, height = image.size

        if width > max_width or height > max_height:
            # 根据最大宽度和高度进行等比例缩放
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)  # 使用LANCZOS代替ANTIALIAS
        return image

    def save_image(self, file_format):
        """保存图像为不同格式"""
        if self.image:
            file_path = filedialog.asksaveasfilename(defaultextension=f".{file_format}",
                                                     filetypes=[(f"{file_format.upper()} files", f"*.{file_format}")])
            if file_path:
                try:
                    dpi_value = float(self.dpi_entry.get())  # 获取输入框中的DPI值
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的 DPI 值！")
                    return
            width_inch = float(self.width_entry.get())  
            dpi_value = float(self.dpi_entry.get())  
            width_px = int(width_inch * dpi_value)
            height_px = int( ( self.image.height/self.image.width)*width_px )

            # 调整图像大小（如果需要的话）
            self.image = self.image.resize((width_px, height_px), Image.Resampling.LANCZOS)
            # 将 DPI 转换为元组 (dpi, dpi)
            self.image.save(file_path, format=file_format.upper())
            messagebox.showinfo("保存成功", f"图像已保存为 {file_format.upper()} 格式")
        else:
            messagebox.showerror("错误", "没有加载图像！")

    # def take_screenshot(self):
    #     """截取桌面截图"""
    #     screenshot = pyautogui.screenshot()
    #     screenshot.save("screenshot.png")
    #     messagebox.showinfo("截图", "桌面截图已保存为 screenshot.png")

if __name__ == "__main__":
    root = tk.Tk()
    app = CropImageApp(root)
    root.mainloop()
