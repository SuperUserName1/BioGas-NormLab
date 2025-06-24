from PyQt5.QtWidgets import QGraphicsOpacityEffect, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QPropertyAnimation, QTimer

class Notifications:
    def __init__(self, main_window):
        self.main_window = main_window
        self.ui = main_window.ui 

        self.opacity_notification = QGraphicsOpacityEffect()
        self.ui.label_notification.setGraphicsEffect(self.opacity_notification)
        self.opacity_notification.setOpacity(0.0)


    def load_image(self, img_path):
        image_notification = QPixmap(img_path)
        if not image_notification.isNull():
            self.ui.label_notification.setPixmap(image_notification)
        else:
            print("error import image")


    def setup_animation(self):
        self.fade_in = QPropertyAnimation(self.opacity_notification, b"opacity")
        self.fade_in.setDuration(3000)
        self.fade_in.setStartValue(1.0)
        self.fade_in.setEndValue(0.0)


    def show_notification(self):
        self.ui.label_notification.show()
        self.fade_in.start()
        QTimer.singleShot(3500, self.hide_notification)

    def hide_notification(self):
        self.ui.label_notification.hide()


    def start_notification(self, img_path):
        self.load_image(img_path)
        self.setup_animation()
        self.show_notification()

