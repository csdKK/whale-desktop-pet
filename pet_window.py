"""
鲸鱼娘桌宠 - 主窗口
透明无边框置顶窗口，播放GIF动画，支持拖拽、缩放、气泡、托盘、右键菜单
"""
import math
import os
import random
import subprocess
from PySide6.QtWidgets import (
    QWidget, QLabel, QMenu, QSystemTrayIcon, QApplication, QInputDialog,
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QCheckBox, QMessageBox, QComboBox, QTextEdit,
    QScrollArea, QTextBrowser, QSizePolicy, QFrame, QFileDialog, QSlider,
)
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QGuiApplication, QPainterPath, QPen,
    QBrush, QFontMetrics, QImage, QIcon,
)
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QSize, QRect, QRectF, QByteArray, Signal, QEvent,
    QObject, QRunnable, QThreadPool,
)

import animations
from gif_player import GifPlayer
import balance as balance_mod
import pet_config
import ai_chat
import ai_monitor


CLOUD_FILL = QColor("#FFFFFF")
CLOUD_STROKE = QColor("#203170")

AUTOSTART_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_RUN_NAME = "DSH-FatFish"


def get_app_paths() -> tuple:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pythonw = os.path.join(base_dir, "python", "pythonw.exe")
    icon = os.path.join(base_dir, "圆角-蓝色大肥鱼.ico")
    return base_dir, pythonw, icon


def set_autostart(enabled: bool):
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        if enabled:
            base_dir, pythonw, _ = get_app_paths()
            main_py = os.path.join(base_dir, "main.py")
            value = f'"{pythonw}" "{main_py}"'
            winreg.SetValueEx(key, AUTOSTART_RUN_NAME, 0, winreg.REG_SZ, value)
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_RUN_NAME)
            except OSError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass


class _AnimSignals(QObject):
    loaded = Signal(str, object)


class _AnimLoadWorker(QRunnable):
    def __init__(self, path, name, signals):
        super().__init__()
        self.path = path
        self.name = name
        self.signals = signals

    def run(self):
        result = GifPlayer.decode_frames(self.path)
        self.signals.loaded.emit(self.name, result)


