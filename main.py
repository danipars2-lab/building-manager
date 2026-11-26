# -*- coding: utf-8 -*-
"""مدیریت هوشمند ساختمان - نسخه پایه قابل اجرا با Kivy و SQLite"""
import os, sys, sqlite3, datetime, shutil
from decimal import Decimal, InvalidOperation
from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase
from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'maxfps', '30')
Config.set('graphics', 'vsync', '0')

APP_TITLE = "مدیریت هوشمند ساختمان"
DB_NAME = "building_manager.db"

KV = r"""
#:import dp kivy.metrics.dp
<Label>:
    font_name: app.selected_font
<Button>:
    font_name: app.selected_font
<TextInput>:
    font_name: app.selected_font
<Spinner>:
    font_name: app.selected_font
<MainScreen>:
    BoxLayout:
        orientation: "vertical"
        spacing: dp(6)
        padding: dp(10)
        canvas.before:
            Color:
                rgba: .96,.97,.98,1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(52)
            Label:
                text: "مدیریت هوشمند ساختمان"
                bold: True
                font_size: "20sp"
                color: .10,.18,.28,1
        GridLayout:
            cols: 2
            size_hint_y: None
            height: dp(116)
            spacing: dp(6)
            Label:
                text: "موجودی صندوق\\n" + root.cash
                color: .05,.40,.27,1
                bold: True
            Label:
                text: "کل وصولی‌ها\\n" + root.receipts
                color: .10,.25,.55,1
                bold: True
            Label:
                text: "کل هزینه‌ها\\n" + root.expenses
                color: .65,.25,.12,1
                bold: True
            Label:
                text: "بدهی واحدها\\n" + root.debts
                color: .65,.15,.15,1
                bold: True
        GridLayout:
            cols: 2
            spacing: dp(7)
            size_hint_y: None
            height: dp(220)
            Button:
                text: "اطلاعات ساختمان و واحدها"
                on_release: root.manager.current = "units"
            Button:
                text: "تنظیم شارژ ماهانه"
                on_release: root.manager.current = "charge"
            Button:
                text: "ثبت وصولی"
                on_release: root.manager.current = "receipt"
            Button:
                text: "ثبت هزینه"
                on_release: root.manager.current = "expense"
            Button:
                text: "گزارش مالی و واحدها"
                on_release: root.manager.current = "reports"
            Button:
                text: "پشتیبان‌گیری"
                on_release: root.backup()
            Button:
                text: "تنظیمات و انتخاب فونت"
                on_release: root.manager.current = "settings"
        Label:
            text: root.status
            size_hint_y: None
            height: dp(38)
            color: .15,.20,.25,1

<UnitScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        Label:
            text: "اطلاعات ساختمان و واحدها"
            size_hint_y: None
            height: dp(40)
            bold: True
        TextInput:
            id: bname
            hint_text: "نام ساختمان"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: address
            hint_text: "آدرس"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: count
            hint_text: "تعداد واحدها"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(44)
        Button:
            text: "ذخیره اطلاعات ساختمان و ایجاد واحدها"
            size_hint_y: None
            height: dp(48)
            on_release: root.save_building(bname.text, address.text, count.text)
        Label:
            text: "تعریف / ویرایش واحد"
            size_hint_y: None
            height: dp(30)
        TextInput:
            id: unit_no
            hint_text: "شماره واحد"
            multiline: False
            size_hint_y: None
            height: dp(42)
        TextInput:
            id: owner
            hint_text: "نام مالک"
            multiline: False
            size_hint_y: None
            height: dp(42)
        TextInput:
            id: resident
            hint_text: "نام ساکن"
            multiline: False
            size_hint_y: None
            height: dp(42)
        TextInput:
            id: area
            hint_text: "متراژ واحد (مترمربع)"
            input_filter: "float"
            multiline: False
            size_hint_y: None
            height: dp(42)
        TextInput:
            id: people
            hint_text: "تعداد نفرات"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(42)
        Button:
            text: "ذخیره واحد"
            size_hint_y: None
            height: dp(48)
            on_release: root.save_unit(unit_no.text, owner.text, resident.text, area.text, people.text)
        Button:
            text: "بازگشت"
            size_hint_y: None
            height: dp(44)
            on_release: root.manager.current = "home"

<ChargeScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(8)
        Label:
            text: "تنظیم شارژ ماهانه"
            size_hint_y: None
            height: dp(42)
            bold: True
        TextInput:
            id: fixed
            hint_text: "مبلغ ثابت هر واحد (تومان)"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(46)
        TextInput:
            id: perperson
            hint_text: "مبلغ متغیر به ازای هر نفر (تومان)"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(46)
        TextInput:
            id: period
            hint_text: "ماه شارژ (مثلاً 1405/09)"
            multiline: False
            size_hint_y: None
            height: dp(46)
        Button:
            text: "محاسبه و ثبت شارژ تمام واحدها"
            size_hint_y: None
            height: dp(50)
            on_release: root.generate(fixed.text, perperson.text, period.text)
        Label:
            id: result
            text: ""
        Button:
            text: "بازگشت"
            size_hint_y: None
            height: dp(44)
            on_release: root.manager.current = "home"

<TransactionScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        Label:
            text: root.heading
            size_hint_y: None
            height: dp(40)
            bold: True
        TextInput:
            id: unit
            hint_text: "شماره واحد (برای هزینه خالی بگذارید)"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: title
            hint_text: "عنوان (مثلاً شارژ ماهانه / نظافت / برق)"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: amount
            hint_text: "مبلغ به تومان"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: date
            hint_text: "تاریخ (مثلاً 1405/09/03)"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: note
            hint_text: "توضیحات / روش پرداخت / شماره پیگیری"
            multiline: False
            size_hint_y: None
            height: dp(44)
        Button:
            text: "ثبت"
            size_hint_y: None
            height: dp(48)
            on_release: root.save(unit.text, title.text, amount.text, date.text, note.text)
        Label:
            id: result
            text: ""
        Button:
            text: "بازگشت"
            size_hint_y: None
            height: dp(44)
            on_release: root.manager.current = "home"

<ReportsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        Label:
            text: "گزارش‌های مالی"
            size_hint_y: None
            height: dp(40)
            bold: True
        Button:
            text: "گزارش خلاصه و مانده هر واحد"
            size_hint_y: None
            height: dp(48)
            on_release: root.show_report()
        ScrollView:
            Label:
                id: report
                text: root.report_text
                size_hint_y: None
                height: self.texture_size[1] + dp(30)
                text_size: self.width, None
                halign: "right"
                valign: "top"
                color: .12,.15,.18,1
        Button:
            text: "خروجی Excel"
            size_hint_y: None
            height: dp(46)
            on_release: root.export_excel()
        Button:
            text: "خروجی PDF"
            size_hint_y: None
            height: dp(46)
            on_release: root.export_pdf()
        Button:
            text: "بازگشت"
            size_hint_y: None
            height: dp(44)
            on_release: root.manager.current = "home"
<SettingsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(10)
        Label:
            text: "تنظیمات نمایش و فونت"
            size_hint_y: None
            height: dp(46)
            bold: True
        Label:
            text: "فونت فارسی"
            size_hint_y: None
            height: dp(34)
        Spinner:
            id: font_picker
            text: app.selected_font_label
            values: ["Vazirmatn (پیش‌فرض)", "B Nazanin", "B Yagut", "B Koodak", "B Traffic"]
            size_hint_y: None
            height: dp(48)
            on_text: root.choose_font(self.text)
        Label:
            text: root.font_status
            text_size: self.width, None
            halign: "center"
            size_hint_y: None
            height: dp(70)
        Label:
            text: "برای استفاده از فونت‌های سری B، باید نسخه مجاز آن‌ها روی ویندوز نصب باشد."
            text_size: self.width, None
            halign: "center"
        Button:
            text: "بازگشت"
            size_hint_y: None
            height: dp(46)
            on_release: root.manager.current = "home"

"""

