import os
import sqlite3
import shutil
import csv
import urllib.parse
from datetime import datetime

from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.toolbar import MDTopAppBar

# --- المسارات وتجهيز البيئة ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "installments.db")
BACKUP_DIR = os.path.join(BASE_DIR, "Backups")

# --- إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_num TEXT, name TEXT, phone TEXT, item TEXT,
            original_price REAL DEFAULT 0, profit_rate REAL DEFAULT 0,
            total_price REAL DEFAULT 0, monthly_amount REAL,
            total_months INTEGER, paid_months INTEGER DEFAULT 0,
            extra_paid REAL DEFAULT 0, start_date TEXT, deferred_months INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER, type TEXT, amount REAL, created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, role TEXT DEFAULT 'مستخدم', created_at TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO users (name, role, created_at) VALUES ('خالد سعد الرحيلي', 'مدير النظام', ?)", (now_str,))
        conn.commit()
    conn.close()

def is_paid_this_month(customer_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute("SELECT COUNT(*) FROM payment_history WHERE customer_id = ? AND created_at LIKE ? AND type = 'MONTH'", (customer_id, f"{current_month}%"))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def get_late_customers_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, total_months, paid_months FROM customers")
    rows = cursor.fetchall()
    conn.close()
    late_count = 0
    for cid, total, paid in rows:
        if not (is_paid_this_month(cid) or (total and paid >= total)):
            late_count += 1
    return late_count

init_db()

# --- الشاشة الرئيسية ---
class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')
        
        # شريط العنوان العلوي
        self.toolbar = MDTopAppBar(
            title="أقساطي",
            left_action_items=[["account-switch", lambda x: MDApp.get_running_app().open_users_dialog()]],
            right_action_items=[["chart-bar", lambda x: MDApp.get_running_app().open_report_dialog()]]
        )
        layout.add_widget(self.toolbar)
        
        # الهيدر والترحيب
        header_box = MDBoxLayout(orientation='vertical', padding=15, spacing=5, size_hint_y=0.25)
        lbl_sub = MDLabel(
            text="(الحمدلله على جزيل عطائه ورزقه)",
            halign="center",
            theme_text_color="Secondary",
            font_style="Subtitle1"
        )
        self.lbl_user = MDLabel(
            text="مرحباً بك: خالد سعد الرحيلي",
            halign="center",
            font_style="H6",
            theme_text_color="Primary"
        )
        header_box.add_widget(lbl_sub)
        header_box.add_widget(self.lbl_user)
        layout.add_widget(header_box)

        # شبكة الخيارات الرئيسية (Grid Cards)
        grid = MDGridLayout(cols=2, padding=15, spacing=15)
        
        card_add = MDCard(ripple_behavior=True, on_release=lambda x: self.navigate('add_customer'))
        box_add = MDBoxLayout(orientation='vertical', padding=10)
        box_add.add_widget(MDIconButton(icon="account-plus", pos_hint={"center_x": 0.5}))
        box_add.add_widget(MDLabel(text="إضافة عميل", halign="center"))
        card_add.add_widget(box_add)

        card_list = MDCard(ripple_behavior=True, on_release=lambda x: self.navigate('customers_list', late_only=False))
        box_list = MDBoxLayout(orientation='vertical', padding=10)
        box_list.add_widget(MDIconButton(icon="account-group", pos_hint={"center_x": 0.5}))
        box_list.add_widget(MDLabel(text="قائمة العملاء", halign="center"))
        card_list.add_widget(box_list)

        card_late = MDCard(ripple_behavior=True, on_release=lambda x: self.navigate('customers_list', late_only=True))
        box_late = MDBoxLayout(orientation='vertical', padding=10)
        box_late.add_widget(MDIconButton(icon="clock-alert", theme_text_color="Error", pos_hint={"center_x": 0.5}))
        self.lbl_late = MDLabel(text=f"المتأخرين ({get_late_customers_count()})", halign="center", theme_text_color="Error")
        box_late.add_widget(self.lbl_late)
        card_late.add_widget(box_late)

        card_settings = MDCard(ripple_behavior=True, on_release=lambda x: self.navigate('settings'))
        box_settings = MDBoxLayout(orientation='vertical', padding=10)
        box_settings.add_widget(MDIconButton(icon="cog", pos_hint={"center_x": 0.5}))
        box_settings.add_widget(MDLabel(text="الإعدادات", halign="center"))
        card_settings.add_widget(box_settings)

        grid.add_widget(card_add)
        grid.add_widget(card_list)
        grid.add_widget(card_late)
        grid.add_widget(card_settings)

        layout.add_widget(grid)
        self.add_widget(layout)

    def on_pre_enter(self):
        self.lbl_late.text = f"المتأخرين ({get_late_customers_count()})"

    def navigate(self, screen_name, late_only=False):
        app = MDApp.get_running_app()
        if screen_name == 'customers_list':
            app.root.get_screen('customers_list').late_only = late_only
        app.root.current = screen_name

# --- شاشة إضافة عميل ---
class AddCustomerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')
        toolbar = MDTopAppBar(title="إضافة عميل جديد", left_action_items=[["arrow-left", lambda x: self.go_back()]])
        layout.add_widget(toolbar)

        scroll = MDScrollView()
        form = MDBoxLayout(orientation='vertical', padding=20, spacing=12, size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))

        self.txt_name = MDTextField(hint_text="اسم العميل *")
        self.txt_phone = MDTextField(hint_text="رقم الجوال")
        self.txt_item = MDTextField(hint_text="نوع السلعة")
        self.txt_voucher = MDTextField(hint_text="رقم السند")
        self.txt_orig_price = MDTextField(hint_text="السعر الأصلي (ريال)")
        self.txt_profit_rate = MDTextField(hint_text="نسبة الفائدة (%)")
        self.txt_months = MDTextField(hint_text="عدد الأشهر *")
        self.txt_start_date = MDTextField(hint_text="تاريخ البداية (YYYY-MM-DD)", text=datetime.now().strftime("%Y-%m-%d"))

        btn_save = MDRaisedButton(text="حفظ البيانات", pos_hint={"center_x": 0.5}, on_release=self.save_customer)

        for w in [self.txt_name, self.txt_phone, self.txt_item, self.txt_voucher, self.txt_orig_price, self.txt_profit_rate, self.txt_months, self.txt_start_date, btn_save]:
            form.add_widget(w)

        scroll.add_widget(form)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def go_back(self):
        MDApp.get_running_app().root.current = 'home'

    def save_customer(self, instance):
        if not self.txt_name.text.strip() or not self.txt_months.text.strip():
            return
        
        try:
            orig = float(self.txt_orig_price.text or 0)
            rate = float(self.txt_profit_rate.text or 0)
            tot = orig + (orig * (rate / 100.0))
            months = int(self.txt_months.text)
            monthly = tot / months if months > 0 else 0

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO customers (voucher_num, name, phone, item, original_price, profit_rate, total_price, monthly_amount, total_months, start_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.txt_voucher.text, self.txt_name.text, self.txt_phone.text, self.txt_item.text, orig, rate, tot, monthly, months, self.txt_start_date.text))
            conn.commit()
            conn.close()

            self.go_back()
        except Exception as e:
            print(f"Error saving customer: {e}")

