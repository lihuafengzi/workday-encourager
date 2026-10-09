import json
import os
import re
import tkinter as tk
from calendar import monthrange
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from tkinter import messagebox, ttk


DEFAULT_SETTINGS = {
    "monthly_salary": "10000",
    "paid_hours": "8",
    "start_time": "09:00",
}

# 国务院办公厅《关于2026年部分节假日安排的通知》（国办发明电〔2025〕7号）
CHINA_HOLIDAY_RANGES = {
    2026: (
        ("2026-01-01", "2026-01-03"),
        ("2026-02-15", "2026-02-23"),
        ("2026-04-04", "2026-04-06"),
        ("2026-05-01", "2026-05-05"),
        ("2026-06-19", "2026-06-21"),
        ("2026-09-25", "2026-09-27"),
        ("2026-10-01", "2026-10-07"),
    )
}
CHINA_MAKEUP_WORKDAYS = {
    2026: frozenset(
        date.fromisoformat(day)
        for day in (
            "2026-01-04",
            "2026-02-14",
            "2026-02-28",
            "2026-05-09",
            "2026-09-20",
            "2026-10-10",
        )
    )
}

BACKGROUND = "#F5F4EF"
CARD = "#FFFFFF"
INK = "#18312D"
MUTED = "#71817B"
GREEN = "#16866F"
GREEN_DARK = "#116B58"
GREEN_PALE = "#E8F4EF"
BORDER = "#E5E9E4"


def validate_settings(values):
    salary = Decimal(str(values["monthly_salary"]).strip())
    if not salary.is_finite() or salary <= 0:
        raise ValueError("月薪必须是大于 0 的有效数字。")

    hours = Decimal(str(values["paid_hours"]).strip())
    if not hours.is_finite() or not Decimal("0") < hours <= Decimal("24"):
        raise ValueError("每天带薪工时必须大于 0 且不超过 24 小时。")

    start_text = str(values["start_time"]).strip()
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_text):
        raise ValueError("上班时间请按 24 小时制填写，例如 09:00。")

    return {
        "monthly_salary": format(salary, "f"),
        "paid_hours": format(hours, "f"),
        "start_time": start_text,
    }


def is_workday(day):
    """Check a date against the bundled mainland China work calendar."""
    if day.year in CHINA_MAKEUP_WORKDAYS and day in CHINA_MAKEUP_WORKDAYS[day.year]:
        return True

    for start_text, end_text in CHINA_HOLIDAY_RANGES.get(day.year, ()):
        if date.fromisoformat(start_text) <= day <= date.fromisoformat(end_text):
            return False

    return day.weekday() < 5


def count_month_workdays(year, month):
    return sum(
        is_workday(date(year, month, day))
        for day in range(1, monthrange(year, month)[1] + 1)
    )


def calendar_notice(year):
    if year in CHINA_HOLIDAY_RANGES:
        return "已计入国家节假日及调休补班"
    return "该年度节假日安排尚未收录，暂按周一至周五估算"


