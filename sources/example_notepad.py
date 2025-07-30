from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit, QToolBar,
    QFileDialog, QInputDialog, QTextBrowser,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QSpacerItem)
from PySide6.QtGui import (
    QAction, QFont, QTextCursor, QTextCharFormat, QTextListFormat,
    QDesktopServices, QMouseEvent, QIntValidator)
from PySide6.QtCore import Qt, QUrl, QSize
import sys

if len(sys.argv) > 1:
    AUTOSAVE_PATH = sys.argv[1]
else:
    AUTOSAVE_PATH = "content.html" # Varsayılan yol
# --- Clickable Links ve Checkboxlar için Özel QTextEdit Sınıfı ---
class ClickableTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction | Qt.TextInteractionFlag.LinksAccessibleByMouse)

        self.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a; /* Yazı alanı arka planı */
                color: #e0e0e0; /* Yazı rengi */
                border-radius: 3px;
                padding: 15px; /* Metin kutusunun iç padding'i */
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
            pass  # İlk çalıştırmada dosya yoksa boş geç
            
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gelişmiş Not Defteri")
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
        self.editor.setCursorWidth(2)
        
        # Metin belgesinin genişliğini, QTextEdit'in genişlemesine göre ayarla.
        # Bu değeri QTextEdit'in genişliğine göre dinamik olarak ayarlamak daha iyi olabilir
        # Ancak sabit bir değer istiyorsanız, burayı artırın.
        # Örneğin, 1000'den 1400'e çıkaralım.

        self.font_point_size = 14
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(10, 10, 10, 0)

        self.setCentralWidget(central_widget)


        self.create_custom_toolbar(main_layout)

        text_editor_layout = QHBoxLayout()
        # Sol boşluk için 1 streç faktörü ile bir esnek boşluk ekle
        text_editor_layout.addStretch(1) 

        # QTextEdit'i ekle ve ona örneğin 10 streç faktörü ver
        # Bu, QTextEdit'in sol ve sağ boşluklara göre 10 kat daha fazla genişlemesini sağlar
        text_editor_layout.addWidget(self.editor)
        text_editor_layout.setStretchFactor(self.editor, 2) # Doğrudan widget objesini veriyoruz

        # Sağ boşluk için 1 streç faktörü ile bir esnek boşluk ekle
        text_editor_layout.addStretch(1)
        
        main_layout.addLayout(text_editor_layout)

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
            ("B", self.make_bold),
            ("I", self.make_italic),
            ("1.", self.insert_numbered_list),
            ("•", self.insert_bullet_list),
            ("☐", self.insert_todo_checkbox),
            ("🔗", self.insert_link),
            ("🖼️", self.insert_image),
        ]

        button_group_widget = QWidget()
        group_layout = QHBoxLayout(button_group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)

        for text, func in buttons_data:
            button = QPushButton(text, self)
            button.clicked.connect(func)
            button.setFixedSize(QSize(30, 30))
            group_layout.addWidget(button)

        # 🎯 Font size entry alanı
        self.font_size_entry = QLineEdit(str(self.font_point_size))
        self.font_size_entry.setFixedSize(QSize(40, 33))
        self.font_size_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.font_size_entry.setValidator(QIntValidator(1, 100, self))
        self.font_size_entry.returnPressed.connect(self.apply_font_size_from_entry)

        # + ve - butonları
        plus_button = QPushButton("+", self)
        plus_button.setFixedSize(QSize(30, 30))
        plus_button.clicked.connect(self.increase_font)

        minus_button = QPushButton("-", self)
        minus_button.setFixedSize(QSize(30, 30))
        minus_button.clicked.connect(self.decrease_font)

        # Ekleme sırası: - entry +
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


    def make_bold(self):
        cursor = self.editor.textCursor()
        # Yeni format: sadece weight ve point size
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
                link_html = (
                f'<a href="{url}" '
                f'style="font-size:{self.font_point_size}pt; text-decoration:none;">'
                f'{text}</a>'
            )
            cursor.insertHtml(link_html)

    def insert_numbered_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.ListDecimal)
        cursor.createList(fmt)

    def insert_bullet_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.ListDisc)
        cursor.createList(fmt)

    def insert_todo_checkbox(self):
        cursor = self.editor.textCursor()
        cursor.insertBlock()
        cursor.insertText("☐ ")
        self.editor.setTextCursor(cursor)

    def insert_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Görsel Seç", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            html_img = f'<img src="{path}" width="300">'
            self.editor.textCursor().insertHtml(html_img)

    def increase_font(self):
        self.font_point_size += 1
        self.font_size_entry.setText(str(self.font_point_size))
        self.apply_font_size()  # Seçim varsa merge, yoksa current format

    def decrease_font(self):
        self.font_point_size = max(1, self.font_point_size - 1)
        self.font_size_entry.setText(str(self.font_point_size))
        self.apply_font_size()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RichEditor()
    window.show()
    sys.exit(app.exec())