# --- شاشة قائمة العملاء والمتأخرين ---
class CustomersListScreen(MDScreen):
    late_only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="قائمة العملاء", left_action_items=[["arrow-left", lambda x: self.go_back()]])
        self.layout.add_widget(self.toolbar)

        self.search_field = MDTextField(hint_text="ابحث باسم العميل أو الجوال...", padding=10)
        self.search_field.bind(text=self.filter_list)
        self.layout.add_widget(self.search_field)

        self.scroll = MDScrollView()
        self.list_view = MDList()
        self.scroll.add_widget(self.list_view)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)

    def go_back(self):
        MDApp.get_running_app().root.current = 'home'

    def on_pre_enter(self):
        self.toolbar.title = "العملاء المتأخرين" if self.late_only else "قائمة العملاء"
        self.load_customers()

    def filter_list(self, instance, text):
        self.load_customers(query=text)

    def load_customers(self, query=""):
        self.list_view.clear_widgets()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if query:
            cursor.execute("SELECT id, name, phone, monthly_amount, total_months, paid_months FROM customers WHERE name LIKE ?", (f"%{query}%",))
        else:
            cursor.execute("SELECT id, name, phone, monthly_amount, total_months, paid_months FROM customers")
        
        rows = cursor.fetchall()
        conn.close()

        for cid, name, phone, monthly, total, paid in rows:
            paid_month = is_paid_this_month(cid)
            all_paid = (total and paid >= total)

            if self.late_only and (paid_month or all_paid):
                continue

            icon = "check-circle" if (paid_month or all_paid) else "alert-circle"
            color = "green" if (paid_month or all_paid) else "red"

            item = TwoLineAvatarIconListItem(
                text=name,
                secondary_text=f"الجوال: {phone} | القسط: {monthly:,.0f} ريال",
                on_release=lambda x, c=cid: self.open_customer_details(c)
            )
            item.add_widget(IconLeftWidget(icon=icon, theme_text_color="Custom", text_color=color))
            
            # زر إشعار واتساب مباشر
            if not (paid_month or all_paid):
                btn_wa = IconRightWidget(icon="whatsapp", theme_text_color="Custom", text_color="green")
                btn_wa.bind(on_release=lambda x, p=phone, m=monthly, r=(total-paid): self.send_wa_notice(p, m, r))
                item.add_widget(btn_wa)

            self.list_view.add_widget(item)

    def send_wa_notice(self, phone, monthly, rem_months):
        target = phone.replace("+", "").replace(" ", "") if phone else ""
        msg = f"السلام عليكم ورحمة الله وبركاته\nتذكير بدفعة القسط المستحقة بقيمة {monthly:,.0f} ريال.\nالأشهر المتبقية: {rem_months}"
        url = f"https://wa.me/{target}?text={urllib.parse.quote(msg)}"
        import webbrowser
        webbrowser.open(url)

    def open_customer_details(self, customer_id):
        app = MDApp.get_running_app()
        app.selected_customer_id = customer_id
        app.root.current = 'customer_details'