def calculate_earned(monthly_salary, working_days, paid_hours, start_time, now, workday=True):
    """Return today's accrued pay, rounded to the nearest cent."""
    if not workday:
        return Decimal("0.00")

    salary = Decimal(str(monthly_salary))
    days = Decimal(str(working_days))
    hours = Decimal(str(paid_hours))
    start = datetime.combine(now.date(), time.fromisoformat(start_time))
    elapsed = Decimal(str((now - start).total_seconds()))
    duration = hours * Decimal("3600")

    if elapsed <= 0:
        return Decimal("0.00")

    progress = min(elapsed / duration, Decimal("1"))
    daily_pay = salary / days
    return (daily_pay * progress).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class EncouragementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("上班鼓励器")
        self.root.configure(bg=BACKGROUND)
        self.root.minsize(620, 650)
        self.root.geometry("720x735")
        self.settings_path = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")),
            "上班鼓励器",
            "settings.json",
        )
        self.settings = self.load_settings()
        now = datetime.now()
        self.current_month = now.date().replace(day=1)
        self.current_workdays = count_month_workdays(now.year, now.month)
        self.displayed_month = (now.year, now.month)
        self.entries = {}
        self.build_ui()
        self.populate_fields()
        self.refresh_clock()

    def load_settings(self):
        try:
            with open(self.settings_path, "r", encoding="utf-8") as settings_file:
                return validate_settings(json.load(settings_file))
        except FileNotFoundError:
            return DEFAULT_SETTINGS.copy()
        except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError, InvalidOperation) as error:
            messagebox.showwarning(
                "设置已重置",
                f"无法读取已保存的设置，将使用默认值。\n\n{error}",
            )
            return DEFAULT_SETTINGS.copy()

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Salary.TEntry",
            fieldbackground=CARD,
            foreground=INK,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=(11, 10),
            font=("Microsoft YaHei UI", 11),
        )
        style.map("Salary.TEntry", bordercolor=[("focus", GREEN)])
        style.configure(
            "Save.TButton",
            background=GREEN,
            foreground="#FFFFFF",
            borderwidth=0,
            padding=(18, 11),
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.map("Save.TButton", background=[("active", GREEN_DARK)])

        outer = tk.Frame(self.root, bg=BACKGROUND, padx=34, pady=26)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=BACKGROUND)
        header.pack(fill="x", pady=(0, 18))
        tk.Label(
            header,
            text="上班鼓励器",
            bg=BACKGROUND,
            fg=INK,
            font=("Microsoft YaHei UI", 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="认真工作的每一分钟，都值得被看见。",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        hero = tk.Frame(outer, bg=INK, padx=28, pady=24)
        hero.pack(fill="x", pady=(0, 16))
        tk.Label(
            hero,
            text="今天已经赚到",
            bg=INK,
            fg="#B8CBC3",
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w")

        amount_row = tk.Frame(hero, bg=INK)
        amount_row.pack(fill="x", pady=(7, 0))
        tk.Label(
            amount_row,
            text="¥",
            bg=INK,
            fg="#9DD4BE",
            font=("Segoe UI", 22, "bold"),
        ).pack(side="left", anchor="s", pady=(0, 9))
        self.amount_label = tk.Label(
            amount_row,
            text="0.00",
            bg=INK,
            fg="#FFFFFF",
            font=("Segoe UI", 48, "bold"),
        )
        self.amount_label.pack(side="left", padx=(7, 0))

        self.status_label = tk.Label(
            hero,
            text="",
            bg=INK,
            fg="#B8CBC3",
            font=("Microsoft YaHei UI", 10),
        )
        self.status_label.pack(anchor="w", pady=(1, 0))
        self.clock_label = tk.Label(
            hero,
            text="",
            bg=INK,
            fg="#88A69B",
            font=("Segoe UI", 9),
        )
        self.clock_label.pack(anchor="w", pady=(11, 0))

        summary = tk.Frame(outer, bg=CARD, padx=20, pady=16, highlightbackground=BORDER, highlightthickness=1)
        summary.pack(fill="x", pady=(0, 16))
        summary.grid_columnconfigure(0, weight=1)
        summary.grid_columnconfigure(1, weight=1)
        self.daily_label = tk.Label(
            summary, text="", bg=CARD, fg=INK, font=("Microsoft YaHei UI", 11, "bold")
        )
        self.daily_label.grid(row=0, column=0, sticky="w")
        self.hourly_label = tk.Label(
            summary, text="", bg=CARD, fg=INK, font=("Microsoft YaHei UI", 11, "bold")
        )
        self.hourly_label.grid(row=0, column=1, sticky="w", padx=(16, 0))
        tk.Label(
            summary,
            text="按月薪 ÷ 工作天数计算",
            bg=CARD,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))
        tk.Label(
            summary,
            text="按日薪 ÷ 每日带薪工时计算",
            bg=CARD,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
        ).grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(5, 0))

        settings_card = tk.Frame(outer, bg=CARD, padx=20, pady=17, highlightbackground=BORDER, highlightthickness=1)
        settings_card.pack(fill="x", pady=(0, 13))
        tk.Label(
            settings_card,
            text="计算设置",
            bg=CARD,
            fg=INK,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 13))

        field_specs = (
            ("monthly_salary", "月薪（元）", "10000"),
            ("working_days", "本月工作日（自动）", ""),
            ("paid_hours", "每天带薪工时", "8"),
            ("start_time", "上班时间", "09:00"),
        )
        for index, (key, label, hint) in enumerate(field_specs):
            row = 1 + index // 2
            column = index % 2
            field = tk.Frame(settings_card, bg=CARD)
            field.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=(0 if column == 0 else 12, 12 if column == 0 else 0),
                pady=(0, 11 if row == 1 else 0),
            )
            settings_card.grid_columnconfigure(column, weight=1, uniform="setting_fields")
            tk.Label(
                field,
                text=label,
                bg=CARD,
                fg="#42544E",
                font=("Microsoft YaHei UI", 9),
            ).pack(anchor="w", pady=(0, 5))
            if key == "working_days":
                self.workdays_value_label = tk.Label(
                    field,
                    text="",
                    bg=GREEN_PALE,
                    fg=GREEN_DARK,
                    padx=11,
                    pady=11,
                    anchor="w",
                    font=("Microsoft YaHei UI", 11, "bold"),
                )
                self.workdays_value_label.pack(fill="x")
            else:
                entry = ttk.Entry(field, style="Salary.TEntry")
                entry.pack(fill="x")
                entry.insert(0, hint)
                self.entries[key] = entry

        settings_footer = tk.Frame(settings_card, bg=CARD)
        settings_footer.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.month_status_label = tk.Label(
            settings_footer,
            text="",
            bg=CARD,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
        )
        self.month_status_label.pack(side="left")
        ttk.Button(settings_footer, text="保存设置", style="Save.TButton", command=self.save_settings).pack(
            side="right"
        )

        tk.Label(
            outer,
            text="工作日按中国大陆国家节假日及调休安排计算；仅工作日计薪，达到每日带薪工时后按日薪封顶。",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
            wraplength=630,
            justify="left",
        ).pack(anchor="w")

    def populate_fields(self):
        for key, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, self.settings[key])
        self.update_summary()

    def update_summary(self):
        salary = Decimal(self.settings["monthly_salary"])
        days = Decimal(self.current_workdays)
        hours = Decimal(self.settings["paid_hours"])
        daily = salary / days
        hourly = daily / hours
        self.daily_label.configure(text=f"日薪  ¥{daily.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
        self.hourly_label.configure(text=f"时薪  ¥{hourly.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
        self.workdays_value_label.configure(
            text=f"{self.current_month:%Y年%m月}　{self.current_workdays} 天"
        )

    def save_settings(self):
        try:
            updated = validate_settings({key: entry.get() for key, entry in self.entries.items()})
        except (ValueError, InvalidOperation) as error:
            messagebox.showerror("设置无效", str(error), parent=self.root)
            return

        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as settings_file:
                json.dump(updated, settings_file, ensure_ascii=False, indent=2)
        except OSError as error:
            messagebox.showerror("保存失败", f"无法保存设置：\n{error}", parent=self.root)
            return

        self.settings = updated
        self.update_summary()
        self.refresh_clock()
        messagebox.showinfo("已保存", "设置已保存并立即生效。", parent=self.root)

    def refresh_clock(self):
        now = datetime.now()
        if (now.year, now.month) != self.displayed_month:
            self.current_month = now.date().replace(day=1)
            self.current_workdays = count_month_workdays(now.year, now.month)
            self.displayed_month = (now.year, now.month)
            self.update_summary()

        earned = calculate_earned(
            self.settings["monthly_salary"],
            self.current_workdays,
            self.settings["paid_hours"],
            self.settings["start_time"],
            now,
            workday=is_workday(now.date()),
        )
        self.month_status_label.configure(text=calendar_notice(now.year))
        self.amount_label.configure(text=f"{earned:,.2f}")
        start = datetime.combine(now.date(), time.fromisoformat(self.settings["start_time"]))
        end = start + timedelta(hours=float(Decimal(self.settings["paid_hours"])))
        if not is_workday(now.date()):
            status = "今天是休息日，先好好放松；休息也很重要"
        elif now < start:
            status = f"距离上班还有 {str(start - now).split('.')[0]}，先给自己一点期待"
        elif now >= end:
            status = "今日带薪工时已完成，今天的收入已稳稳到手"
        else:
            status = "每一秒都在变成收入，继续加油"
        self.status_label.configure(text=status)
        self.clock_label.configure(text=f"现在 {now:%H:%M:%S}  ·  下班计薪时间 {end:%H:%M}")
        self.root.after(500, self.refresh_clock)


if __name__ == "__main__":
    root = tk.Tk()
    EncouragementApp(root)
    root.mainloop()
