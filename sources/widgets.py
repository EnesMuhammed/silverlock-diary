# widgets.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os
import sys
import subprocess

class BaseWidget(QWidget):
    """Tüm widget'lar için temel sınıf"""
    
    def __init__(self, name: str, fixed_size: QSize, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedSize(fixed_size)
        self._setup_layout()
        self._setup_button()
        self._apply_styles()
    
    def _setup_layout(self):
        """Layout kurulumu"""
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.setLayout(self.content_layout)
    
    def _setup_button(self):
        """Button kurulumu"""
        self.button = QPushButton(self.name)
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_layout.addWidget(self.button)
    
    def _apply_styles(self):
        """Stil uygulama - alt sınıflarda override edilmeli"""
        pass


class FolderWidget(BaseWidget):
    """Klasör widget'ı"""
    
    clicked = pyqtSignal(str)  # Signal tanımı
    
    def __init__(self, folder_name: str, fixed_size: QSize, current_path: str, parent=None):
        self.current_path = current_path
        super().__init__(folder_name, fixed_size, parent)
        self.button.clicked.connect(self._on_click)
    
    def _apply_styles(self):
        self.setStyleSheet("""
            background-color: #901010;
            border-radius: 4px;
        """)
        
        self.button.setStyleSheet("""
            QPushButton {
                background-color: green;
                border: none;
                color: white;
                font-size: 16px;
                text-align: center;
                white-space: normal;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
    
    def _on_click(self):
        """Klasör tıklama işlemi"""
        print(f"Folder tıklandı: {self.name}")
        print(f"Şu anki current_path: {self.current_path}")
        
        new_path = os.path.join(self.current_path, "-__" + self.name)
        print(f"Yeni path olacak: {new_path}")
        
        if os.path.exists(new_path) and os.path.isdir(new_path):
            print(f"Path geçerli, navigasyon yapılıyor...")
            # Signal emit et
            self.clicked.emit(new_path + "/")
        else:
            print(f"HATA: Path bulunamadı veya klasör değil: {new_path}")


class FileWidget(BaseWidget):
    """Dosya widget'ı"""
    
    def __init__(self, file_name: str, fixed_size: QSize, parent=None):
        super().__init__(file_name, fixed_size, parent)
        self._setup_context_menu()
        self.button.clicked.connect(self._on_click)
    
    def _apply_styles(self):
        self.setStyleSheet("""
            background-color: #414141;
            border-radius: 4px;
        """)
        
        self.button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
                text-align: center;
                white-space: normal;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
    
    def _setup_context_menu(self):
        """Sağ tık menüsü kurulumu"""
        self.button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.button.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, pos):
        """Sağ tık menüsünü göster"""
        context_menu = QMenu(self.button)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #2E2E2E;
                color: white;
                border: 1px solid #505050;
            }
            QMenu::item {
                padding: 5px 10px;
            }
            QMenu::item:selected {
                background-color: #3498DB;
            }
        """)
        
        change_password_action = context_menu.addAction("Parolayı Değiştir")
        change_password_action.triggered.connect(lambda: self._change_password())
        
        context_menu.exec(self.button.mapToGlobal(pos))
    
    def _change_password(self):
        """Parola değiştirme işlemi"""
        # Ana sınıftan change_folder_password metodunu çağır
        if hasattr(self.parent(), 'change_folder_password'):
            self.parent().change_folder_password(self.name)
    
    def _on_click(self):
        """Dosya tıklama işlemi"""
        folder_dir = os.path.join("data", self.name)
        print(f"DEBUG: Folder directory: {folder_dir}")
        password_hash_file = os.path.join(folder_dir, "content.bin")
        print(f"DEBUG: Password hash file: {password_hash_file}")

        stored_hash = None
        
        if not os.path.exists(password_hash_file):
            specific_folder_password = self.name[:3]
            QMessageBox.information(self, "Parola Belirle", 
                                    f"'{self.name}' klasörü için parola dosyası bulunamadı.\n"
                                    f"Otomatik bir parola belirlenip kaydedilecek: '{specific_folder_password}'")
            stored_hash = hash_password(specific_folder_password)
            save_hashed_password(password_hash_file, stored_hash)
            QMessageBox.information(self, "Parola Kaydedildi", "Yeni parola başarıyla kaydedildi.")
        else:
            try:
                stored_hash = load_hashed_password(password_hash_file)
                print(f"DEBUG: Password hash loaded. Length: {len(stored_hash) if stored_hash else 'None'}")
            except FileNotFoundError:
                print("DEBUG: FileNotFoundError occurred (inner try-except).")
                QMessageBox.critical(self, "Hata", f"Parola dosyası bulunamadı: '{password_hash_file}'")
                return
            except Exception as e:
                print(f"DEBUG: An unexpected exception occurred during loading: {e}")
                QMessageBox.critical(self, "Hata", f"Parola dosyası yüklenirken bir hata oluştu: {e}")
                return

        if stored_hash is None or not isinstance(stored_hash, bytes) or len(stored_hash) < 16 + 32:
            print("DEBUG: stored_hash is invalid or None after loading/setting.")
            QMessageBox.critical(self, "Hata", "Yüklenen/belirlenen parola hash'i geçersiz. Lütfen dosyayı kontrol edin.")
            return

        self._open_with_login(folder_dir, stored_hash)
    
    def _open_with_login(self, folder_dir: str, stored_hash: bytes):
        """Login penceresi ile dosya açma"""
        def on_login_success():
            if hasattr(self.parent(), 'login_window') and self.parent().login_window:
                self.parent().login_window.close()
                self.parent().login_window.deleteLater() 
                self.parent().login_window = None
            
            NOTEPAD_SCRIPT_PATH = "notepad.py" 
            notes_file_path = os.path.join(folder_dir, "content.html")

            if not os.path.exists(notes_file_path):
                try:
                    with open(notes_file_path, 'w', encoding='utf-8') as f:
                        f.write("\n")
                    print(f"DEBUG: Yeni '{notes_file_path}' dosyası oluşturuldu.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"'{notes_file_path}' dosyası oluşturulurken hata: {e}")
                    return

            print(f"'{self.name}' klasörüne tıklandı. '{notes_file_path}' dosyası açılıyor...")
            try:
                subprocess.run([sys.executable, NOTEPAD_SCRIPT_PATH, notes_file_path], check=True)
                print(f"DEBUG: Notepad uygulaması '{notes_file_path}' ile kapatıldı.")
            except FileNotFoundError:
                QMessageBox.critical(self, "Hata", f"'notepad.py' veya '{notes_file_path}' bulunamadı. Yolları kontrol edin.")
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Hata", f"Notepad uygulaması bir hata ile sonlandı. Hata kodu: {e.returncode}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Beklenmeyen bir hata oluştu: {e}")
        
        # LoginWindow'ı başlat
        if hasattr(self.parent(), 'login_window'):
            self.parent().login_window = LoginWindow(expected_password_hash=stored_hash, on_success=on_login_success)
            self.parent().login_window.show()


class AddFolderWidget(BaseWidget):
    """Klasör ekleme widget'ı"""
    
    def __init__(self, fixed_size: QSize, parent=None):
        super().__init__("+", fixed_size, parent)
    
    def _apply_styles(self):
        self.setStyleSheet("border-radius: 4px;")
        
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                border: none;
                color: white;
                font-size: 40px;
                text-align: center;
                white-space: normal;
            }
            QPushButton:hover {
                background-color: #349899;
            }
            QPushButton:pressed {
                background-color: #9998DB;
            }
        """)


class QuickAccessWidget(BaseWidget):
    """Hızlı erişim widget'ı"""
    
    def _apply_styles(self):
        self.setStyleSheet("""
            background-color: #414141;
            border-radius: 4px;
        """)
        
        self.button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
                text-align: center;
                white-space: normal;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)


