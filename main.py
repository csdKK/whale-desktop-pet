"""
鲸鱼娘桌宠 - 启动入口
双击运行即可启动桌面宠物。每次启动生成独立实例，互不干扰。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from pet_window import PetWindow
from splash import SplashWindow
import pet_config
import ai_monitor


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    instance_id = "whale-pet"
    ai_monitor.set_snapshot_instance(instance_id)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)

    def find_file(name):
        local = os.path.join(base_dir, name)
        if os.path.exists(local):
            return local
        outer = os.path.join(parent_dir, name)
        if os.path.exists(outer):
            return outer
        return ""

    icon_path = find_file("圆角-蓝色大肥鱼.ico")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    pet = PetWindow()
    if icon_path:
        pet.setWindowIcon(QIcon(icon_path))

    video_path = find_file("启动动画.mp4")
    if video_path:
        splash = SplashWindow(video_path, on_finished=lambda: pet.show())
        splash.play()
    else:
        pet.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()