def money(v):
    return f"{int(v or 0):,}"

class DB:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.init()
    def init(self):
        c=self.conn.cursor()
        c.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS building(id INTEGER PRIMARY KEY CHECK(id=1), name TEXT, address TEXT, unit_count INTEGER, total_area REAL);
        CREATE TABLE IF NOT EXISTS units(id INTEGER PRIMARY KEY AUTOINCREMENT, unit_no TEXT UNIQUE NOT NULL, owner TEXT, resident TEXT, area REAL DEFAULT 0, people INTEGER DEFAULT 0, active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS income_titles(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS expense_titles(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS charges(id INTEGER PRIMARY KEY AUTOINCREMENT, unit_id INTEGER NOT NULL, period TEXT NOT NULL, amount INTEGER NOT NULL, UNIQUE(unit_id,period), FOREIGN KEY(unit_id) REFERENCES units(id));
        CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY AUTOINCREMENT, unit_id INTEGER, title TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>0), date TEXT NOT NULL, period TEXT, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(unit_id) REFERENCES units(id));
        CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>0), date TEXT NOT NULL, vendor TEXT, invoice_no TEXT, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, table_name TEXT, record_id INTEGER, detail TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        for t in ["شارژ ماهانه","شارژ فوق‌العاده","کمک مالی ساکنان","درآمد اجاره مشاعات","سایر درآمدها"]:
            c.execute("INSERT OR IGNORE INTO income_titles(title) VALUES(?)",(t,))
        for t in ["نظافت","حقوق سرایدار","برق مشاعات","آب مشاعات","گاز","تعمیر آسانسور","سرویس تأسیسات","تعمیرات عمومی","خرید تجهیزات","بیمه ساختمان","سایر هزینه‌ها"]:
            c.execute("INSERT OR IGNORE INTO expense_titles(title) VALUES(?)",(t,))
        self.conn.commit()
    def totals(self):
        c=self.conn.cursor()
        inc=c.execute("SELECT COALESCE(SUM(amount),0) n FROM receipts").fetchone()["n"]
        exp=c.execute("SELECT COALESCE(SUM(amount),0) n FROM expenses").fetchone()["n"]
        due=c.execute("SELECT COALESCE(SUM(amount),0) n FROM charges").fetchone()["n"]
        paid=c.execute("SELECT COALESCE(SUM(amount),0) n FROM receipts").fetchone()["n"]
        return inc,exp,inc-exp,max(0,due-paid)
    def unit_balance(self, uid):
        c=self.conn.cursor()
        due=c.execute("SELECT COALESCE(SUM(amount),0) n FROM charges WHERE unit_id=?",(uid,)).fetchone()["n"]
        paid=c.execute("SELECT COALESCE(SUM(amount),0) n FROM receipts WHERE unit_id=?",(uid,)).fetchone()["n"]
        return due-paid

