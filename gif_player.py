"""
GIF动画播放器：用Pillow提取每一帧，QTimer控制播放帧率
支持：循环播放、透明度、镜像翻转、缩放
优化：预渲染所有帧（缩放+镜像），播放时零计算；支持后台解码
"""
from PIL import Image, ImageSequence, ImageFilter
from PySide6.QtGui import QPixmap, QImage, QTransform
from PySide6.QtCore import Qt, QObject, QTimer, Signal


class GifPlayer(QObject):
    frame_changed = Signal(QPixmap)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._raw_frames: list[QPixmap] = []
        self._frames: list[QPixmap] = []
        self._durations: list[int] = []
        self._index = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._mirrored = False
        self._scale = 1.0
        self._loop = True
        self._playing = False
        self._name = ""
        self._original_width = 0
        self._dirty = True
        self._speed = 1.0

    @property
    def name(self) -> str:
        return self._name

    @property
    def playing(self) -> bool:
        return self._playing

    @property
    def frame_width(self) -> int:
        if self._frames:
            return self._frames[0].width()
        return 0

    @property
    def original_width(self) -> int:
        return self._original_width

    @staticmethod
    def decode_frames(path: str):
        """后台线程可调用：只做Pillow解码+裁剪+alpha模糊，返回字节数据。
        返回 (frame_bytes_list, durations, original_width) 或 None。
        """
        try:
            im = Image.open(path)
        except Exception:
            return None
        raw_frames = []
        durations = []
        for frame in ImageSequence.Iterator(im):
            rgba = frame.convert("RGBA")
            raw_frames.append(rgba)
            dur = frame.info.get("duration", 80)
            if dur <= 0:
                dur = 80
            durations.append(dur)
        if not raw_frames:
            return None
        original_width = raw_frames[0].size[0]
        min_left = min_top = float("inf")
        max_right = max_bottom = 0
        for rgba in raw_frames:
            bbox = rgba.getbbox()
            if bbox:
                min_left = min(min_left, bbox[0])
                min_top = min(min_top, bbox[1])
                max_right = max(max_right, bbox[2])
                max_bottom = max(max_bottom, bbox[3])
        if max_right <= min_left or max_bottom <= min_top:
            min_left, min_top = 0, 0
            max_right, max_bottom = raw_frames[0].size
        frame_bytes = []
        for rgba in raw_frames:
            cropped = rgba.crop((min_left, min_top, max_right, max_bottom))
            r, g, b, a = cropped.split()
            a = a.filter(ImageFilter.GaussianBlur(radius=1.2))
            cropped = Image.merge("RGBA", (r, g, b, a))
            w, h = cropped.size
            data = cropped.tobytes("raw", "RGBA")
            frame_bytes.append((data, w, h))
        return (frame_bytes, durations, original_width)

    def set_raw_frames(self, frame_bytes, durations, original_width, name=""):
        """主线程调用：把字节数据转成QPixmap并准备播放。"""
        self.stop()
        self._raw_frames.clear()
        self._frames.clear()
        self._durations = list(durations)
        self._index = 0
        self._name = name
        self._original_width = original_width
        self._dirty = True
        for data, w, h in frame_bytes:
            qimg = QImage(data, w, h, w * 4, QImage.Format_RGBA8888)
            pm = QPixmap.fromImage(qimg.copy())
            self._raw_frames.append(pm)
        self._render_frames()
        return len(self._frames) > 0

    def load(self, path: str) -> bool:
        result = self.decode_frames(path)
        if result is None:
            return False
        frame_bytes, durations, original_width = result
        return self.set_raw_frames(frame_bytes, durations, original_width, name=path)

    def set_scale(self, scale: float):
        new_scale = max(0.05, min(scale, 10.0))
        if abs(new_scale - self._scale) > 1e-6:
            self._scale = new_scale
            self._dirty = True

    def set_mirrored(self, mirrored: bool):
        if mirrored != self._mirrored:
            self._mirrored = mirrored
            self._dirty = True

    def set_speed(self, speed: float):
        new_speed = max(0.5, min(speed, 3.0))
        self._speed = new_speed
        if self._playing and self._index < len(self._durations):
            self._timer.start(int(self._durations[self._index] / self._speed))

    def _render_frames(self):
        if not self._raw_frames:
            return
        self._frames.clear()
        need_mirror = self._mirrored
        need_scale = abs(self._scale - 1.0) > 1e-6
        for pm in self._raw_frames:
            if need_mirror:
                pm = pm.transformed(
                    QTransform().scale(-1, 1), Qt.SmoothTransformation
                )
            if need_scale:
                pm = pm.scaledToWidth(
                    int(pm.width() * self._scale), Qt.SmoothTransformation
                )
            self._frames.append(pm)
        self._dirty = False

    def _ensure_rendered(self):
        if self._dirty:
            self._render_frames()

    def start(self, loop: bool = True):
        self._ensure_rendered()
        if not self._frames:
            return
        self._loop = loop
        self._index = 0
        self._playing = True
        self._emit_frame()
        self._timer.start(int(self._durations[0] / self._speed))

    def stop(self):
        self._timer.stop()
        self._playing = False

    def _next_frame(self):
        self._index += 1
        if self._index >= len(self._frames):
            if self._loop:
                self._index = 0
            else:
                self.stop()
                self.finished.emit()
                return
        self._emit_frame()
        self._timer.start(int(self._durations[self._index] / self._speed))

    def _emit_frame(self):
        self.frame_changed.emit(self._frames[self._index])