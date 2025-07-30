from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit, QToolBar,
    QFileDialog, QInputDialog, QTextBrowser, QDialog, QLabel,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QSpacerItem, QSlider, QScrollArea)
from PySide6.QtGui import (
    QAction, QFont, QTextCursor, QTextCharFormat, QTextListFormat,
    QDesktopServices, QMouseEvent, QIntValidator, QColor, QPixmap, QKeySequence, QShortcut)
from PySide6.QtCore import Qt, QUrl, QSize
import sys
from PIL import Image, ImageQt
import os

if len(sys.argv) > 1:
    AUTOSAVE_PATH = sys.argv[1]
else:
    AUTOSAVE_PATH = "content.html" # Varsayılan yol

# --- Görsel Kırpma Dialog'u ---
class ImageCropDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Görseli Kırp ve Boyutlandır")
        self.setModal(True)
        self.resize(600, 500)
        
        self.image_path = image_path
        self.cropped_image = None
        self.alignment = "left"  # Varsayılan olarak sol seçili olsun
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Görsel önizleme
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #444; background-color: #1e1e1e;")
        self.image_label.setMinimumHeight(300)
        
        # Orijinal görseli yükle ve göster
        self.original_image = Image.open(image_path)
        self.current_image = self.original_image.copy()
        self.update_preview()
        
        layout.addWidget(self.image_label)
        
        # Boyut kontrolü
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Genişlik:"))
        
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setMinimum(50)
        self.width_slider.setMaximum(800)
        self.width_slider.setValue(300)
        self.width_slider.valueChanged.connect(self.resize_image)
        
        self.width_label = QLabel("300px")
        
        size_layout.addWidget(self.width_slider)
        size_layout.addWidget(self.width_label)
        layout.addLayout(size_layout)
        
        # Hizalama butonları (SADECE SOL VE SAĞ)
        align_layout = QHBoxLayout()
        align_layout.addWidget(QLabel("Hizalama:"))
        
        self.left_btn = QPushButton("Sol")
        self.right_btn = QPushButton("Sağ")
        
        self.left_btn.clicked.connect(lambda: self.set_alignment("left"))
        self.right_btn.clicked.connect(lambda: self.set_alignment("right"))
        
        # Varsayılan olarak sol seçili
        self.left_btn.setStyleSheet("background-color: #005bb5;") # Vurgulama
        
        align_layout.addWidget(self.left_btn)
        align_layout.addWidget(self.right_btn)
        align_layout.addStretch()
        layout.addLayout(align_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Tamam")
        cancel_btn = QPushButton("İptal")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        # DÜZELTİLMİŞ KISIM: Tam stil kodunu buraya ekleyin
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #0076d6;
                color: #e0e0e0;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QLabel {
                color: #e0e0e0;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 6px;
                background: #1e1e1e;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0076d6;
                border: 1px solid #005bb5;
                width: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
        """)
    # set_alignment fonksiyonunu da basitleştirelim
    def set_alignment(self, alignment):
        self.alignment = alignment
        if alignment == "left":
            self.left_btn.setStyleSheet("background-color: #3a3a3a;") # Vurgulu
            self.right_btn.setStyleSheet("background-color: #3a3a3a;") # Normal
        elif alignment == "right":
            self.right_btn.setStyleSheet("background-color: #3a3a3a;") # Vurgulu
            self.left_btn.setStyleSheet("background-color: #3a3a3a;") # Normal

    # ... (ImageCropDialog sınıfının geri kalanı aynı kalabilir)
    def resize_image(self):
        width = self.width_slider.value()
        self.width_label.setText(f"{width}px")
        
        # Oranı koru
        aspect_ratio = self.original_image.height / self.original_image.width
        height = int(width * aspect_ratio)
        
        self.current_image = self.original_image.resize((width, height), Image.Resampling.LANCZOS)
        self.update_preview()
    
    def update_preview(self):
        # PIL'den QPixmap'e dönüştür
        qt_image = ImageQt.ImageQt(self.current_image)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Önizleme boyutuna sığdır
        scaled_pixmap = pixmap.scaled(400, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
    
    def get_result(self):
        return self.current_image, self.alignment

# --- Clickable Links ve Checkboxlar için Özel QTextEdit Sınıfı ---
class ClickableTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        
        # Arapça desteği için ayarlar
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)  # Varsayılan soldan sağa
        
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border-radius: 3px;
                padding: 15px;
                font-family: "Arial", "Tahoma", "Traditional Arabic", "Al Bayan";
            }
        """)

    def mouseReleaseEvent(self, event: QMouseEvent):
        anchor_url = self.anchorAt(event.pos())
        if anchor_url:
            QDesktopServices.openUrl(QUrl(anchor_url))
            event.accept()
            return

        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        selected_text = cursor.selectedText()

        UNCHECKED_BOX = "☐"
        CHECKED_BOX = "☑"

        if selected_text.startswith(UNCHECKED_BOX):
            cursor.insertText(CHECKED_BOX + selected_text[len(UNCHECKED_BOX):])
            event.accept()
        elif selected_text.startswith(CHECKED_BOX):
            cursor.insertText(UNCHECKED_BOX + selected_text[len(CHECKED_BOX):])
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        anchor_url = self.anchorAt(event.pos())

        cursor = self.cursorForPosition(event.pos())
        current_char = ""
        if not cursor.isNull():
            block = cursor.block()
            text_in_block = block.text()
            char_index_in_block = cursor.positionInBlock()

            if char_index_in_block >= 0 and char_index_in_block < len(text_in_block):
                current_char = text_in_block[char_index_in_block]

        if anchor_url or current_char in ["☐", "☑"]:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor)

        super().mouseMoveEvent(event)