class MainScreen(Screen):
    cash=StringProperty("۰")
    receipts=StringProperty("۰")
    expenses=StringProperty("۰")
    debts=StringProperty("۰")
    status=StringProperty("آماده")
    def refresh(self):
        inc,exp,cash,debt=self.manager.db.totals()
        self.cash=money(cash)+" تومان"; self.receipts=money(inc)+" تومان"
        self.expenses=money(exp)+" تومان"; self.debts=money(debt)+" تومان"
    def backup(self):
        try:
            dest=os.path.join(App.get_running_app().user_data_dir,"backup_building_manager.db")
            self.manager.db.conn.commit(); shutil.copy2(self.manager.db.path,dest)
            self.status="نسخه پشتیبان ذخیره شد: "+dest
        except Exception as e: self.status="خطا در پشتیبان‌گیری: "+str(e)

class UnitScreen(Screen):
    def save_building(self,name,address,count):
        if not name.strip() or not count.isdigit() or int(count)<1:
            self.ids.bname.text = name
            self.ids.address.text = address
            self.ids.count.text = count
            self.manager.get_screen("home").status="نام ساختمان و تعداد واحد معتبر الزامی است."
            return
        self.manager.db.conn.execute("INSERT INTO building(id,name,address,unit_count) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,address=excluded.address,unit_count=excluded.unit_count",(name.strip(),address.strip(),int(count)))
        self.manager.db.conn.commit()
        self.manager.get_screen("home").status="اطلاعات ساختمان ذخیره شد."
    def save_unit(self,no,owner,resident,area,people):
        if not no.strip() or not (area or "0").replace(".","",1).isdigit() or not (people or "0").isdigit():
            self.manager.get_screen("home").status="شماره واحد، متراژ و تعداد نفرات را بررسی کنید."
            return
        try:
            self.manager.db.conn.execute("""INSERT INTO units(unit_no,owner,resident,area,people) VALUES(?,?,?,?,?)
            ON CONFLICT(unit_no) DO UPDATE SET owner=excluded.owner,resident=excluded.resident,area=excluded.area,people=excluded.people""",
            (no.strip(),owner.strip(),resident.strip(),float(area or 0),int(people or 0)))
            self.manager.db.conn.commit()
            self.manager.get_screen("home").status="اطلاعات واحد ذخیره شد."
        except Exception as e: self.manager.get_screen("home").status="خطا: "+str(e)

