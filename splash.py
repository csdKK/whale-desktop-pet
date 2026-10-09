"""
启动动画播放器
播放 mp4 启动动画，结束后显示主窗口
"""
import os
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class SplashWindow(QWidget):
    """启动动画窗口：无边框居中播放 mp4，播放完自动关闭"""

    def __init__(self, video_path: str, on_finished):
        super().__init__()
        self._on_finished = on_finished
        self._finished = False

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget(self)
        layout.addWidget(self.video_widget)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.setSource(QUrl.fromLocalFile(video_path))
        self.player.mediaStatusChanged.connect(self._on_status_changed)
        self.player.errorOccurred.connect(self._on_error)

        screen = self.screen().availableGeometry() if self.screen() else None
        vid_w, vid_h = 1066, 600
        if screen:
            w = min(screen.width(), vid_w)
            h = min(screen.height(), vid_h)
            self.setGeometry(
                (screen.width() - w) // 2,
                (screen.height() - h) // 2,
                w, h,
            )
        else:
            self.resize(vid_w, vid_h)

    def play(self):
        self.show()
        self.player.play()

    def _on_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and not self._finished:
            self._finished = True
            QTimer.singleShot(200, self._finish)

    def _on_error(self, *args):
        print(f"启动动画播放出错: {args}")
        self._finished = True
        QTimer.singleShot(100, self._finish)

    def _finish(self):
        self.close()
        if self._on_finished:
            self._on_finished()

    def mousePressEvent(self, e):
        if not self._finished:
            self._finished = True
            self._finish()