# --- شاشة تفاصيل العميل ---
class CustomerDetailsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical')
        toolbar = MDTopAppBar(title="تفاصيل العميل", left_action_items=[["arrow-left", lambda x: self.go_back()]])
        self.layout.add_widget(toolbar)

        self.content_box = MDBoxLayout(orientation='vertical', padding=20, spacing=10)
        self.layout.add_widget(self.content_box)
        self.add_widget(self.layout)

    def go_back(self):
        MDApp.get_running_app().root.current = 'customers_list'

    def on_pre_enter(self):
        self.content_box.clear_widgets()
        cid = MDApp.get_running_app().selected_customer_id

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, phone, item, voucher_num, monthly_amount, total_months, paid_months FROM customers WHERE id = ?", (cid,))
        c = cursor.fetchone()
        conn.close()

        if not c:
            return

        name, phone, item, voucher, monthly, total, paid = c
        rem_months = max(0, total - paid)

        self.content_box.add_widget(MDLabel(text=f"الاسم: {name}", font_style="H6"))
        self.content_box.add_widget(MDLabel(text=f"رقم الجوال: {phone}"))
        self.content_box.add_widget(MDLabel(text=f"السلعة: {item} | رقم السند: {voucher}"))
        self.content_box.add_widget(MDLabel(text=f"القسط الشهري: {monthly:,.0f} ريال"))
        self.content_box.add_widget(MDLabel(text=f"الأشهر المدفوعة: {paid} من أصل {total}"))

        btn_pay = MDRaisedButton(text="🟢 تسديد قسط شهر", pos_hint={"center_x": 0.5}, on_release=lambda x: self.pay_installment(cid))
        self.content_box.add_widget(btn_pay)

    def pay_installment(self, cid):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE customers SET paid_months = paid_months + 1 WHERE id = ?", (cid,))
        cursor.execute("INSERT INTO payment_history (customer_id, type, amount, created_at) VALUES (?, 'MONTH', 1, ?)", (cid, now))
        conn.commit()
        conn.close()
        self.on_pre_enter()

# --- شاشة الإعدادات والنسخ الاحتياطي ---
class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')
        toolbar = MDTopAppBar(title="الإعدادات والنسخ الاحتياطي", left_action_items=[["arrow-left", lambda x: self.go_back()]])
        layout.add_widget(toolbar)

        box = MDBoxLayout(orientation='vertical', padding=20, spacing=15)
        
        btn_excel = MDRaisedButton(text="📊 تصدير البيانات إلى Excel (CSV)", pos_hint={"center_x": 0.5}, on_release=self.export_csv)
        btn_backup = MDRaisedButton(text="📦 إنشاء نسخة احتياطية محلياً", pos_hint={"center_x": 0.5}, on_release=self.make_backup)

        box.add_widget(btn_excel)
        box.add_widget(btn_backup)
        layout.add_widget(box)
        self.add_widget(layout)

    def go_back(self):
        MDApp.get_running_app().root.current = 'home'

    def export_csv(self, instance):
        try:
            export_path = os.path.join(BASE_DIR, "customers_export.csv")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers")
            rows = cursor.fetchall()
            conn.close()

            with open(export_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
        except Exception as e:
            print(f"Excel Export Error: {e}")

    def make_backup(self, instance):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(DB_PATH, os.path.join(BACKUP_DIR, f"backup_{timestamp}.db"))

# --- التطبيق الرئيسي ---
class AqsatyApp(MDApp):
    selected_customer_id = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Indigo"

        sm = MDScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(AddCustomerScreen(name='add_customer'))
        sm.add_widget(CustomersListScreen(name='customers_list'))
        sm.add_widget(CustomerDetailsScreen(name='customer_details'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

    def open_users_dialog(self):
        dialog = MDDialog(title="الحساب الحالي", text="عمي خالد (مدير النظام)", buttons=[MDFlatButton(text="إغلاق", on_release=lambda x: dialog.dismiss())])
        dialog.open()

    def open_report_dialog(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(total_price), SUM(monthly_amount) FROM customers")
        row = cursor.fetchone()
        conn.close()

        tot_val = row[0] or 0
        tot_m = row[1] or 0

        dialog = MDDialog(
            title="التقرير المالي السريع",
            text=f"إجمالي العقود: {tot_val:,.0f} ريال\nإجمالي الدخل الشهري المتوقع: {tot_m:,.0f} ريال",
            buttons=[MDFlatButton(text="حسناً", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

if __name__ == '__main__':
    AqsatyApp().run()