class ChargeScreen(Screen):
    def generate(self,fixed,perperson,period):
        try:
            f=int(fixed); p=int(perperson)
            if f<0 or p<0 or not period.strip(): raise ValueError()
            units=self.manager.db.conn.execute("SELECT id,people FROM units WHERE active=1").fetchall()
            if not units: raise ValueError("ابتدا واحدها را تعریف کنید.")
            for u in units:
                amt=f+p*int(u["people"] or 0)
                self.manager.db.conn.execute("INSERT INTO charges(unit_id,period,amount) VALUES(?,?,?) ON CONFLICT(unit_id,period) DO UPDATE SET amount=excluded.amount",(u["id"],period.strip(),amt))
            self.manager.db.conn.commit()
            self.ids.result.text=f"شارژ {len(units)} واحد برای دوره {period} ثبت شد."
            self.manager.get_screen("home").refresh()
        except Exception as e: self.ids.result.text="ورودی نامعتبر یا خطا: "+str(e)

class TransactionScreen(Screen):
    kind=StringProperty("receipt")
    heading=StringProperty("ثبت وصولی")
    def save(self,unit,title,amount,date,note):
        try:
            a=int(amount)
            if a<=0 or not title.strip() or not date.strip(): raise ValueError()
            if self.kind=="receipt":
                if not unit.strip(): raise ValueError("شماره واحد الزامی است.")
                u=self.manager.db.conn.execute("SELECT id FROM units WHERE unit_no=?",(unit.strip(),)).fetchone()
                if not u: raise ValueError("واحد پیدا نشد.")
                self.manager.db.conn.execute("INSERT INTO receipts(unit_id,title,amount,date,note) VALUES(?,?,?,?,?)",(u["id"],title.strip(),a,date.strip(),note.strip()))
            else:
                self.manager.db.conn.execute("INSERT INTO expenses(title,amount,date,note) VALUES(?,?,?,?)",(title.strip(),a,date.strip(),note.strip()))
            self.manager.db.conn.commit()
            self.ids.result.text="تراکنش با موفقیت ثبت شد."
            self.manager.get_screen("home").refresh()
            self.ids.amount.text=""
        except Exception as e: self.ids.result.text="خطا: "+str(e)