class RichEditor(QMainWindow):
    def closeEvent(self, event):
        with open(AUTOSAVE_PATH, 'w', encoding='utf-8') as file:
            file.write(self.editor.toHtml())
        event.accept()
        
    def load_autosave(self):
        try:
            with open(AUTOSAVE_PATH, 'r', encoding='utf-8') as file:
                html = file.read()
                self.editor.setHtml(html)
        except FileNotFoundError:
            pass

    def set_default_font(self, p):
        font = QFont("Arial", p)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.editor.setFont(font)
        self.font_point_size = p

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notepad")
        self.resize(900, 600)
        self.showMaximized()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #3a3a3a;
                border-radius: 3px;
            }
        """)

        self.editor = ClickableTextEdit()
        self.load_autosave()
        self.editor.setFocus()
        self.editor.setAcceptRichText(True)
        self.editor.viewport().setMouseTracking(True)
        self.editor.setCursorWidth(1.5)
        self.editor.cursorPositionChanged.connect(self.update_font_size_entry_from_cursor)
        
        self.font_point_size = 12
        self.apply_font_size()
        self.set_default_font(12)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(10, 10, 10, 0)

        self.setCentralWidget(central_widget)

        self.create_custom_toolbar(main_layout)

        # Ana editör düzeni - sol ve sağ görseller için boşluklar
        text_editor_layout = QHBoxLayout()
        
        # Sol görsel alanı
        self.left_image_area = QScrollArea()
        self.left_image_widget = QWidget()
        self.left_image_widget.setStyleSheet("""
            QWidget {
                background-color: #3a3a3a;
                border-radius: 3px;
            }""")
        self.left_image_layout = QVBoxLayout(self.left_image_widget)
        self.left_image_layout.addStretch()
        self.left_image_area.setWidget(self.left_image_widget)
        self.left_image_area.setWidgetResizable(True)
        self.left_image_area.setFixedWidth(320)
        self.left_image_area.setStyleSheet("""
            QScrollArea {
                background-color: #3a3a3a;
                border-radius: 3px;
            }
        """)
        
        # Sağ görsel alanı
        self.right_image_area = QScrollArea()
        self.right_image_widget = QWidget()
        self.right_image_widget.setStyleSheet("""
            QWidget {
                background-color: #3a3a3a;
                border-radius: 3px;
            }""")
        self.right_image_layout = QVBoxLayout(self.right_image_widget)
        self.right_image_layout.addStretch()
        self.right_image_area.setWidget(self.right_image_widget)
        self.right_image_area.setWidgetResizable(True)
        self.right_image_area.setFixedWidth(320)
        self.right_image_area.setStyleSheet("""
            QScrollArea {
                background-color: #3a3a3a;
                border-radius: 3px;
            }
        """)
        
        text_editor_layout.addWidget(self.left_image_area)
        text_editor_layout.addWidget(self.editor, 2)
        text_editor_layout.addWidget(self.right_image_area)
        
        main_layout.addLayout(text_editor_layout)
        
        # Kısayolları ayarla
        self.setup_shortcuts()
        self.editor.setFocus()
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.editor.setTextCursor(cursor)

    def create_custom_toolbar(self, parent_layout: QVBoxLayout):
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(5)

        button_widget.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #0076d6;
                color: #e0e0e0;
                border: none;
                border-radius: 3px;
                padding: 3px;
                font-size: 12pt;
                min-width: 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 2px;
                font-size: 12pt;
                width: 40px;
            }
        """)

        buttons_data = [
            ("B", self.make_bold, "Ctrl+B"),
            ("I", self.make_italic, "Ctrl+I"),
            ("1.", self.insert_numbered_list, "Ctrl+Shift+1"),
            ("•", self.insert_bullet_list, "Ctrl+Shift+8"),
            ("☐", self.insert_todo_checkbox, "Ctrl+Shift+T"),
            ("🔗", self.insert_link, "Ctrl+K"),
            ("🖼️", self.insert_image, "Ctrl+Shift+I"),
            ("⇄", self.toggle_text_direction, "Ctrl+Shift+D"),
            ("⟵", self.align_right, "Ctrl+R"),
            ("↔", self.align_center, "Ctrl+E"),
            ("⟶", self.align_left, "Ctrl+L"),
        ]

        button_group_widget = QWidget()
        group_layout = QHBoxLayout(button_group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)

        for text, func, shortcut in buttons_data:
            button = QPushButton(text, self)
            button.clicked.connect(func)
            button.setFixedSize(QSize(30, 30))
            button.setToolTip(f"{shortcut}")  # Tooltip olarak kısayolu göster
            group_layout.addWidget(button)

        # Font size kontrolü
        self.font_size_entry = QLineEdit(str(self.font_point_size))
        self.font_size_entry.setFixedSize(QSize(40, 33))
        self.font_size_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.font_size_entry.setValidator(QIntValidator(1, 100, self))
        self.font_size_entry.returnPressed.connect(self.apply_font_size_from_entry)

        plus_button = QPushButton("+", self)
        plus_button.setFixedSize(QSize(30, 30))
        plus_button.clicked.connect(self.increase_font)
        plus_button.setToolTip("Ctrl+=")

        minus_button = QPushButton("-", self)
        minus_button.setFixedSize(QSize(30, 30))
        minus_button.clicked.connect(self.decrease_font)
        minus_button.setToolTip("Ctrl+-")

        group_layout.addWidget(minus_button)
        group_layout.addWidget(self.font_size_entry)
        group_layout.addWidget(plus_button)

        button_layout.addWidget(button_group_widget)
        button_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        toolbar_container = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(0)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(button_widget)
        toolbar_layout.addStretch()

        parent_layout.addWidget(toolbar_container)

    def setup_shortcuts(self):
        """Tüm butonlar için klavye kısayollarını ayarla"""
        shortcuts = [
            ("Ctrl+B", self.make_bold),
            ("Ctrl+I", self.make_italic),
            ("Ctrl+Shift+1", self.insert_numbered_list),
            ("Ctrl+Shift+8", self.insert_bullet_list),
            ("Ctrl+Shift+T", self.insert_todo_checkbox),
            ("Ctrl+K", self.insert_link),
            ("Ctrl+Shift+I", self.insert_image),
            ("Ctrl+Shift+D", self.toggle_text_direction),
            ("Ctrl+R", self.align_right),
            ("Ctrl+E", self.align_center),
            ("Ctrl+L", self.align_left),
            ("Ctrl+=", self.increase_font),
            ("Ctrl+-", self.decrease_font),
            ("Ctrl+S", self.manual_save),
            ("Ctrl+O", self.open_file),
            ("Ctrl+N", self.new_file),
        ]
        
        for key_seq, func in shortcuts:
            shortcut = QShortcut(QKeySequence(key_seq), self)
            shortcut.activated.connect(func)

    # Yeni hizalama fonksiyonları
    def align_left(self):
        cursor = self.editor.textCursor()
        fmt = cursor.blockFormat()
        fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(fmt)
        self.editor.setFocus()

    def align_center(self):
        cursor = self.editor.textCursor()
        fmt = cursor.blockFormat()
        fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cursor.setBlockFormat(fmt)
        self.editor.setFocus()

    def align_right(self):
        cursor = self.editor.textCursor()
        fmt = cursor.blockFormat()
        fmt.setAlignment(Qt.AlignmentFlag.AlignRight)
        cursor.setBlockFormat(fmt)
        self.editor.setFocus()

    def toggle_text_direction(self):
        """Metin yönünü değiştirir (soldan sağa / sağdan sola)"""
        cursor = self.editor.textCursor()
        fmt = cursor.blockFormat()
        
        # Mevcut yön
        current_dir = fmt.layoutDirection()
        
        if current_dir == Qt.LayoutDirection.RightToLeft:
            # Sağdan sola ise, soldan sağa yap
            fmt.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        else:
            # Soldan sağa ise, sağdan sola yap
            fmt.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        cursor.setBlockFormat(fmt)
        self.editor.setFocus()

    def update_font_size_entry_from_cursor(self):
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()
        point_size = fmt.fontPointSize()
        
        if point_size > 0:
            self.font_point_size = int(point_size)
            self.font_size_entry.setText(str(self.font_point_size))

    def make_bold(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        current_weight = cursor.charFormat().fontWeight()
        new_weight = QFont.Weight.Bold if current_weight != QFont.Weight.Bold else QFont.Weight.Normal
        fmt.setFontWeight(new_weight)
        fmt.setFontPointSize(self.font_point_size)
        cursor.mergeCharFormat(fmt)
        self.editor.setFocus()

    def make_italic(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        current_italic = cursor.charFormat().fontItalic()
        fmt.setFontItalic(not current_italic)
        fmt.setFontPointSize(self.font_point_size)
        cursor.mergeCharFormat(fmt)
        self.editor.setFocus()

    def insert_link(self):
        cursor = self.editor.textCursor()
        url, ok = QInputDialog.getText(self, "Link Ekle", "URL gir:")
        if ok and url:
            selected_text = cursor.selectedText() or url
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://") or url.startswith("mailto:")):
                url = "http://" + url

            fmt = QTextCharFormat()
            fmt.setAnchor(True)
            fmt.setAnchorHref(url)
            fmt.setForeground(QColor("#0076d6"))
            fmt.setFontUnderline(False)
            fmt.setFontPointSize(self.font_point_size)

            if cursor.hasSelection():
                cursor.mergeCharFormat(fmt)
            else:
                cursor.insertText(selected_text, fmt)

            cursor.clearSelection()
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor)
            self.editor.setTextCursor(cursor)

            self.font_point_size += 1
            self.apply_font_size()
            self.font_point_size -= 1
            self.apply_font_size()

            normal_fmt = QTextCharFormat()
            normal_fmt.setAnchor(False)
            normal_fmt.setFontPointSize(self.font_point_size)
            self.editor.setCurrentCharFormat(normal_fmt)

            self.editor.setFocus()

    def insert_numbered_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.ListDecimal)
        cursor.createList(fmt)
        self.apply_font_size_to_list(cursor)

    def insert_bullet_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.ListDisc)
        cursor.createList(fmt)
        self.apply_font_size_to_list(cursor)

    def apply_font_size_to_list(self, cursor):
        block = cursor.block()
        while block.isValid():
            fmt = QTextCharFormat()
            fmt.setFontPointSize(self.font_point_size)
            cursor.mergeCharFormat(fmt)
            block = block.next()

    def insert_todo_checkbox(self):
        cursor = self.editor.textCursor()

        if cursor.hasSelection():
            start = cursor.selectionStart()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.insertText("☐ ")
        else:
            cursor.insertBlock()
            cursor.insertText("☐ ")

        self.apply_font_size()
        self.editor.setTextCursor(cursor)
    # BU FONKSİYONU GÜNCELLEYİN: Dosya yolu yerine doğrudan PIL görsel nesnesi alsın
    def add_image_to_side(self, pil_image, side="left"):
        """PIL görselini sol veya sağ alana ekle"""
        try:
            # Yan alanlara sığacak şekilde boyutlandır
            pil_image.thumbnail((280, 400), Image.Resampling.LANCZOS)
            
            # PIL'den QPixmap'e dönüştür
            qt_image = ImageQt.ImageQt(pil_image)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Görsel label'ı oluştur
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    margin: 5px;
                    padding: 5px;
                }
            """)
            image_label.setScaledContents(False)
            
            # Görseli uygun alana ekle
            if side == "left":
                count = self.left_image_layout.count()
                self.left_image_layout.insertWidget(count - 1, image_label)
            else:  # right
                count = self.right_image_layout.count()
                self.right_image_layout.insertWidget(count - 1, image_label)
                
        except Exception as e:
            print(f"Görsel ekleme hatası: {e}")

    # BU FONKSİYONU DEĞİŞTİRİN: Sadece dialog'u çağıracak ve yanlara ekleyecek
    def insert_image(self):
        """Görsel seçtirir, boyutlandırma/hizalama dialog'unu açar ve YAN PANELE ekler."""
        path, _ = QFileDialog.getOpenFileName(self, "Görsel Seç", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            dialog = ImageCropDialog(path, self)
            
            # Dialog'u aç ve kullanıcının "Tamam"a basıp basmadığını kontrol et
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Sonuçları al
                processed_image, alignment = dialog.get_result()

                # alignment 'left' veya 'right' olabilir. Her iki durumda da yan panele ekle.
                self.add_image_to_side(processed_image, alignment)
    def increase_font(self):
        self.font_point_size += 1
        self.font_size_entry.setText(str(self.font_point_size))
        self.apply_font_size()
        self.editor.setFocus()

    def decrease_font(self):
        self.font_point_size = max(1, self.font_point_size - 1)
        self.font_size_entry.setText(str(self.font_point_size))
        self.apply_font_size()
        self.editor.setFocus()

    def apply_font_size_from_entry(self):
        value = self.font_size_entry.text()
        if value.isdigit():
            self.font_point_size = int(value)
            self.apply_font_size()

    def apply_font_size(self):
        cursor = self.editor.textCursor()
        size_fmt = QTextCharFormat()
        size_fmt.setFontPointSize(self.font_point_size)

        if cursor.hasSelection():
            cursor.mergeCharFormat(size_fmt)
        else:
            self.editor.setCurrentCharFormat(size_fmt)

    # Dosya işlemleri için ek fonksiyonlar
    def manual_save(self):
        """Manuel kaydetme - Ctrl+S"""
        path, _ = QFileDialog.getSaveFileName(self, "Dosyayı Kaydet", "", "HTML Files (*.html)")
        if path:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(self.editor.toHtml())

    def open_file(self):
        """Dosya açma - Ctrl+O"""
        path, _ = QFileDialog.getOpenFileName(self, "Dosya Aç", "", "HTML Files (*.html)")
        if path:
            with open(path, 'r', encoding='utf-8') as file:
                html = file.read()
                self.editor.setHtml(html)

    def new_file(self):
        """Yeni dosya - Ctrl+N"""
        self.editor.clear()
        self.editor.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Arapça desteği için uygulama ayarları
    app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    
    window = RichEditor()
    window.show()
    sys.exit(app.exec())