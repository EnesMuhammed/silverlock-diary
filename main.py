import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QInputDialog, QLineEdit
from PySide6.QtCore import Qt , QSize, QEvent
from manager import LoginWindow
# dashboard'dan sadece main fonksiyonunu import ediyoruz
# ve dashboard.py'deki main fonksiyonunun artık app.exec() çağırmadığından emin olmalıyız.
from dashboard import main as launch_dashboard_main_window # İsim çakışmasını önlemek için yeniden adlandırdık
from hash import hash_password, verify_password, save_hashed_password, load_hashed_password

# Ana parola hash dosyasının yolu
MAIN_PASSWORD_HASH_FILE = "sources/main.bin"

# QApplication'ı SADECE BİR KEZ oluştur
app = QApplication(sys.argv)

# Login penceresine referans tutmak için global değişken
login_window_ref = None

def launch_main_window():
    """
    Giriş başarılı olduğunda çağrılır.
    Login penceresini gizler ve ana dashboard penceresini başlatır.
    """
    global login_window_ref
    if login_window_ref:
        login_window_ref.hide() # Login penceresini gizle

    # Ana dashboard penceresini başlatmak için dashboard.py'deki main fonksiyonunu çağır
    # app objesini parametre olarak iletiyoruz, böylece dashboard.py yeni bir QApplication oluşturmaz.
    launch_dashboard_main_window(app)

if __name__ == "__main__":

    # Ana parola hash dosyasının dizinini oluştur (varsa sorun olmaz)
    os.makedirs(os.path.dirname(MAIN_PASSWORD_HASH_FILE), exist_ok=True)

    # Ana parola hash'ini depolamak için değişken
    main_app_password_hash = None

    # Parola dosyasının varlığını kontrol et
    if not os.path.exists(MAIN_PASSWORD_HASH_FILE):
        # Dosya yoksa: Uygulama ilk kez çalışıyor veya parola silinmiş.
        # Kullanıcıdan ana parola belirlemesini iste.
        QMessageBox.information(None, "Ana Parola Belirle",
                                "Uygulamayı ilk kez çalıştırıyorsunuz. Lütfen bir ana parola belirleyin.")

        new_main_password, ok = QInputDialog.getText(None, "Ana Parola",
                                                     "Lütfen uygulamanız için bir ana parola girin:", QLineEdit.Password)
        if ok and new_main_password:
            # Yeni parolayı hash'le ve kaydet
            main_app_password_hash = hash_password(new_main_password)
            save_hashed_password(MAIN_PASSWORD_HASH_FILE, main_app_password_hash)
            QMessageBox.information(None, "Parola Kaydedildi", "Ana parola başarıyla kaydedildi.")
        else:
            QMessageBox.critical(None, "Hata", "Ana parola belirlenmedi. Uygulama kapatılıyor.")
            sys.exit(1) # Parola belirlenmediği için uygulamayı kapat
    else:
        # Dosya varsa: Hash'i dosyadan yükle
        try:
            main_app_password_hash = load_hashed_password(MAIN_PASSWORD_HASH_FILE)
        except Exception as e:
            QMessageBox.critical(None, "Hata", f"Ana parola dosyası yüklenirken bir hata oluştu: {e}\nUygulama kapatılıyor.")
            sys.exit(1) # Yükleme hatası nedeniyle uygulamayı kapat

    # Eğer main_app_password_hash hala None ise (ki yukarıdaki logic ile olmamalı ama bir güvenlik katmanı),
    # bu durumu da kontrol edebilirsiniz. Genellikle yukarıdaki sys.exit'ler bunu engeller.
    if main_app_password_hash is None:
        QMessageBox.critical(None, "Hata", "Uygulama parolası yüklenemedi. Uygulama kapatılıyor.")
        sys.exit(1)

    # Ekranı ortalamak için boyutları al
    screen = app.primaryScreen()
    geom = screen.availableGeometry()
    w, h = geom.width(), geom.height()
    win_w, win_h = 400, 200 # Login penceresinin boyutu

    # LoginWindow’ı başlatırken yüklenen (veya yeni belirlenen) hash'i kullan
    login = LoginWindow(
        expected_password_hash=main_app_password_hash,
        on_success=launch_main_window
    )
    # Login penceresine referansı sakla
    login_window_ref = login

    # Login penceresini ekranın ortasına yerleştir
    login.setGeometry(
        w//2 - win_w//2,
        h//2 - win_h//2,
        win_w, win_h
    )

    login.show()
    # QApplication'ın olay döngüsünü SADECE BURADA başlat
    # Bu çağrı, uygulama kapatılana kadar bloklayacaktır.
    sys.exit(app.exec())
