"""PySide6 desktop GUI for vinci-convert — Catppuccin Mocha themed.

Reproduces the sam5F canvas mockup:
  • Title bar with traffic-light dots
  • App header (🎬 Vinci Convert)
  • Single File / Directory mode toggle
  • Browse row with native file/folder dialog
  • Info panel (Input / Output / Codec / Pixel Format / Audio)
  • Progress bar + stats (Elapsed / ETA / Size)
  • Action buttons: Convert / Export H264 / Clean / Quit
  • Log panel at the bottom
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import qss
from .converter import (
    collect_videos,
    default_output_dir,
    ensure_dirs,
    ffmpeg_available,
)
from .donate import PIX_KEY, SPONSORS_URL, has_pix
from .workers import ConvertWorker, ExportWorker

APP_NAME = "Vinci Convert"
APP_TAGLINE = "DaVinci Resolve Video Converter · ProRes / H264"
WINDOW_TITLE = "vinci-convert — DaVinci Resolve Converter"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(960, 760)
        self.setMinimumSize(720, 640)

        self._mode = "single"  # or "directory"
        self._thread: QThread | None = None
        self._worker: ConvertWorker | None = None
        self._converted_dir, self._exported_dir = ensure_dirs(
            default_output_dir()
        )
        self._start_time: float = 0.0
        self._eta_timer = QTimer(self)
        self._eta_timer.setInterval(200)
        self._eta_timer.timeout.connect(self._tick_stats)

        self._build_ui()
        self._connect_signals()
        self._update_info_panel()

        if not ffmpeg_available():
            QTimer.singleShot(100, self._warn_no_ffmpeg)

    # ── UI construction ───────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_title_bar())

        body = QFrame()
        body.setObjectName("Body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(32, 24, 32, 24)
        body_layout.setSpacing(20)
        root.addWidget(body, 1)

        body_layout.addWidget(self._build_header())
        body_layout.addWidget(self._build_mode_selector())
        body_layout.addLayout(self._build_browse_row())
        body_layout.addWidget(self._build_info_panel())
        body_layout.addWidget(self._build_progress_section(), 0)
        body_layout.addLayout(self._build_button_row(), 0)
        body_layout.addWidget(self._build_log_panel(), 1)
        body_layout.addWidget(self._build_support_bar())

    def _build_title_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(44)
        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 24, 0)
        h.setSpacing(0)

        title = QLabel(WINDOW_TITLE)
        title.setObjectName("TitleText")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(title, 1)
        return bar

    def _build_header(self) -> QFrame:
        row = QFrame()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        icon = QLabel("🎬")
        icon.setObjectName("AppIcon")
        h.addWidget(icon)

        col = QVBoxLayout()
        col.setSpacing(2)
        name = QLabel(APP_NAME)
        name.setObjectName("AppName")
        tag = QLabel(APP_TAGLINE)
        tag.setObjectName("AppTagline")
        col.addWidget(name)
        col.addWidget(tag)
        h.addLayout(col, 1)
        return row

    def _build_mode_selector(self) -> QFrame:
        row = QFrame()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        self.btn_single = QPushButton("●  Single File")
        self.btn_single.setObjectName("ModeSingle")
        self.btn_single.setCheckable(True)
        self.btn_single.setChecked(True)

        self.btn_dir = QPushButton("○  Directory")
        self.btn_dir.setObjectName("ModeDir")
        self.btn_dir.setCheckable(True)

        h.addWidget(self.btn_single)
        h.addWidget(self.btn_dir)
        h.addStretch(1)
        return row

    def _build_browse_row(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        self.path_input = QLineEdit()
        self.path_input.setObjectName("PathInput")
        self.path_input.setPlaceholderText(
            "Select a video file or a directory…"
        )

        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setObjectName("BrowseBtn")

        h.addWidget(self.path_input, 1)
        h.addWidget(self.browse_btn, 0)
        return h

    def _build_info_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("InfoPanel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        self.lbl_input = self._info_row(v, "Input", "InputValue")
        self.lbl_output = self._info_row(v, "Output", "OutputValue")
        self.lbl_codec = self._info_row(v, "Codec", "CodecValue")
        self.lbl_pixfmt = self._info_row(v, "Pixel Format", "PixfmtValue")
        self.lbl_audio = self._info_row(v, "Audio", "AudioValue")
        return panel

    def _info_row(self, parent_layout: QVBoxLayout, label: str, value_obj: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = QLabel(label.ljust(14))
        lbl.setObjectName("InfoLabel")
        lbl.setFixedWidth(110)
        val = QLabel("—")
        val.setObjectName(value_obj)
        row.addWidget(lbl)
        row.addWidget(val, 1)
        parent_layout.addLayout(row)
        return val

    def _build_progress_section(self) -> QFrame:
        sec = QFrame()
        v = QVBoxLayout(sec)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        # status + percent
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        self.lbl_status = QLabel("Idle")
        self.lbl_status.setObjectName("ProgressStatus")
        self.lbl_percent = QLabel("0%")
        self.lbl_percent.setObjectName("ProgressPercent")
        top.addWidget(self.lbl_status, 1)
        top.addWidget(self.lbl_percent)
        v.addLayout(top)

        # progress bar
        self.progress = QProgressBar()
        self.progress.setObjectName("ProgressBar")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        v.addWidget(self.progress)

        # stats row
        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(32)
        self.lbl_elapsed = self._stat(stats, "Elapsed", "00:00")
        self.lbl_eta = self._stat(stats, "ETA", "—")
        self.lbl_size = self._stat(stats, "Size", "—")
        stats.addStretch(1)
        v.addLayout(stats)
        return sec

    def _stat(self, parent_layout: QHBoxLayout, label: str, initial: str) -> QLabel:
        col = QVBoxLayout()
        col.setSpacing(2)
        lbl = QLabel(label)
        lbl.setObjectName("StatLabel")
        val = QLabel(initial)
        val.setObjectName("StatValue")
        col.addWidget(lbl)
        col.addWidget(val)
        parent_layout.addLayout(col)
        return val

    def _build_button_row(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)
        h.addStretch(1)

        self.btn_convert = QPushButton("▶ Convert")
        self.btn_convert.setObjectName("ConvertBtn")
        self.btn_convert.setMinimumWidth(120)

        self.btn_export = QPushButton("↩ Export H264")
        self.btn_export.setObjectName("ExportBtn")
        self.btn_export.setMinimumWidth(150)

        self.btn_clean = QPushButton("✕ Clean")
        self.btn_clean.setObjectName("CleanBtn")
        self.btn_clean.setMinimumWidth(100)

        self.btn_quit = QPushButton("⏻ Quit")
        self.btn_quit.setObjectName("QuitBtn")
        self.btn_quit.setMinimumWidth(90)

        for btn in (
            self.btn_convert,
            self.btn_export,
            self.btn_clean,
            self.btn_quit,
        ):
            h.addWidget(btn, 0)
        h.addStretch(1)
        return h

    def _build_log_panel(self) -> QFrame:
        self.log_panel = QPlainTextEdit()
        self.log_panel.setObjectName("LogPanel")
        self.log_panel.setReadOnly(True)
        self.log_panel.setMaximumBlockCount(2000)
        return self.log_panel

    def _build_support_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("SupportBar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 10, 0, 0)
        h.setSpacing(12)

        tip = QLabel("♥ vinci-convert is free — keep it alive")
        tip.setObjectName("SupportTip")

        self.btn_support = QPushButton("Support the project")
        self.btn_support.setObjectName("SupportBtn")
        self.btn_support.setCursor(Qt.CursorShape.PointingHandCursor)

        h.addWidget(tip, 1)
        h.addWidget(self.btn_support, 0)
        return bar

    # ── Signals ───────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self.btn_single.clicked.connect(lambda: self._set_mode("single"))
        self.btn_dir.clicked.connect(lambda: self._set_mode("directory"))
        self.browse_btn.clicked.connect(self._browse)
        self.btn_convert.clicked.connect(self._on_convert)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_clean.clicked.connect(self._on_clean)
        self.btn_quit.clicked.connect(self.close)
        self.btn_support.clicked.connect(self._open_support)
        self.path_input.textChanged.connect(self._update_info_panel)

    # ── Mode / browse / info ──────────────────────────────────────

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        self.btn_single.setChecked(mode == "single")
        self.btn_dir.setChecked(mode == "directory")
        self._update_info_panel()

    def _browse(self) -> None:
        if self._mode == "single":
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select a video file",
                str(Path.home()),
                "Video Files (*.mp4 *.mkv *.avi *.m4v *.mov *.webm *.flv *.ts);;All Files (*)",
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self, "Select a directory", str(Path.home())
            )
        if path:
            self.path_input.setText(path)

    def _current_path(self) -> Path | None:
        text = self.path_input.text().strip()
        if not text:
            return None
        p = Path(text).expanduser()
        return p if p.exists() else None

    def _update_info_panel(self) -> None:
        path = self._current_path()
        if path is None:
            self.lbl_input.setText("—")
            self.lbl_output.setText("—")
            self.lbl_codec.setText("—")
            self.lbl_pixfmt.setText("—")
            self.lbl_audio.setText("—")
            return

        if path.is_file():
            self.lbl_input.setText(str(path))
            self.lbl_output.setText(
                str(self._converted_dir / f"{path.stem}.mov")
            )
            self._probe_into_labels(path)
            self.lbl_audio.setText("pcm_s16be")
        else:
            videos = collect_videos(path)
            self.lbl_input.setText(str(path))
            self.lbl_output.setText(
                f"{self._converted_dir}  ({len(videos)} files)"
            )
            self.lbl_codec.setText("auto-detected per file")
            self.lbl_pixfmt.setText("auto-detected per file")
            self.lbl_audio.setText("pcm_s16be")

    def _probe_into_labels(self, path: Path) -> None:
        from .converter import ConversionType, probe

        try:
            res = probe(path)
        except Exception as exc:
            self.lbl_codec.setText(f"probe error: {exc}")
            self.lbl_pixfmt.setText("—")
            return

        label = {
            ConversionType.STANDARD: "prores_ks · profile 3 (HQ)",
            ConversionType.ALPHA: "prores_ks · profile 4444",
            ConversionType.COPY: "stream copy (already compatible)",
        }[res.conversion]
        note = {
            ConversionType.ALPHA: " (alpha detected)",
            ConversionType.COPY: " (12-bit .mov)",
            ConversionType.STANDARD: "",
        }[res.conversion]
        self.lbl_codec.setText(label)
        self.lbl_pixfmt.setText(f"{res.pix_fmt}{note}")

    # ── Actions ───────────────────────────────────────────────────

    def _on_convert(self) -> None:
        if self._thread is not None:
            return
        path = self._current_path()
        if path is None:
            QMessageBox.warning(
                self, APP_NAME, "Please select a valid file or directory."
            )
            return
        videos = collect_videos(path)
        if not videos:
            QMessageBox.warning(
                self, APP_NAME, "No video files found in the selected path."
            )
            return
        self._start_worker(ConvertWorker(videos, self._converted_dir))

    def _on_export(self) -> None:
        if self._thread is not None:
            return
        videos = sorted(self._converted_dir.glob("*.mov"))
        if not videos:
            QMessageBox.information(
                self,
                APP_NAME,
                f"No converted .mov files found in:\n{self._converted_dir}",
            )
            return
        self._start_worker(ExportWorker(videos, self._exported_dir))

    def _start_worker(self, worker: ConvertWorker | ExportWorker) -> None:
        self._set_running(True)
        self.progress.setValue(0)
        self.lbl_percent.setText("0%")
        self.lbl_status.setText("Starting…")
        self._start_time = time.time()
        self._eta_timer.start()

        thread = QThread(self)
        worker.moveToThread(thread)
        self._worker = worker
        self._thread = thread

        # connect common signals
        worker.progress.connect(self._on_progress)
        worker.log.connect(self._log)
        worker.error.connect(self._on_worker_error)
        worker.finished_all.connect(self._on_finished_all)

        if isinstance(worker, ConvertWorker):
            worker.started_file.connect(self._on_convert_started)
        else:
            worker.started_file.connect(self._on_export_started)

        thread.started.connect(worker.run)
        # When the worker is done, stop the thread's event loop so it
        # can exit cleanly — otherwise QThread.run()'s exec() never returns.
        worker.finished_all.connect(thread.quit)
        # keep references alive
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _on_convert_started(
        self, src: str, dst: str, codec: str, pixfmt: str
    ) -> None:
        self.lbl_input.setText(src)
        self.lbl_output.setText(dst)
        self.lbl_codec.setText(codec)
        self.lbl_pixfmt.setText(pixfmt)
        self.lbl_audio.setText("pcm_s16be")
        self.lbl_size.setText("…")

    def _on_export_started(self, src: str, dst: str) -> None:
        self.lbl_input.setText(src)
        self.lbl_output.setText(dst)
        self.lbl_codec.setText("libx264 · preset ultrafast · crf 0")
        self.lbl_pixfmt.setText("—")
        self.lbl_audio.setText("copy")
        self.lbl_size.setText("…")

    def _on_progress(self, pct: int, status: str) -> None:
        self.progress.setValue(pct)
        self.lbl_percent.setText(f"{pct}%")
        self.lbl_status.setText(status)

    def _tick_stats(self) -> None:
        elapsed = time.time() - self._start_time
        self.lbl_elapsed.setText(self._fmt_time(elapsed))
        pct = self.progress.value()
        if pct > 0 and pct < 100:
            total = elapsed / (pct / 100)
            eta = max(total - elapsed, 0)
            self.lbl_eta.setText(self._fmt_time(eta))
        elif pct >= 100:
            self.lbl_eta.setText("00:00")

    @staticmethod
    def _fmt_time(s: float) -> str:
        s = int(s)
        return f"{s // 60:02d}:{s % 60:02d}"

    def _on_finished_all(self, successes: int, total: int) -> None:
        self._eta_timer.stop()
        self._set_running(False)
        self.progress.setValue(100)
        self.lbl_percent.setText("100%")
        self.lbl_status.setText(
            f"Done — {successes}/{total} files succeeded"
        )
        self._log(f"✓ Finished: {successes}/{total} succeeded")
        # update output size of the last file if present
        out_text = self.lbl_output.text()
        p = Path(out_text)
        if p.is_file():
            self.lbl_size.setText(self._fmt_bytes(p.stat().st_size))

        # Thread is quitting via finished_all→thread.quit; clear refs
        # once the thread has fully finished to avoid "destroyed while
        # running" warnings.
        if self._thread is not None:
            self._thread.finished.connect(self._clear_worker_refs)

    def _clear_worker_refs(self) -> None:
        self._thread = None
        self._worker = None

    @staticmethod
    def _fmt_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.0f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    def _on_clean(self) -> None:
        if self._thread is not None:
            return
        files = [f for f in self._converted_dir.iterdir() if f.is_file()]
        if not files:
            QMessageBox.information(
                self, APP_NAME, "Nothing to clean — converted dir is empty."
            )
            return
        confirm = QMessageBox.question(
            self,
            APP_NAME,
            f"Delete ALL {len(files)} files in\n{self._converted_dir}?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        for f in files:
            f.unlink()
        self._log(f"✓ Cleaned {self._converted_dir}")
        self._update_info_panel()

    def _open_support(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("Support Vinci Convert")
        text = (
            "Vinci Convert is free and open source under GPL-3.0.\n"
            "If it saves you time, a small donation keeps it shipping:\n\n"
            f"GitHub Sponsors: {SPONSORS_URL}"
        )
        if has_pix():
            text += f"\nPIX (BRL): {PIX_KEY}"
        box.setText(text)

        sponsors_btn = box.addButton(
            "Open GitHub Sponsors", QMessageBox.ButtonRole.AcceptRole
        )
        pix_btn = None
        if has_pix():
            pix_btn = box.addButton(
                "Copy PIX key", QMessageBox.ButtonRole.ActionRole
            )
        box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is sponsors_btn:
            QDesktopServices.openUrl(QUrl(SPONSORS_URL))
        elif pix_btn is not None and clicked is pix_btn:
            QApplication.clipboard().setText(PIX_KEY)

    # ── State ─────────────────────────────────────────────────────

    def _set_running(self, running: bool) -> None:
        self.btn_convert.setEnabled(not running)
        self.btn_export.setEnabled(not running)
        self.btn_clean.setEnabled(not running)
        self.browse_btn.setEnabled(not running)
        self.path_input.setEnabled(not running)
        self.btn_single.setEnabled(not running)
        self.btn_dir.setEnabled(not running)

    def _log(self, msg: str) -> None:
        self.log_panel.appendPlainText(msg)

    def _on_worker_error(self, msg: str) -> None:
        # surface ffmpeg/worker errors both in the log and the status line
        # so a failure is never silent (the most common cause of "not working").
        self.log_panel.appendPlainText(f"⚠ {msg}")
        first_line = msg.splitlines()[0] if msg else "error"
        self.lbl_status.setText(f"⚠ {first_line}")
        self.lbl_status.setStyleSheet(f"color: {qss.RED};")

    def _warn_no_ffmpeg(self) -> None:
        QMessageBox.critical(
            self,
            APP_NAME,
            "ffmpeg and ffprobe were not found on your PATH.\n"
            "Install them first, then relaunch the app.",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._thread is not None:
            if self._worker is not None:
                self._worker.cancel()
            self._thread.quit()
            self._thread.wait(5000)
        event.accept()


def main() -> int:
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(qss.QSS)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
