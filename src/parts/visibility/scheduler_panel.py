# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""Scheduler Panel — UI for the Controlled Scheduled Mission System."""
from __future__ import annotations
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QLineEdit, QTextEdit, QCheckBox,
    QDialog, QMessageBox, QFrame, QListWidget, QListWidgetItem,
    QScrollArea, QGridLayout, QDateTimeEdit, QSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ...core.task_scheduler import (
    TaskScheduler, ScheduledTask, ScheduleType, ScheduleStatus,
    RecurrencePattern, classify_risk,
)


_STATUS_COLORS = {
    ScheduleStatus.PENDING: "#f0883e",
    ScheduleStatus.APPROVED: "#238636",
    ScheduleStatus.RUNNING: "#1f6feb",
    ScheduleStatus.COMPLETED: "#2ea043",
    ScheduleStatus.FAILED: "#f85149",
    ScheduleStatus.MISSED: "#da3633",
    ScheduleStatus.PAUSED: "#8b949e",
    ScheduleStatus.CANCELLED: "#6e7681",
}


class TaskCard(QFrame):
    approve_clicked = pyqtSignal(str)
    pause_clicked = pyqtSignal(str)
    resume_clicked = pyqtSignal(str)
    cancel_clicked = pyqtSignal(str)
    remove_clicked = pyqtSignal(str)

    def __init__(self, task: ScheduledTask, parent=None):
        super().__init__(parent)
        self._task = task
        color = _STATUS_COLORS.get(task.status, "#8b949e")
        self.setStyleSheet(f"TaskCard {{ border: 1px solid {color}; border-radius: 8px;  padding: 8px; }}")
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QHBoxLayout()
        name_lbl = QLabel(task.name)
        name_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #e6edf3;")
        header.addWidget(name_lbl)
        status_lbl = QLabel(task.status.value.upper())
        status_lbl.setStyleSheet(f"background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;")
        header.addWidget(status_lbl)
        layout.addLayout(header)

        # Details
        risk = classify_risk(task.mission_text)
        risk_lbl = QLabel(f"Risk: {risk} | Approval: {'required' if task.requires_approval else 'auto'}")
        risk_lbl.setStyleSheet("font-size: 11px; color: #8b949e;")
        layout.addWidget(risk_lbl)

        mission_lbl = QLabel(f"Mission: {task.mission_text[:100]}")
        mission_lbl.setStyleSheet("font-size: 11px; color: #8b949e;")
        mission_lbl.setWordWrap(True)
        layout.addWidget(mission_lbl)

        # Schedule info
        sched_text = f"Type: {task.schedule_type.value}"
        if task.next_run:
            try:
                nr = datetime.fromisoformat(task.next_run)
                sched_text += f" | Next: {nr.strftime('%Y-%m-%d %H:%M')}"
            except Exception:
                pass
        if task.last_run:
            try:
                lr = datetime.fromisoformat(task.last_run)
                sched_text += f" | Last: {lr.strftime('%Y-%m-%d %H:%M')}"
            except Exception:
                pass
        sched_lbl = QLabel(sched_text)
        sched_lbl.setStyleSheet("font-size: 11px; color: #768390;")
        layout.addWidget(sched_lbl)

        if task.last_result:
            res_lbl = QLabel(f"Result: {task.last_result[:80]}")
            res_lbl.setStyleSheet("font-size: 10px; color: #768390; font-style: italic;")
            res_lbl.setWordWrap(True)
            layout.addWidget(res_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        if task.status == ScheduleStatus.PENDING and task.requires_approval:
            btn_approve = QPushButton("Approve")
            btn_approve.setStyleSheet("QPushButton { background-color: #238636; color: white; border-radius: 4px; padding: 4px 12px; font-weight: bold; } QPushButton:hover { background-color: #2ea043; }")
            btn_approve.clicked.connect(lambda: self.approve_clicked.emit(task.task_id))
            btn_row.addWidget(btn_approve)
        if task.status in (ScheduleStatus.PENDING, ScheduleStatus.APPROVED):
            btn_pause = QPushButton("Pause")
            btn_pause.setStyleSheet("QPushButton { background-color: #30363d; color: #e6edf3; border-radius: 4px; padding: 4px 12px; } QPushButton:hover { background-color: #424a53; }")
            btn_pause.clicked.connect(lambda: self.pause_clicked.emit(task.task_id))
            btn_row.addWidget(btn_pause)
        if task.status == ScheduleStatus.PAUSED:
            btn_resume = QPushButton("Resume")
            btn_resume.setStyleSheet("QPushButton { background-color: #1f6feb; color: white; border-radius: 4px; padding: 4px 12px; } QPushButton:hover { background-color: #388bfd; }")
            btn_resume.clicked.connect(lambda: self.resume_clicked.emit(task.task_id))
            btn_row.addWidget(btn_resume)
        if task.status not in (ScheduleStatus.COMPLETED, ScheduleStatus.CANCELLED):
            btn_cancel = QPushButton("Cancel")
            btn_cancel.setStyleSheet("QPushButton { background-color: #da3633; color: white; border-radius: 4px; padding: 4px 12px; } QPushButton:hover { background-color: #f85149; }")
            btn_cancel.clicked.connect(lambda: self.cancel_clicked.emit(task.task_id))
            btn_row.addWidget(btn_cancel)
        btn_remove = QPushButton("Remove")
        btn_remove.setStyleSheet("QPushButton {  color: #8b949e; border-radius: 4px; padding: 4px 12px; } QPushButton:hover { background-color: #30363d; color: #e6edf3; }")
        btn_remove.clicked.connect(lambda: self.remove_clicked.emit(task.task_id))
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        layout.addLayout(btn_row)


class SchedulerPanel(QWidget):
    def __init__(self, scheduler: TaskScheduler, parent=None):
        super().__init__(parent)
        self._sched = scheduler
        self._cards: dict[str, TaskCard] = {}
        self._build_ui()
        self._connect_signals()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Scheduled Missions")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e6edf3;")
        layout.addWidget(title)

        warning = QLabel("All scheduled missions require approval before execution. No autonomous actions.")
        warning.setStyleSheet("font-size: 11px; color: #f0883e; font-style: italic;")
        layout.addWidget(warning)

        # New task form
        form_group = QGroupBox("Schedule New Mission")
        form_layout = QVBoxLayout(form_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Name:"))
        self._txt_name = QLineEdit()
        self._txt_name.setPlaceholderText("Task name...")
        self._txt_name.setStyleSheet("background-color: #0f172a; color: #e2e8f0; border: 1px solid #334155; padding: 4px; border-radius: 4px;")
        row1.addWidget(self._txt_name, 1)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Mission:"))
        self._txt_mission = QLineEdit()
        self._txt_mission.setPlaceholderText("What should the AI do?")
        self._txt_mission.setStyleSheet("background-color: #0f172a; color: #e2e8f0; border: 1px solid #334155; padding: 4px; border-radius: 4px;")
        row2.addWidget(self._txt_mission, 1)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Type:"))
        self._combo_type = QComboBox()
        self._combo_type.addItems(["Once", "Recurring"])
        self._combo_type.setStyleSheet("padding: 2px 8px;")
        row3.addWidget(self._combo_type)

        row3.addWidget(QLabel("When:"))
        self._dt_trigger = QDateTimeEdit(datetime.now() + timedelta(hours=1))
        self._dt_trigger.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._dt_trigger.setStyleSheet("padding: 2px 6px;")
        row3.addWidget(self._dt_trigger)

        row3.addWidget(QLabel("Repeat:"))
        self._combo_recurrence = QComboBox()
        self._combo_recurrence.addItems(["Hourly", "Daily", "Weekly", "Every N Min"])
        self._combo_recurrence.setStyleSheet("padding: 2px 8px;")
        row3.addWidget(self._combo_recurrence)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(1, 1440)
        self._spin_interval.setValue(60)
        self._spin_interval.setSuffix(" min")
        self._spin_interval.setStyleSheet("padding: 2px 6px;")
        row3.addWidget(self._spin_interval)
        form_layout.addLayout(row3)

        row4 = QHBoxLayout()
        self._chk_auto_safe = QCheckBox("Auto-approve safe missions (summarize, write, analyze, etc.)")
        self._chk_auto_safe.setStyleSheet("color: #8b949e;")
        row4.addWidget(self._chk_auto_safe)
        form_layout.addLayout(row4)

        self._btn_add = QPushButton("+ Schedule Task")
        self._btn_add.setStyleSheet("QPushButton { background-color: #238636; color: white; border-radius: 4px; padding: 6px 16px; font-weight: bold; } QPushButton:hover { background-color: #2ea043; }")
        self._btn_add.clicked.connect(self._on_add_task)
        form_layout.addWidget(self._btn_add)

        layout.addWidget(form_group)

        # Stats
        self._lbl_stats = QLabel()
        self._lbl_stats.setStyleSheet("font-size: 11px; color: #8b949e;")
        layout.addWidget(self._lbl_stats)

        # Task list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setSpacing(8)
        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll, 1)

        self._lbl_no_tasks = QLabel("No scheduled tasks. Create one above.")
        self._lbl_no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_no_tasks.setStyleSheet("font-size: 14px; color: #8b949e; padding: 40px;")
        self._lbl_no_tasks.setVisible(False)
        layout.addWidget(self._lbl_no_tasks)

    def _connect_signals(self):
        self._sched.task_list_changed.connect(self.refresh)
        self._sched.task_completed.connect(self._on_task_completed)
        self._sched.task_failed.connect(self._on_task_failed)
        self._sched.task_missed.connect(self._on_task_missed)
        self._sched.approval_needed.connect(self._on_approval_needed)

    def refresh(self):
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        tasks = self._sched.list_tasks()
        pending = len([t for t in tasks if t.status == ScheduleStatus.PENDING])
        missed = len([t for t in tasks if t.status == ScheduleStatus.MISSED])
        running = len([t for t in tasks if t.status == ScheduleStatus.RUNNING])
        self._lbl_stats.setText(f"Total: {len(tasks)} | Pending: {pending} | Running: {running} | Missed: {missed}")
        if not tasks:
            self._lbl_no_tasks.setVisible(True)
            return
        self._lbl_no_tasks.setVisible(False)
        for task in tasks:
            card = TaskCard(task)
            card.approve_clicked.connect(self._on_approve)
            card.pause_clicked.connect(self._on_pause)
            card.resume_clicked.connect(self._on_resume)
            card.cancel_clicked.connect(self._on_cancel)
            card.remove_clicked.connect(self._on_remove)
            self._cards_layout.addWidget(card)
            self._cards[task.task_id] = card

    def _on_add_task(self):
        name = self._txt_name.text().strip()
        mission = self._txt_mission.text().strip()
        if not name or not mission:
            QMessageBox.warning(self, "Missing Info", "Please enter a name and mission.")
            return
        is_recurring = self._combo_type.currentIndex() == 1
        trigger = self._dt_trigger.dateTime().toPyDateTime()
        rec_map = [RecurrencePattern.HOURLY, RecurrencePattern.DAILY, RecurrencePattern.WEEKLY, RecurrencePattern.EVERY_N_MINUTES]
        recurrence = rec_map[self._combo_recurrence.currentIndex()]
        interval = self._spin_interval.value()
        task = TaskScheduler.create_task(
            name=name, mission_text=mission,
            schedule_type=ScheduleType.RECURRING if is_recurring else ScheduleType.ONCE,
            trigger_time=trigger if not is_recurring else None,
            recurrence=recurrence, recurrence_interval=interval,
            auto_approve_safe=self._chk_auto_safe.isChecked(),
        )
        if self._sched.add_task(task):
            self._txt_name.clear()
            self._txt_mission.clear()
            QMessageBox.information(self, "Task Scheduled", f"Task '{name}' scheduled.\n{'Approval required before execution.' if task.requires_approval else 'Auto-approved (safe mission).'}")
        else:
            QMessageBox.warning(self, "Error", "Failed to add task.")

    def _on_approve(self, task_id: str):
        self._sched.approve_task(task_id)

    def _on_pause(self, task_id: str):
        self._sched.pause_task(task_id)

    def _on_resume(self, task_id: str):
        self._sched.resume_task(task_id)

    def _on_cancel(self, task_id: str):
        self._sched.cancel_task(task_id)

    def _on_remove(self, task_id: str):
        reply = QMessageBox.question(self, "Remove Task", "Remove this scheduled task?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._sched.remove_task(task_id)

    def _on_task_completed(self, task_id: str, result: str):
        QMessageBox.information(self, "Task Completed", f"Scheduled task completed:\n\n{result[:200]}")

    def _on_task_failed(self, task_id: str, error: str):
        QMessageBox.warning(self, "Task Failed", f"Scheduled task failed:\n\n{error[:200]}")

    def _on_task_missed(self, task_id: str):
        task = self._sched.get_task(task_id)
        name = task.name if task else task_id
        QMessageBox.warning(self, "Task Missed", f"Scheduled task '{name}' was missed — it was not approved in time.")

    def _on_approval_needed(self, task):
        name = task.name if hasattr(task, 'name') else str(task)
        reply = QMessageBox.question(self, "Approval Needed", f"Scheduled task '{name}' is due.\n\nMission: {task.mission_text[:100]}\n\nApprove execution?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._sched.approve_task(task.task_id)


class SchedulerDialog(QDialog):
    def __init__(self, scheduler: TaskScheduler, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scheduled Missions — Command Nexus(TM)")
        self.setMinimumSize(700, 700)
        self.setStyleSheet(" color: #e6edf3;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._panel = SchedulerPanel(scheduler, self)
        layout.addWidget(self._panel)
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("QPushButton { background-color: #30363d; color: #e6edf3; border-radius: 4px; padding: 6px 20px; font-weight: bold; } QPushButton:hover { background-color: #424a53; }")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
