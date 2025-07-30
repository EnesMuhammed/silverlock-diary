import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QWidget, QLabel, QGridLayout,QSpacerItem, QSizePolicy, QScrollArea
from PySide6.QtCore import Qt , QSize, QEvent

from hash import hash_password, verify_password, save_hashed_password, load_hashed_password

class LoginWindow(QMainWindow):
    # expected_password yerine expected_password_hash alacak şekilde güncelledik
    def __init__(self, expected_password_hash: bytes, on_success, parent=None):
        super().__init__(parent)
        # Giriş penceresine doğrudan hashlenmiş parolayı geçiyoruz
        self.expected_password_hash = expected_password_hash 
        self.on_success = on_success
        self.setWindowTitle("Uygulama - Giriş")
        self.setGeometry(400, 200, 10, 10)  # Pencere boyutları ve pozisyonu

        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 30, 30, 20)  # Pencere kenarlarından 20px boşluk

        # Başlık
        self.title_label = QLabel("Enter Password")
        self.title_label.setStyleSheet("font-size: 20px; color: white; font-weight: bold; text-align: center; padding: 0px 0px 10px 0px;")
        self.layout.addWidget(self.title_label)
        self.layout.setAlignment(self.title_label, Qt.AlignCenter)

        # Horiantal Layout (QLineEdit ve > Butonu için)
        self.entry_layout = QHBoxLayout()

        # Tek bir QLineEdit (Entry) ekliyoruz
        self.password_entry = QLineEdit(self)
        self.password_entry.setEchoMode(QLineEdit.Password)  # Şifreyi nokta olarak göstermek için
        self.password_entry.setAlignment(Qt.AlignCenter)  # Text'in ortalanması
        self.password_entry.setStyleSheet("""
            background-color: #2E2E2E;  /* Koyu gri arka plan */
            color: white;
            font-size: 25px;
            height: 50px;
            width: 300px;
            border: none;
            border-radius: 4px;
            border-bottom: 2px solid #3498DB;  /* Mavi alt sınır */
            margin: 5px;  /* Entry'lerin arasındaki boşluğu artırmak için */
        """)
        self.entry_layout.addWidget(self.password_entry)

        # > butonu ekliyoruz
        self.enter_button = QPushButton(">", self)
        self.enter_button.setFixedSize(52, 52)  # Kare boyut
        self.enter_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-size: 20px;
                border: none;
                border-radius: 4px;
                text-align: center;
                cursor: pointer;
            }

            QPushButton:hover {
                background-color: #2980B9; /* Hover rengi */
            }

            QPushButton:pressed {
                background-color: #1F6F97; /* Tıklanmış renk */
            }
        """)
        self.entry_layout.addWidget(self.enter_button)
        self.layout.addLayout(self.entry_layout)

        # Hata mesajı etiketi
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; text-align: center;")
        self.layout.addWidget(self.error_label)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # İlk entry'e odaklan
        self.password_entry.setFocus()

        # Buton tıklama olayını bağlama
        self.enter_button.clicked.connect(self.on_enter_button_click)
    
    def authenticate(self, entered_password):
        """Girilen parolayı doğrula"""
        if verify_password(self.expected_password_hash, entered_password):
            self.close()
            self.on_success()
        else:
            self.password_entry.clear()
            self.password_entry.setFocus()
            self.error_label.setText("Yanlış Parola! Tekrar deneyin.")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def on_enter_button_click(self):
        """Butona tıklandığında parola doğrulama fonksiyonunu çalıştır"""
        self.authenticate(self.password_entry.text())

    def keyPressEvent(self, event):
        """Klavyedeki tuşları kontrol et"""
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            # Enter tuşuna basıldığında authenticate et
            self.authenticate(self.password_entry.text())