class ReportsScreen(Screen):
    report_text=StringProperty("برای مشاهده گزارش، دکمه گزارش را بزنید.")
    def show_report(self):
        db=self.manager.db; inc,exp,cash,debt=db.totals()
        lines=["خلاصه مالی ساختمان",f"کل وصولی: {money(inc)} تومان",f"کل هزینه: {money(exp)} تومان",f"موجودی صندوق: {money(cash)} تومان",f"کل شارژهای ثبت‌شده: {money(db.conn.execute('SELECT COALESCE(SUM(amount),0) FROM charges').fetchone()[0])} تومان","", "وضعیت واحدها:"]
        for u in db.conn.execute("SELECT * FROM units ORDER BY unit_no"):
            bal=db.unit_balance(u["id"])
            lines.append(f"واحد {u['unit_no']} | مالک: {u['owner'] or '-'} | ساکن: {u['resident'] or '-'} | متراژ: {u['area']} | نفرات: {u['people']} | "+("بدهکار" if bal>0 else "بستانکار" if bal<0 else "تسویه")+" "+money(abs(bal))+" تومان")
        lines += ["","ریز وصولی‌ها:"]
        for r in db.conn.execute("SELECT u.unit_no,r.title,r.amount,r.date FROM receipts r LEFT JOIN units u ON u.id=r.unit_id ORDER BY r.date DESC"):
            lines.append(f"{r['date']} | واحد {r['unit_no']} | {r['title']} | {money(r['amount'])}")
        lines += ["","ریز هزینه‌ها:"]
        for e in db.conn.execute("SELECT title,amount,date FROM expenses ORDER BY date DESC"):
            lines.append(f"{e['date']} | {e['title']} | {money(e['amount'])}")
        self.report_text="\\n".join(lines)
    def export_excel(self):
        try:
            from openpyxl import Workbook
            path=os.path.join(App.get_running_app().user_data_dir,"گزارش_ساختمان.xlsx")
            wb=Workbook(); ws=wb.active; ws.title="خلاصه"
            ws.append(["گزارش مالی ساختمان","مبلغ (تومان)"])
            inc,exp,cash,debt=self.manager.db.totals()
            for row in [("وصولی",inc),("هزینه",exp),("موجودی",cash),("بدهی محاسبه‌شده",debt)]: ws.append(list(row))
            wu=wb.create_sheet("واحدها"); wu.append(["واحد","مالک","ساکن","متراژ","نفرات","مانده"])
            for u in self.manager.db.conn.execute("SELECT * FROM units ORDER BY unit_no"):
                wu.append([u["unit_no"],u["owner"],u["resident"],u["area"],u["people"],self.manager.db.unit_balance(u["id"])])
            wr=wb.create_sheet("وصولی‌ها"); wr.append(["واحد","عنوان","مبلغ","تاریخ","توضیحات"])
            for r in self.manager.db.conn.execute("SELECT u.unit_no,r.* FROM receipts r LEFT JOIN units u ON u.id=r.unit_id"):
                wr.append([r["unit_no"],r["title"],r["amount"],r["date"],r["note"]])
            we=wb.create_sheet("هزینه‌ها"); we.append(["عنوان","مبلغ","تاریخ","توضیحات"])
            for e in self.manager.db.conn.execute("SELECT * FROM expenses"): we.append([e["title"],e["amount"],e["date"],e["note"]])
            wb.save(path); self.report_text += "\\n\\nفایل Excel ذخیره شد: "+path
        except Exception as e: self.report_text += "\\nخطا در Excel: "+str(e)
    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            path=os.path.join(App.get_running_app().user_data_dir,"گزارش_ساختمان.pdf")
            c=canvas.Canvas(path,pagesize=A4); w,h=A4
            c.setFont("Helvetica",10)
            y=h-45
            for line in self.report_text.splitlines():
                # ReportLab's built-in Helvetica cannot shape Persian; store readable UTF-8 text in Excel
                safe=line.encode("ascii","backslashreplace").decode("ascii")
                c.drawRightString(w-35,y,safe[:115]); y-=16
                if y<45: c.showPage(); c.setFont("Helvetica",10); y=h-45
            c.save(); self.report_text += "\\n\\nفایل PDF ذخیره شد: "+path+" (نسخه پایه؛ برای نمایش صحیح فارسی باید فونت فارسی در بسته نهایی افزوده شود.)"
        except Exception as e: self.report_text += "\\nخطا در PDF: "+str(e)