class Bubble(QWidget):
    """蓬松云朵气泡：白色填充 + 深蓝色边框，底部尾巴指向鲸鱼娘"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._text = ""
        self._base_font_size = 12
        self._scale = 1.0
        self._font = QFont("Microsoft YaHei", self._base_font_size)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def set_bubble_scale(self, scale: float):
        self._scale = max(0.3, min(scale, 3.0))
        self._font = QFont("Microsoft YaHei", int(self._base_font_size * self._scale))

    def show_text(self, text: str, anchor_pos: QPoint, timeout_ms: int = 4000):
        self._text = text
        fm = QFontMetrics(self._font)
        s = self._scale
        text_w = min(max(fm.horizontalAdvance(text), int(80 * s)), int(240 * s))
        lines = self._wrap_text(fm, text, text_w)
        w = max(int(text_w + 150 * s), int(220 * s))
        h = max(int(w * 0.78), int(160 * s))
        self.setFixedSize(w, h)
        x = anchor_pos.x() - w // 2 - int(w * 0.30)
        y = anchor_pos.y() - h + int(20 * s)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = max(5, min(x, screen.width() - w - 5))
        y = max(5, y)
        self.move(x, y)
        self.show()
        self.raise_()
        self._timer.stop()
        if timeout_ms > 0:
            self._timer.start(timeout_ms)

    def _wrap_text(self, fm: QFontMetrics, text: str, max_w: int) -> list[str]:
        if fm.horizontalAdvance(text) <= max_w:
            return [text]
        lines = []
        cur = ""
        for ch in text:
            if fm.horizontalAdvance(cur + ch) > max_w and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
        return lines[:3]

    def _cloud_path(self, w: int, h: int) -> QPainterPath:
        cx = w / 2
        cy = h * 0.44
        r = h * 0.18

        path = QPainterPath()
        path.addEllipse(QRectF(w * 0.10, cy - r * 0.55, w * 0.80, r * 1.6))

        def add_circle(cx_ratio, cy_ratio, radius_ratio):
            nonlocal path
            p = QPainterPath()
            br = r * radius_ratio
            p.addEllipse(QRectF(w * cx_ratio - br, h * cy_ratio - br, 2 * br, 2 * br))
            path = path.united(p)

        add_circle(0.18, 0.42, 0.70)
        add_circle(0.32, 0.36, 0.88)
        add_circle(0.50, 0.32, 1.00)
        add_circle(0.68, 0.36, 0.92)
        add_circle(0.82, 0.42, 0.72)

        add_circle(0.24, 0.56, 0.62)
        add_circle(0.42, 0.58, 0.70)
        add_circle(0.58, 0.58, 0.70)
        add_circle(0.76, 0.56, 0.62)

        return path

    def _tail_bubbles(self, w: int, h: int) -> list[QRectF]:
        body_bottom = h * 0.58 + h * 0.18 * 0.70
        start_x = w * 0.58
        end_x = w * 0.68
        bubbles = []
        n = 3
        total_gap = h - body_bottom - 4
        for i in range(n):
            t = (i + 1) / (n + 1)
            cy = body_bottom + total_gap * t
            cx = start_x + (end_x - start_x) * (t ** 1.3)
            radius = h * 0.06 * (1 - t * 0.4)
            bubbles.append(QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius))
        return bubbles

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
            | QPainter.TextAntialiasing
        )
        w, h = self.width(), self.height()
        path = self._cloud_path(w, h)
        p.setBrush(QBrush(CLOUD_FILL))
        pen = QPen(CLOUD_STROKE)
        pen.setWidthF(2.5)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawPath(path)

        for bubble in self._tail_bubbles(w, h):
            p.drawEllipse(bubble)

        fm = QFontMetrics(self._font)
        s = self._scale
        lines = self._wrap_text(fm, self._text, w - int(150 * s))
        total_h = fm.lineSpacing() * len(lines)
        cloud_center_y = h * 0.46
        y = int(cloud_center_y) - total_h // 2 + fm.ascent()
        p.setPen(QPen(CLOUD_STROKE))
        p.setFont(self._font)
        for line in lines:
            lw = fm.horizontalAdvance(line)
            p.drawText((w - lw) // 2, y, line)
            y += fm.lineSpacing()


class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self.cfg = pet_config.load()
        self._scale = self.cfg["scale"]
        self._mirrored = self.cfg["mirrored"]
        self._current_anim = ""
        self._current_loop = True
        self._anim_queue = []
        self._non_loop_busy = False
        self._dragging = False
        self._drag_offset = QPoint()
        self._last_pos = QPoint()
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click)
        self._pending_click = False

        self._chat_worker = None
        self._thinking = False
        self._thinking_dots = 0
        self._thinking_timer = QTimer(self)
        self._thinking_timer.timeout.connect(self._update_thinking_indicator)
        self._chat_window = None

        self._anim_cache = {}
        self._anim_loading = set()
        self._pending_anim = None
        self._pending_loop = True
        self._thread_pool = QThreadPool.globalInstance()
        self._anim_signals = _AnimSignals()
        self._anim_signals.loaded.connect(self._on_anim_loaded)

        self._monitor_statuses = {}
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._do_monitor)
        if self.cfg.get("monitor_enabled"):
            interval = max(5, int(self.cfg.get("monitor_interval", 15)))
            self._monitor_timer.start(interval * 1000)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.label)

        self.player = GifPlayer(self)
        self.player.frame_changed.connect(self._on_frame)
        self.player.finished.connect(self._on_anim_finished)
        self.player.set_speed(self.cfg.get("anim_speed", 1.0))

        self.bubble = Bubble(self)

        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._play_random)
        self._auto_timer.start(self.cfg["auto_action_sec"] * 1000)

        self._balance_timer = QTimer(self)
        self._balance_timer.timeout.connect(self._refresh_balance)
        if self.cfg.get("ai_provider") == "deepseek" and self._balance_api_key():
            self._balance_timer.start(self.cfg["balance_refresh_sec"] * 1000)

        self._init_tray()
        self._play_animation(random.choice(animations.IDLE))

        self._apply_window_size()
        self._restore_position()

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = self._make_tray_icon()
        self.tray.setIcon(icon)
        self.tray.setToolTip("鲸鱼娘桌宠")
        menu = QMenu()
        menu.addAction("🐳 显示/隐藏", self.toggle_visible)
        menu.addSeparator()
        menu.addAction("💰 查看余额", self._show_balance)
        menu.addAction("🔄 刷新余额", self._refresh_balance)
        menu.addAction("📡 AI 工具状态", self.show_monitor_detail)
        menu.addSeparator()
        act_menu = menu.addMenu("🎬 点播动作")
        for cat_name, cat_anims in animations.CATEGORIES.items():
            sub = act_menu.addMenu(cat_name)
            for a in cat_anims:
                sub.addAction(a, lambda checked=False, n=a: self._play_animation(n))
        menu.addSeparator()
        menu.addAction("⚙️ 设置", self._open_settings)
        menu.addSeparator()
        menu.addAction("❌ 退出", self._quit)
        self.tray.setContextMenu(menu)
        self.tray.show()
        self.tray.activated.connect(self._on_tray_activated)

    def _make_tray_icon(self) -> QIcon:
        from PySide6.QtGui import QIcon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)
        for cand in (
            os.path.join(base_dir, "圆角-蓝色大肥鱼.ico"),
            os.path.join(parent_dir, "圆角-蓝色大肥鱼.ico"),
        ):
            if os.path.exists(cand):
                return QIcon(cand)
        pm = QPixmap(64, 64)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor("#4FC3F7"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(4, 4, 56, 56)
        p.setBrush(QColor("#0288D1"))
        p.drawEllipse(18, 14, 10, 14)
        p.drawEllipse(36, 14, 10, 14)
        p.end()
        return QIcon(pm)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_visible()

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def _apply_window_size(self):
        base_w, base_h = 220, 124
        w = int(base_w * self._scale)
        h = int(base_h * self._scale)
        self.setFixedSize(w, h)
        self.bubble.set_bubble_scale(self._scale * 0.6)

    def _restore_position(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = self.cfg["pos_x"]
        y = self.cfg["pos_y"]
        if x < 0 or y < 0:
            x = screen.width() - self.width() - 40 + random.randint(-60, 60)
            y = screen.height() - self.height() - 80 + random.randint(-60, 60)
        self.move(x, y)

    def _play_animation(self, name: str, loop: bool = True, force: bool = False):
        if not force and name == self._current_anim and self.player.playing:
            return
        if not loop and self._non_loop_busy and not force:
            self._anim_queue.append((name, loop))
            return
        if force or loop:
            self._anim_queue.clear()
            self._non_loop_busy = False
        self._play_anim_direct(name, loop)

    def _play_anim_direct(self, name: str, loop: bool):
        self._current_loop = loop
        if not loop:
            self._non_loop_busy = True
        path = animations.gif_path(name)
        cached = self._anim_cache.get(name)
        if cached is not None:
            self._apply_anim(name, cached, loop)
            return
        if name in self._anim_loading:
            self._pending_anim = name
            self._pending_loop = loop
            return
        self._anim_loading.add(name)
        self._pending_anim = name
        self._pending_loop = loop
        worker = _AnimLoadWorker(path, name, self._anim_signals)
        self._thread_pool.start(worker)

    def _on_anim_finished(self):
        self._non_loop_busy = False
        if self._anim_queue:
            name, loop = self._anim_queue.pop(0)
            self._play_anim_direct(name, loop)
        else:
            self._play_anim_direct(animations.IDLE[0], loop=True)

    def _apply_anim(self, name, decoded, loop):
        frame_bytes, durations, original_width = decoded
        self.player.set_mirrored(self._mirrored)
        if original_width > 0:
            actual_scale = (220 * self._scale) / original_width
        else:
            actual_scale = self._scale
        self.player.set_scale(actual_scale)
        if self.player.set_raw_frames(frame_bytes, durations, original_width, name=name):
            self._current_anim = name
            self.player.start(loop=loop)
        elif not loop:
            self._non_loop_busy = False
            if self._anim_queue:
                n, l = self._anim_queue.pop(0)
                self._play_anim_direct(n, l)
            else:
                self._play_anim_direct(animations.IDLE[0], loop=True)

    def _on_anim_loaded(self, name, result):
        self._anim_loading.discard(name)
        if result is None:
            return
        if len(self._anim_cache) >= 8:
            oldest = next(iter(self._anim_cache))
            del self._anim_cache[oldest]
        self._anim_cache[name] = result
        if self._pending_anim == name:
            self._apply_anim(name, result, self._pending_loop)
            self._pending_anim = None

    def _do_monitor(self):
        selected = pet_config.load().get("monitor_tools", [])
        if not selected:
            return
        try:
            statuses = ai_monitor.monitor(selected)
        except Exception:
            return
        prev = self._monitor_statuses
        self._monitor_statuses = statuses
        messages = []
        for key, st in statuses.items():
            old = prev.get(key, {})
            was_running = old.get("running", False)
            now_running = st["running"]
            if now_running and not was_running:
                messages.append(f"{st['label']} 启动了~")
            elif not now_running and was_running:
                messages.append(f"{st['label']} 关闭了")
            elif now_running:
                old_state = old.get("state", "idle")
                new_state = st.get("state", "idle")
                if old_state != "working" and new_state == "working":
                    messages.append(f"{st['label']}开始工作了~")
                elif old_state == "working" and new_state == "just_finished":
                    messages.append(f"{st['label']}工作完成~")
        if messages:
            self.bubble.show_text(
                "\n".join(messages),
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                5000,
            )

    def show_monitor_detail(self):
        selected = pet_config.load().get("monitor_tools", [])
        if not selected:
            self.bubble.show_text(
                "请先在设置 → AI 工具监测 中选择要监测的工具哦~",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                5000,
            )
            return
        statuses = self._monitor_statuses
        if not statuses:
            try:
                statuses = ai_monitor.monitor(selected)
            except Exception:
                statuses = {}
        if not statuses:
            self.bubble.show_text(
                "当前没有 AI 在运行~",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                5000,
            )
            return
        running = [st for st in statuses.values() if st.get("running")]
        if not running:
            self.bubble.show_text(
                "当前没有 AI 在运行~",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                5000,
            )
            return
        text = ai_monitor.format_status_text(statuses)
        self.bubble.show_text(
            text,
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            8000,
        )

    def _play_random(self):
        if self._non_loop_busy:
            return
        anim = animations.pick_random(exclude=self._current_anim)
        self._play_animation(anim, loop=True)

    def _on_frame(self, pm: QPixmap):
        if pm.size() != self.label.size():
            old_center = self.geometry().center()
            self.setFixedSize(pm.width(), pm.height())
            self.label.resize(pm.size())
            if not self._dragging:
                self.move(old_center.x() - pm.width() // 2, old_center.y() - pm.height() // 2)
        self.label.setPixmap(pm)

    def _on_single_click(self):
        if not self._pending_click:
            return
        self._pending_click = False
        anim = animations.pick_click(exclude=self._current_anim)
        self._play_animation(anim, loop=False)
        sayings = [
            "你好呀~", "摸摸头~", "嘻嘻~", "有什么事吗？", "今天也要加油哦！",
            "我在呢~", "喵？", "别戳我啦~", "嘿嘿~", "需要帮忙吗？","肚子又饿了，有带token给我吗~",
        ]
        self.bubble.show_text(
            random.choice(sayings),
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            3000,
        )

    def _balance_api_key(self) -> str:
        """余额查询用的 API Key：直接用 AI 对话配置的 Key"""
        return self.cfg.get("ai_api_key", "") or self.cfg.get("api_key", "")

    def _show_balance(self):
        if not self._balance_api_key():
            self.bubble.show_text(
                "请先在设置→AI对话中填入 API Key",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                4000,
            )
            self._open_settings()
            return
        self._refresh_balance(show=True)

    def _refresh_balance(self, show: bool = False):
        api_key = self._balance_api_key()
        if not api_key:
            return
        provider = self.cfg.get("ai_provider", "none")
        result = balance_mod.query_balance(provider, api_key)
        if result["is_available"]:
            bal = result["balance"]
            self.cfg["last_balance"] = bal
            pet_config.save(self.cfg)
            used_pct = min(100.0, max(0.0, (1 - bal / self.cfg["balance_cap"]) * 100))
            anim = animations.balance_animation(used_pct)
            self._play_animation(anim, loop=False)
            currency = result.get("currency", "CNY")
            symbol = {"CNY": "¥", "USD": "$", "EUR": "€"}.get(currency, currency + " ")
            self.bubble.show_text(
                f"余额 {symbol}{bal:.2f}",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                5000,
            )
        else:
            self.bubble.show_text(
                f"余额查询失败：{result['error']}",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                4000,
            )

    def _open_settings(self):
        dlg = SettingsDialog(self.cfg, None)
        dlg.accepted.connect(lambda: self._apply_settings(dlg.result))
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        dlg.setFocus()

    def _apply_settings(self, new_cfg: dict):
        self.cfg.update(new_cfg)
        pet_config.save(self.cfg)
        self._scale = self.cfg["scale"]
        self._mirrored = self.cfg["mirrored"]
        self._apply_window_size()
        self._auto_timer.setInterval(self.cfg["auto_action_sec"] * 1000)
        self.player.set_speed(self.cfg.get("anim_speed", 1.0))
        provider = self.cfg.get("ai_provider", "none")
        if provider == "deepseek" and self._balance_api_key():
            self._balance_timer.start(self.cfg["balance_refresh_sec"] * 1000)
        else:
            self._balance_timer.stop()
        if provider not in ("none", "deepseek") and self._balance_api_key():
            self.bubble.show_text(
                "我只能支持 DeepSeek 的查询余额哦~",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                4000,
            )
        self._play_animation(self._current_anim or animations.IDLE[0], force=True)
        if self.cfg.get("monitor_enabled"):
            interval = max(5, int(self.cfg.get("monitor_interval", 15)))
            self._monitor_timer.start(interval * 1000)
        else:
            self._monitor_timer.stop()
            self._monitor_statuses = {}
        set_autostart(self.cfg.get("auto_start", False))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._last_pos = e.globalPosition().toPoint()
            self._pending_click = True
            self._click_timer.start(200)

    def mouseMoveEvent(self, e):
        if self._dragging:
            new_pos = e.globalPosition().toPoint() - self._drag_offset
            if self.cfg["snap_enabled"]:
                new_pos = self._snap_to_edge(new_pos)
            self.move(new_pos)
            if (e.globalPosition().toPoint() - self._last_pos).manhattanLength() > 5:
                self._pending_click = False

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = False
            self.cfg["pos_x"] = self.x()
            self.cfg["pos_y"] = self.y()
            pet_config.save(self.cfg)

    def mouseDoubleClickEvent(self, e):
        self._pending_click = False
        self._click_timer.stop()
        self._start_chat()

    def _start_chat(self):
        if self.cfg["ai_provider"] == "none":
            self.bubble.show_text(
                "还没配置 AI 哦~\n右键→设置里选一个吧~",
                self.mapToGlobal(QPoint(self.width() // 2, 0)),
                4000,
            )
            return
        if self._chat_window is None:
            self._chat_window = ChatWindow(self)
            self._chat_window.send_request.connect(self._send_chat_message)
            self._chat_window.closed.connect(self._on_chat_window_closed)
        self._position_chat_window()
        self._chat_window.show()
        self._chat_window.raise_()
        self._chat_window.activateWindow()

    def _position_chat_window(self):
        pet_x = self.x()
        pet_y = self.y()
        pet_w = self.width()
        pet_h = self.height()
        cw = self._chat_window
        cw_w = cw.width()
        cw_h = cw.height()
        screen = QGuiApplication.primaryScreen().availableGeometry()
        margin = 20
        right_x = pet_x + pet_w + margin
        left_x = pet_x - cw_w - margin
        if right_x + cw_w <= screen.width() - 10:
            x = right_x
        elif left_x >= 10:
            x = left_x
        else:
            x = pet_x
        y = max(10, pet_y - 60)
        if y + cw_h > screen.height() - 10:
            y = max(10, screen.height() - cw_h - 10)
        cw.move(x, y)

    def _on_chat_window_closed(self):
        if self._thinking and self._chat_worker:
            self._chat_worker.requestInterruption()
            self._thinking = False
            self._thinking_timer.stop()
            self._play_animation(animations.IDLE[0])

    def _send_chat_message(self, text: str):
        if self._thinking:
            return
        if self._try_ai_status_query(text):
            return
        self._thinking = True
        self._thinking_dots = 0
        self._thinking_timer.start(400)
        anim = animations.WORK_STATUS[0]
        self._play_animation(anim, loop=True)
        self.bubble.show_text(
            "思考中",
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            0,
        )
        system_prompt = ai_chat.get_effective_prompt(self.cfg)
        self._chat_worker = ai_chat.ChatWorker(
            provider=self.cfg["ai_provider"],
            model=self.cfg["ai_model"],
            api_base=self.cfg["ai_api_base"],
            api_key=self.cfg["ai_api_key"] or self.cfg.get("api_key", ""),
            system_prompt=system_prompt,
            user_message=text.strip(),
            stream=self.cfg.get("ai_stream", True),
        )
        self._chat_worker.thinking.connect(self._on_ai_thinking)
        self._chat_worker.finished.connect(self._on_ai_finished)
        self._chat_worker.error.connect(self._on_ai_error)
        self._chat_worker.start()

    def _try_ai_status_query(self, text: str) -> bool:
        if not self._is_ai_status_query(text):
            return False
        try:
            statuses = ai_monitor.monitor(
                self.cfg.get("monitor_tools", [])
            )
        except Exception:
            statuses = {}
        reply = ai_monitor.format_status_text(statuses) or "当前没有监测到 AI 在运行~"
        self._reply_local(reply)
        return True

    @staticmethod
    def _is_ai_status_query(text: str) -> bool:
        t = text.strip().lower()
        if not t:
            return False
        tool_names = [
            "trae", "claude", "cursor", "windsurf",
        ]
        status_words = [
            "状态", "在工作", "在跑", "在运行", "运行情况", "运行状况",
            "工作情况", "在干嘛", "在做什么", "谁在", "有没有", "在线",
            "忙不忙", "忙吗", "空闲", "什么状态", "怎么样了",
        ]
        if any(n in t for n in tool_names) and any(w in t for w in status_words):
            return True
        if "ai" in t and any(w in t for w in status_words):
            return True
        if "谁在" in t and any(w in t for w in ["工作", "跑", "运行", "忙"]):
            return True
        query_words = ["ai工具", "ai 工具", "编程工具", "ai状态", "ai 状态"]
        if any(w in t for w in query_words):
            return True
        return False

    def _reply_local(self, text: str):
        self._thinking = False
        self._thinking_timer.stop()
        if self._chat_window:
            self._chat_window.update_assistant_message(text, done=True)
            self._chat_window.set_thinking(False)
        self.bubble.show_text(
            text,
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            8000,
        )

    def _update_thinking_indicator(self):
        if not self._thinking:
            return
        self._thinking_dots = (self._thinking_dots + 1) % 4
        dots = "." * self._thinking_dots
        self.bubble.show_text(
            f"思考中{dots}",
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            0,
        )

    def _on_ai_thinking(self, text: str):
        self._thinking_timer.stop()
        if self._chat_window:
            self._chat_window.update_assistant_message(text)
        self.bubble.show_text(
            text,
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            0,
        )

    def _on_ai_finished(self, text: str):
        self._thinking = False
        self._thinking_timer.stop()
        if self._chat_window:
            self._chat_window.update_assistant_message(text, done=True)
            self._chat_window.set_thinking(False)
        self.bubble.show_text(
            text,
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            8000,
        )
        self._play_animation(animations.WORK_STATUS[4], loop=False)

    def _on_ai_error(self, msg: str):
        self._thinking = False
        self._thinking_timer.stop()
        if self._chat_window:
            self._chat_window.update_assistant_message(f"出错啦：{msg}", done=True)
            self._chat_window.set_thinking(False)
        self.bubble.show_text(
            f"出错啦：{msg}",
            self.mapToGlobal(QPoint(self.width() // 2, 0)),
            5000,
        )
        self._play_animation(animations.WORK_STATUS[5], loop=False)

    def _toggle_mirror(self):
        self._mirrored = not self._mirrored
        self.cfg["mirrored"] = self._mirrored
        pet_config.save(self.cfg)
        self._play_animation(self._current_anim or animations.IDLE[0], force=True)

    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        if delta > 0:
            self._scale = min(3.0, self._scale + 0.1)
        else:
            self._scale = max(0.3, self._scale - 0.1)
        self.cfg["scale"] = self._scale
        pet_config.save(self.cfg)
        self._apply_window_size()
        self._play_animation(self._current_anim or animations.IDLE[0], force=True)

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowStaysOnTopHint)
        menu.addAction("💰 查看余额", self._show_balance)
        menu.addAction("💬 聊天", self._start_chat)
        menu.addAction("🔄 随机动作", self._play_random)
        menu.addAction("📡 AI 工具状态", self.show_monitor_detail)
        menu.addAction("🪞 镜像翻转", self._toggle_mirror)
        menu.addSeparator()
        act_menu = menu.addMenu("🎬 点播动作")
        for cat_name, cat_anims in animations.CATEGORIES.items():
            sub = act_menu.addMenu(cat_name)
            for a in cat_anims:
                sub.addAction(a, lambda checked=False, n=a: self._play_animation(n))
        menu.addSeparator()
        menu.addAction("⚙️ 设置", self._open_settings)
        menu.addAction("🙈 隐藏", self.hide)
        menu.addSeparator()
        menu.addAction("❌ 退出", self._quit)
        menu.exec(e.globalPos())

    def _snap_to_edge(self, pos: QPoint) -> QPoint:
        screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        sg = screen.geometry()
        margin = 15
        x, y = pos.x(), pos.y()
        if x < sg.left() + margin:
            x = sg.left()
        elif x + self.width() > sg.right() + 1 - margin:
            x = sg.right() + 1 - self.width()
        if y < sg.top() + margin:
            y = sg.top()
        elif y + self.height() > sg.bottom() + 1 - margin:
            y = sg.bottom() + 1 - self.height()
        return QPoint(x, y)

    def paintEvent(self, e):
        pass

    def closeEvent(self, e):
        e.ignore()
        self.hide()

    def _quit(self):
        self.cfg["pos_x"] = self.x()
        self.cfg["pos_y"] = self.y()
        pet_config.save(self.cfg)
        self.tray.hide()
        QApplication.quit()


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.resize(520, 560)
        self.result = dict(cfg)
        self._last_preset_base = ""
        self._last_preset_model = ""

        from PySide6.QtWidgets import QTabWidget, QWidget
        tabs = QTabWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tabs)

        # ===== 基础设置 =====
        base_tab = QWidget()
        layout = QFormLayout(base_tab)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.3, 3.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(cfg["scale"])
        layout.addRow("缩放比例:", self.scale_spin)

        self.auto_sec = QSpinBox()
        self.auto_sec.setRange(10, 600)
        self.auto_sec.setValue(cfg["auto_action_sec"])
        layout.addRow("自动动作间隔(秒):", self.auto_sec)

        self.bal_sec = QSpinBox()
        self.bal_sec.setRange(60, 7200)
        self.bal_sec.setValue(cfg["balance_refresh_sec"])
        layout.addRow("余额刷新间隔(秒):", self.bal_sec)

        self.cap_spin = QDoubleSpinBox()
        self.cap_spin.setRange(1.0, 1000.0)
        self.cap_spin.setValue(cfg["balance_cap"])
        layout.addRow("余额满额(元):", self.cap_spin)

        speed_row = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(5, 30)
        self.speed_slider.setSingleStep(1)
        self.speed_slider.setPageStep(5)
        self.speed_slider.setValue(int(cfg.get("anim_speed", 1.0) * 10))
        self.speed_slider.setTickPosition(QSlider.NoTicks)
        self.speed_value = QLabel()
        self.speed_value.setMinimumWidth(45)
        self.speed_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.speed_slider.valueChanged.connect(lambda v: self.speed_value.setText(f"{v / 10:.1f}x"))
        self.speed_value.setText(f"{self.speed_slider.value() / 10:.1f}x")
        speed_row.addWidget(QLabel("0.5x"))
        speed_row.addWidget(self.speed_slider, 1)
        speed_row.addWidget(QLabel("3.0x"))
        speed_row.addWidget(self.speed_value)
        speed_wrap = QWidget()
        speed_wrap.setLayout(speed_row)
        layout.addRow("动画速度:", speed_wrap)

        self.snap_chk = QCheckBox("启用屏幕边缘吸附")
        self.snap_chk.setChecked(cfg["snap_enabled"])
        layout.addRow(self.snap_chk)

        self.mirror_chk = QCheckBox("镜像翻转(朝左)")
        self.mirror_chk.setChecked(cfg["mirrored"])
        layout.addRow(self.mirror_chk)

        self.autostart_chk = QCheckBox("开机自启动")
        self.autostart_chk.setChecked(cfg.get("auto_start", False))
        layout.addRow(self.autostart_chk)

        tabs.addTab(base_tab, "基础")

        # ===== AI 设置 =====
        ai_tab = QWidget()
        ai_layout = QFormLayout(ai_tab)

        self.ai_provider = QComboBox()
        for key, name in ai_chat.PROVIDERS.items():
            self.ai_provider.addItem(name, key)
        idx = self.ai_provider.findData(cfg.get("ai_provider", "none"))
        self.ai_provider.setCurrentIndex(max(0, idx))
        self.ai_provider.currentIndexChanged.connect(self._on_provider_changed)
        ai_layout.addRow("AI 提供商:", self.ai_provider)

        self.ai_api_base = QLineEdit(cfg.get("ai_api_base", ""))
        self.ai_api_base.setPlaceholderText("Ollama: http://localhost:11434")
        ai_layout.addRow("API 地址:", self.ai_api_base)

        model_row = QHBoxLayout()
        self.ai_model = QLineEdit(cfg.get("ai_model", ""))
        self.ai_model.setPlaceholderText("模型名，如 qwen2.5:7b / deepseek-chat")
        self.detect_btn = QPushButton("🔍 检测本地模型")
        self.detect_btn.clicked.connect(self._detect_models)
        model_row.addWidget(self.ai_model)
        model_row.addWidget(self.detect_btn)
        ai_layout.addRow("模型名:", model_row)

        self.ai_api_key = QLineEdit(cfg.get("ai_api_key", ""))
        self.ai_api_key.setEchoMode(QLineEdit.Password)
        self.ai_api_key.setPlaceholderText("云端模型需要，Ollama 留空")
        ai_layout.addRow("AI API Key:", self.ai_api_key)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("提示词方案:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(180)
        self.preset_combo.addItem("系统提示词", "__system__")
        for p in cfg.get("ai_presets", []):
            self.preset_combo.addItem(p["name"], p["name"])
        active = cfg.get("ai_active_preset", "__system__")
        idx = self.preset_combo.findData(active)
        self.preset_combo.setCurrentIndex(max(0, idx))
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.preset_combo, 1)

        self.add_preset_btn = QPushButton("＋ 新建")
        self.add_preset_btn.clicked.connect(self._add_preset)
        self.del_preset_btn = QPushButton("🗑 删除")
        self.del_preset_btn.clicked.connect(self._delete_preset)
        preset_row.addWidget(self.add_preset_btn)
        preset_row.addWidget(self.del_preset_btn)
        ai_layout.addRow(preset_row)

        self._presets_list = [
            {"name": p["name"], "text": p["text"]} for p in cfg.get("ai_presets", [])
        ]

        self.ai_system_prompt = QTextEdit()
        self.ai_system_prompt.setPlaceholderText("留空则不设定 AI 身份，像官网一样直接对话")
        self.ai_system_prompt.setFixedHeight(100)
        self._on_preset_changed()
        ai_layout.addRow("提示词内容:", self.ai_system_prompt)

        self.ai_stream_chk = QCheckBox("流式输出（气泡逐字刷新）")
        self.ai_stream_chk.setChecked(cfg.get("ai_stream", True))
        ai_layout.addRow(self.ai_stream_chk)

        tabs.addTab(ai_tab, "AI 对话")

        # ===== AI 工具监测 =====
        mon_tab = QWidget()
        mon_layout = QVBoxLayout(mon_tab)

        self.monitor_chk = QCheckBox("启用 AI 工具状态监测")
        self.monitor_chk.setChecked(cfg.get("monitor_enabled", False))
        self.monitor_chk.toggled.connect(self._on_monitor_toggled)
        mon_layout.addWidget(self.monitor_chk)

        mon_layout.addWidget(QLabel("选择要监测的工具:"))
        self._monitor_checkboxes = {}
        for key, info in ai_monitor.TOOLS.items():
            cb = QCheckBox(info["label"])
            cb.setChecked(key in cfg.get("monitor_tools", []))
            self._monitor_checkboxes[key] = cb
            mon_layout.addWidget(cb)

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("监测间隔(秒):"))
        self.monitor_interval = QSpinBox()
        self.monitor_interval.setRange(5, 300)
        self.monitor_interval.setValue(cfg.get("monitor_interval", 15))
        interval_row.addWidget(self.monitor_interval)
        interval_row.addStretch()
        mon_layout.addLayout(interval_row)

        mon_layout.addStretch()
        self._on_monitor_toggled(self.monitor_chk.isChecked())
        tabs.addTab(mon_tab, "AI 工具监测")

        # ===== 按钮 =====
        btns = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        main_layout.addLayout(btns)

        self._on_provider_changed()

    def _on_monitor_toggled(self, checked):
        for cb in self._monitor_checkboxes.values():
            cb.setEnabled(checked)
        self.monitor_interval.setEnabled(checked)

    def _on_preset_changed(self):
        data = self.preset_combo.currentData()
        is_system = (data == "__system__")
        self.del_preset_btn.setEnabled(not is_system)
        if is_system:
            self.ai_system_prompt.setPlainText(ai_chat.DEFAULT_SYSTEM_PROMPT)
            self.ai_system_prompt.setReadOnly(True)
        else:
            self.ai_system_prompt.setReadOnly(False)
            for p in self._presets_list:
                if p["name"] == data:
                    self.ai_system_prompt.setPlainText(p["text"])
                    return
            self.ai_system_prompt.setPlainText("")

    def _add_preset(self):
        name, ok = QInputDialog.getText(
            self, "新建提示词方案", "方案名称:"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if name == "__system__":
            QMessageBox.warning(self, "无效名称", "不能使用系统保留名称。")
            return
        if any(p["name"] == name for p in self._presets_list):
            QMessageBox.warning(self, "重名", f"方案 \"{name}\" 已存在。")
            return
        self._presets_list.append({"name": name, "text": ""})
        self.preset_combo.addItem(name, name)
        self.preset_combo.setCurrentIndex(self.preset_combo.findData(name))

    def _delete_preset(self):
        data = self.preset_combo.currentData()
        if data == "__system__":
            return
        ret = QMessageBox.question(
            self, "删除方案",
            f"确定删除提示词方案 \"{data}\" 吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret != QMessageBox.Yes:
            return
        self._presets_list = [p for p in self._presets_list if p["name"] != data]
        self.preset_combo.removeItem(self.preset_combo.currentIndex())
        self.preset_combo.setCurrentIndex(0)

    def _on_provider_changed(self):
        provider = self.ai_provider.currentData()
        is_ollama = provider == "ollama"
        is_none = provider == "none"
        is_cloud = provider not in ("none", "ollama")
        self.detect_btn.setEnabled(is_ollama)
        self.ai_api_key.setEnabled(is_cloud)
        self.ai_model.setEnabled(not is_none)
        self.ai_api_base.setEnabled(not is_none)
        preset = ai_chat.PROVIDER_PRESETS.get(provider)
        if preset:
            if not self.ai_api_base.text().strip() or self._last_preset_base:
                self.ai_api_base.setText(preset["api_base"])
            if preset["model"] and (not self.ai_model.text().strip() or self._last_preset_model):
                self.ai_model.setText(preset["model"])
            self._last_preset_base = preset["api_base"]
            self._last_preset_model = preset["model"]
        elif provider == "ollama":
            if not self.ai_api_base.text().strip():
                self.ai_api_base.setText("http://localhost:11434")
            self._last_preset_base = "http://localhost:11434"
            self._last_preset_model = ""
        else:
            self._last_preset_base = ""
            self._last_preset_model = ""

    def _detect_models(self):
        base = self.ai_api_base.text().strip() or "http://localhost:11434"
        if not ai_chat.check_ollama_running(base):
            QMessageBox.warning(self, "检测失败", "未检测到 Ollama 服务，请确认 Ollama 已启动。")
            return
        models = ai_chat.detect_ollama_models(base)
        if not models:
            QMessageBox.information(self, "无模型", "Ollama 已运行，但未找到任何模型。\n请先运行 ollama pull <模型名> 下载模型。")
            return
        model, ok = QInputDialog.getItem(
            self, "选择模型", "检测到以下模型，请选择：", models, 0, False,
        )
        if ok and model:
            self.ai_model.setText(model)

    def _on_ok(self):
        cur_data = self.preset_combo.currentData()
        if cur_data != "__system__":
            for p in self._presets_list:
                if p["name"] == cur_data:
                    p["text"] = self.ai_system_prompt.toPlainText()
                    break
        self.result["ai_presets"] = [
            {"name": p["name"], "text": p["text"]} for p in self._presets_list
        ]
        self.result["ai_active_preset"] = cur_data
        self.result["scale"] = self.scale_spin.value()
        self.result["auto_action_sec"] = self.auto_sec.value()
        self.result["balance_refresh_sec"] = self.bal_sec.value()
        self.result["balance_cap"] = self.cap_spin.value()
        self.result["anim_speed"] = self.speed_slider.value() / 10.0
        self.result["snap_enabled"] = self.snap_chk.isChecked()
        self.result["mirrored"] = self.mirror_chk.isChecked()
        provider = self.ai_provider.currentData()
        self.result["ai_provider"] = provider
        self.result["ai_model"] = self.ai_model.text().strip()
        self.result["ai_api_base"] = self.ai_api_base.text().strip()
        self.result["ai_api_key"] = self.ai_api_key.text().strip()
        self.result["ai_stream"] = self.ai_stream_chk.isChecked()
        self.result["monitor_enabled"] = self.monitor_chk.isChecked()
        self.result["monitor_tools"] = [
            k for k, cb in self._monitor_checkboxes.items() if cb.isChecked()
        ]
        self.result["monitor_interval"] = self.monitor_interval.value()
        self.result["auto_start"] = self.autostart_chk.isChecked()
        self.accept()


class ChatWindow(QWidget):
    """类似豆包的对话窗口"""

    send_request = Signal(str)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("和鲸鱼娘聊天 🐋")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.resize(520, 640)
        self.setMinimumSize(380, 440)

        self._thinking = False
        self._streaming_label = None
        self._pending_files = []
        self.setAcceptDrops(True)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._ai_avatar_pm = self._load_avatar_pm(os.path.join(base_dir, "AI聊天头像.png"))
        self._user_avatar_pm = self._load_avatar_pm(os.path.join(base_dir, "白色米饭.png"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f7f8fa;
                border: none;
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #f7f8fa;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch(1)
        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self.attach_btn = QPushButton("···", self)
        self.attach_btn.setFixedSize(44, 64)
        self.attach_btn.setCursor(Qt.PointingHandCursor)
        self.attach_btn.setToolTip("发送本地文件给鲸鱼娘（支持文本/代码文件）")
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4e83fd;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eef3ff;
                border: 1px solid #4e83fd;
            }
        """)
        self.attach_btn.clicked.connect(self._on_attach)
        bottom.addWidget(self.attach_btn)

        self.input_edit = QTextEdit(self)
        self.input_edit.setPlaceholderText("说点什么吧... (Enter 发送, Shift+Enter 换行)")
        self.input_edit.setFixedHeight(64)
        self.input_edit.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #1a1a1a;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #4e83fd;
            }
        """)
        bottom.addWidget(self.input_edit, 1)

        self.input_edit.installEventFilter(self)

        self.send_btn = QPushButton("发送", self)
        self.send_btn.setFixedSize(72, 64)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4e83fd;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a6fd8;
            }
            QPushButton:pressed {
                background-color: #2d5bb5;
            }
            QPushButton:disabled {
                background-color: #b0b0b0;
            }
        """)
        self.send_btn.clicked.connect(self._on_send)
        bottom.addWidget(self.send_btn)

        layout.addLayout(bottom)

        self._append_assistant("你好呀～我是鲸鱼娘，有什么可以帮你的吗？😊")

    def _load_avatar_pm(self, path: str) -> QPixmap:
        pm = QPixmap(path)
        if pm.isNull():
            pm = QPixmap(36, 36)
            pm.fill(QColor("#cccccc"))
        return pm.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _avatar_label(self, pm: QPixmap) -> QLabel:
        lbl = QLabel()
        lbl.setPixmap(pm)
        lbl.setFixedSize(36, 36)
        lbl.setStyleSheet("border-radius: 18px;")
        return lbl

    def _markdown_to_html(self, text: str) -> str:
        import html as _html
        escaped = _html.escape(text)
        lines = escaped.split("\n")
        result_lines = []
        in_list = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_list:
                    result_lines.append("</ul>")
                    in_list = False
                result_lines.append("<br>")
                continue
            if stripped.startswith("### "):
                if in_list:
                    result_lines.append("</ul>")
                    in_list = False
                result_lines.append(f"<h4>{stripped[4:]}</h4>")
            elif stripped.startswith("## "):
                if in_list:
                    result_lines.append("</ul>")
                    in_list = False
                result_lines.append(f"<h3>{stripped[3:]}</h3>")
            elif stripped.startswith("# "):
                if in_list:
                    result_lines.append("</ul>")
                    in_list = False
                result_lines.append(f"<h2>{stripped[2:]}</h2>")
            elif stripped.startswith(("- ", "* ")):
                if not in_list:
                    result_lines.append("<ul>")
                    in_list = True
                item = stripped[2:]
                result_lines.append(f"<li>{item}</li>")
            elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == "." and stripped[2] == " ":
                if not in_list:
                    result_lines.append("<ol>")
                    in_list = True
                item = stripped[3:]
                result_lines.append(f"<li>{item}</li>")
            else:
                if in_list:
                    result_lines.append("</ul>")
                    in_list = False
                result_lines.append(stripped)
        if in_list:
            result_lines.append("</ul>")
        html = "".join(result_lines)
        import re
        html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
        html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", html)
        html = re.sub(r"`([^`]+)`", r'<code style="background:#e8e8e8;padding:1px 4px;border-radius:3px;">\1</code>', html)
        return html

    def _make_bubble_label(self, text: str, is_user: bool) -> QLabel:
        if is_user:
            lbl = QLabel(text)
            lbl.setTextFormat(Qt.PlainText)
        else:
            html = self._markdown_to_html(text)
            lbl = QLabel(html)
            lbl.setTextFormat(Qt.RichText)
            lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
        lbl.setWordWrap(True)
        if is_user:
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #4e83fd;
                    color: white;
                    border-radius: 14px;
                    border-top-right-radius: 2px;
                    padding: 10px 14px;
                    font-size: 14px;
                }
            """)
        else:
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    color: #1a1a1a;
                    border-radius: 14px;
                    border-top-left-radius: 2px;
                    padding: 10px 14px;
                    font-size: 14px;
                }
            """)
        lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        lbl.setMaximumWidth(max(int(self.width() * 0.75), 360))
        return lbl

    def _append_row(self, text: str, is_user: bool) -> QLabel:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        if is_user:
            row_layout.addStretch(1)
            bubble = self._make_bubble_label(text, is_user)
            row_layout.addWidget(bubble, 0, Qt.AlignTop)
            row_layout.addWidget(self._avatar_label(self._user_avatar_pm), 0, Qt.AlignTop)
        else:
            row_layout.addWidget(self._avatar_label(self._ai_avatar_pm), 0, Qt.AlignTop)
            bubble = self._make_bubble_label(text, is_user)
            row_layout.addWidget(bubble, 0, Qt.AlignTop)
            row_layout.addStretch(1)
        insert_idx = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(insert_idx, row)
        self._scroll_to_bottom()
        return bubble

    def _make_file_card(self, name: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #f5f5f7;
                border-radius: 12px;
            }
        """)
        card.setFixedWidth(220)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        icon_lbl = QLabel("📄")
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: #1a1a1a; font-size: 13px; font-weight: bold; background: transparent;")
        name_lbl.setWordWrap(True)
        ext = os.path.splitext(name)[1].lstrip(".").upper() or "FILE"
        type_lbl = QLabel(ext)
        type_lbl.setStyleSheet("color: #888888; font-size: 11px; background: transparent;")
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(type_lbl)
        layout.addLayout(info_layout, 1)
        return card

    def _append_file_card(self, name: str):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        row_layout.addStretch(1)
        row_layout.addWidget(self._make_file_card(name), 0, Qt.AlignTop)
        row_layout.addWidget(self._avatar_label(self._user_avatar_pm), 0, Qt.AlignTop)
        insert_idx = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(insert_idx, row)
        self._scroll_to_bottom()

    def _on_attach(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要发送的文件",
            os.path.expanduser("~"),
            "文本/代码文件 (*.py *.txt *.md *.json *.csv *.xml *.html *.css *.js *.ts *.java *.c *.cpp *.h *.go *.rs *.rb *.php *.sh *.bat *.ps1 *.yaml *.yml *.toml *.ini *.cfg *.log);;所有文件 (*.*)",
        )
        if not file_path:
            return
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.warning(self, "读取失败", f"无法读取文件：{e}")
            return
        self._pending_files.append((file_name, content))
        self._append_file_card(file_name)

    def _build_message_with_files(self, text: str) -> str:
        if not self._pending_files:
            return text
        parts = []
        if text:
            parts.append(text)
        else:
            parts.append("请阅读以下文件内容并简要说明：")
        for name, content in self._pending_files:
            parts.append(f"--- 文件：{name} ---\n{content}")
        return "\n\n".join(parts)

    def _send_with_files(self, text: str = ""):
        if not self._pending_files:
            return
        if self._thinking:
            return
        self.input_edit.clear()
        self._thinking = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("思考中...")
        self._streaming_label = None
        message = self._build_message_with_files(text)
        self._pending_files = []
        self.send_request.emit(message)

    def _on_send(self):
        text = self.input_edit.toPlainText().strip()
        if self._pending_files:
            if text:
                self._append_user(text)
            self._send_with_files(text)
            return
        if not text or self._thinking:
            return
        self._append_user(text)
        self.input_edit.clear()
        self._thinking = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("思考中...")
        self._streaming_label = None
        self.send_request.emit(text)

    def _append_user(self, text: str):
        self._append_row(text, is_user=True)

    def _append_assistant(self, text: str):
        self._append_row(text, is_user=False)

    def update_assistant_message(self, text: str, done: bool = False):
        if self._streaming_label is None:
            self._streaming_label = self._append_row(text, is_user=False)
        else:
            self._streaming_label.setText(self._markdown_to_html(text))
        if done:
            self._streaming_label = None
        self._scroll_to_bottom()

    def set_thinking(self, thinking: bool):
        self._thinking = thinking
        if thinking:
            self.send_btn.setEnabled(False)
            self.send_btn.setText("思考中...")
        else:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("发送")

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def eventFilter(self, obj, event):
        if obj == self.input_edit and event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() == Qt.ShiftModifier:
                    return False
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        max_w = max(int(self.width() * 0.75), 360)
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            w = item.widget()
            if w is None:
                continue
            for child in w.findChildren(QLabel):
                if child.pixmap() is None:
                    child.setMaximumWidth(max_w)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        added = 0
        for url in urls:
            if not url.isLocalFile():
                continue
            path = url.toLocalFile()
            if not os.path.isfile(path):
                continue
            name = os.path.basename(path)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                self._append_assistant(f"文件 {name} 读取失败，可能是二进制文件哦～")
                continue
            self._pending_files.append((name, content))
            self._append_file_card(name)
            added += 1
        if added:
            QTimer.singleShot(100, lambda: self._send_with_files(""))

    def closeEvent(self, e):
        self.closed.emit()
        super().closeEvent(e)