class HistoryWidget(BaseWidget):
    """Geçmiş widget'ı"""
    
    def _apply_styles(self):
        self.setStyleSheet("""
            background-color: #414141;
            border-radius: 3px;
        """)
        
        self.button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
                text-align: center;
                white-space: normal;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)


# Widget oluşturucu sınıfları
class WidgetFactory:
    """Widget fabrika sınıfı"""
    
    @staticmethod
    def create_folder_widget(folder_name: str, fixed_size: QSize, current_path: str, parent=None):
        return FolderWidget(folder_name, fixed_size, current_path, parent)
    
    @staticmethod
    def create_file_widget(file_name: str, fixed_size: QSize, parent=None):
        return FileWidget(file_name, fixed_size, parent)
    
    @staticmethod
    def create_add_folder_widget(fixed_size: QSize, parent=None):
        return AddFolderWidget(fixed_size, parent)
    
    @staticmethod
    def create_quick_access_widget(item_name: str, fixed_size: QSize, parent=None):
        return QuickAccessWidget(item_name, fixed_size, parent)
    
    @staticmethod
    def create_history_widget(item_name: str, fixed_size: QSize, parent=None):
        return HistoryWidget(item_name, fixed_size, parent)


# Layout hesaplama sınıfları
class LayoutCalculator:
    """Layout boyut hesaplama sınıfı"""
    
    @staticmethod
    def calculate_widget_dimensions(container_width: int, container_height: int, 
                                  margins, title_height: int, spacing: int,
                                  widgets_per_row: int, estimated_rows: int,
                                  min_width: int = 1, min_height: int = 80):
        """Widget boyutlarını hesapla"""
        
        # Genişlik hesaplama
        horizontal_margins = margins.left() + margins.right()
        total_horizontal_spacing = spacing * (widgets_per_row - 1)
        effective_width = container_width - horizontal_margins - total_horizontal_spacing
        calculated_width = max(min_width, effective_width // widgets_per_row)
        
        # Yükseklik hesaplama
        vertical_margins = margins.top() + margins.bottom()
        total_vertical_spacing = spacing * (estimated_rows - 1)
        effective_height = container_height - title_height - vertical_margins - total_vertical_spacing + 2
        calculated_height = max(min_height, effective_height // 5)
        
        return QSize(calculated_width, calculated_height)


class GridPopulator:
    """Grid doldurma işlemleri sınıfı"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def clear_layout(self, layout):
        """Layout'u temizle"""
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item is None:
                continue
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                for j in reversed(range(item.layout().count())):
                    sub_item = item.layout().itemAt(j)
                    if sub_item and sub_item.widget():
                        sub_item.widget().deleteLater()
                item.layout().deleteLater()
            layout.removeItem(item)
    
    def populate_files_grid(self, layout, base_path: str, current_path: str, widget_size: QSize):
        """Dosya grid'ini doldur"""
        self.clear_layout(layout)
        
        if not os.path.exists(base_path):
            return
        
        # Dosya ve klasörleri al
        all_items = []
        for item in os.scandir(base_path):
            if item.is_dir():
                all_items.append(('folder', item.name))
            elif item.is_file():
                all_items.append(('file', item.name))
        
        # Sırala
        all_items.sort(key=lambda x: (x[0] == 'file', x[1].lower()))
        
        widgets_per_row = 5
        row, col = 0, 0
        
        # Column stretch'leri sıfırla
        for i in range(widgets_per_row):
            layout.setColumnStretch(i, 0)
        
        # "+" widget'ı ekle
        add_widget = WidgetFactory.create_add_folder_widget(widget_size, self.parent)
        layout.addWidget(add_widget, row, col)
        col += 1
        
        # Dosya ve klasörleri ekle
        for item_type, item_name in all_items:
            if item_type == 'folder':
                if item_name[:3] != "-__":
                    widget = WidgetFactory.create_file_widget(item_name, widget_size, self.parent)
                else:
                    folder_widget = WidgetFactory.create_folder_widget(item_name[3:], widget_size, current_path, self.parent)
                    # Folder click signal'ını bağla
                    folder_widget.clicked.connect(self.parent.navigate_to_folder)
                    widget = folder_widget
            else:
                widget = WidgetFactory.create_file_widget(item_name, widget_size, self.parent)
            
            layout.addWidget(widget, row, col)
            col += 1
            
            if col >= widgets_per_row:
                col = 0
                row += 1
        
        # Boş alanları doldur
        if col > 0:
            for i in range(col, widgets_per_row):
                layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), row, i)
        
        # Vertical spacer ekle
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), row + 1, 0, 1, widgets_per_row)
    
    def populate_quick_access_grid(self, layout, widget_size: QSize, items: list):
        """Hızlı erişim grid'ini doldur"""
        self.clear_layout(layout)
        
        rows = 2
        col = 5
        
        for i, item_name in enumerate(items):
            row = i % rows
            quick_widget = WidgetFactory.create_quick_access_widget(item_name, widget_size, self.parent)
            layout.addWidget(quick_widget, row, col)
            
            if (i + 1) % rows == 0:
                col += 1
        
        # Horizontal spacer ekle
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), 0, col + 1, rows, 1)
    
    def populate_history_grid(self, layout, widget_size: QSize, items: list):
        """Geçmiş grid'ini doldur"""
        self.clear_layout(layout)
        
        row = 0
        
        for item_name in items:
            history_widget = WidgetFactory.create_history_widget(item_name, widget_size, self.parent)
            layout.addWidget(history_widget, row, 0)
            row += 1
        
        # Vertical spacer ekle
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), row, 0)