class SettingsScreen(Screen):
    font_status = StringProperty("فونت پیش‌فرض فعال است.")
    def choose_font(self, label):
        app = App.get_running_app()
        try:
            if label == "Vazirmatn (پیش‌فرض)":
                app.selected_font = "Persian"
                app.selected_font_label = label
                self.font_status = "فونت پیش‌فرض فعال شد."
                app.save_font_preference(label)
                return
            path = app.find_windows_font(label)
            if not path:
                self.font_status = "این فونت روی ویندوز نصب نیست. ابتدا نسخه مجاز فونت را نصب کنید."
                return
            LabelBase.register(name=label, fn_regular=path, fn_bold=path, fn_italic=path, fn_bolditalic=path)
            app.selected_font = label
            app.selected_font_label = label
            app.save_font_preference(label)
            self.font_status = "فونت " + label + " فعال شد."
        except Exception as exc:
            self.font_status = "امکان فعال‌سازی فونت وجود ندارد: " + str(exc)

class RootManager(ScreenManager):
    db=None

class BuildingManagerApp(App):
    selected_font = StringProperty("Persian")
    selected_font_label = StringProperty("Vazirmatn (پیش‌فرض)")

    def save_font_preference(self, label):
        try:
            import json
            path = os.path.join(self.user_data_dir, "settings.json")
            with open(path, "w", encoding="utf-8") as stream:
                json.dump({"font": label}, stream, ensure_ascii=False)
        except Exception:
            pass

    def find_windows_font(self, family):
        if platform != "win":
            return None
        import winreg
        candidates = {
            "B Nazanin": ("B Nazanin", "BNazanin.ttf", "B Nazanin (TrueType)"),
            "B Yagut": ("B Yagut", "BYagut.ttf", "B Yagut (TrueType)"),
            "B Koodak": ("B Koodak", "BKoodakBold.ttf", "B Koodak (TrueType)"),
            "B Traffic": ("B Traffic", "BTraffic.ttf", "B Traffic (TrueType)")
        }
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        ]
        names = candidates.get(family, ())
        for hive, key in keys:
            try:
                with winreg.OpenKey(hive, key) as handle:
                    count = winreg.QueryInfoKey(handle)[1]
                    for index in range(count):
                        name, value, _ = winreg.EnumValue(handle, index)
                        if any(token.lower() in name.lower() for token in names):
                            path = value if os.path.isabs(value) else os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", value)
                            if os.path.isfile(path):
                                return path
            except OSError:
                continue
        fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        for filename in names:
            path = os.path.join(fonts_dir, filename)
            if os.path.isfile(path):
                return path
        return None

    def build(self):
        os.makedirs(self.user_data_dir,exist_ok=True)
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_dir, "fonts", "Vazirmatn-Regular.ttf")
        if not os.path.isfile(font_path):
            raise FileNotFoundError("فونت فارسی برنامه پیدا نشد: " + font_path)
        LabelBase.register(name="Persian", fn_regular=font_path, fn_bold=font_path, fn_italic=font_path, fn_bolditalic=font_path)
        try:
            import json
            settings_path = os.path.join(self.user_data_dir, "settings.json")
            if os.path.isfile(settings_path):
                with open(settings_path, "r", encoding="utf-8") as stream:
                    saved = json.load(stream).get("font", "Vazirmatn (پیش‌فرض)")
                if saved != "Vazirmatn (پیش‌فرض)":
                    saved_path = self.find_windows_font(saved)
                    if saved_path:
                        LabelBase.register(name=saved, fn_regular=saved_path, fn_bold=saved_path, fn_italic=saved_path, fn_bolditalic=saved_path)
                        self.selected_font = saved
                        self.selected_font_label = saved
        except Exception:
            pass
        dbpath=os.path.join(self.user_data_dir,DB_NAME)
        self.db=DB(dbpath)
        Builder.load_string(KV)
        sm=RootManager()
        home=MainScreen(name="home"); units=UnitScreen(name="units"); charge=ChargeScreen(name="charge")
        receipt=TransactionScreen(name="receipt",kind="receipt",heading="ثبت وصولی")
        expense=TransactionScreen(name="expense",kind="expense",heading="ثبت هزینه")
        reports=ReportsScreen(name="reports")
        settings=SettingsScreen(name="settings")
        for s in [home,units,charge,receipt,expense,reports,settings]: sm.add_widget(s)
        sm.db=self.db
        Clock.schedule_once(lambda dt: home.refresh(),.2)
        return sm

if __name__ == "__main__":
    BuildingManagerApp().run()
