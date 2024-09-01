import tkinter as tk
from tkinter import ttk, messagebox
from api_client import APIClient
from datetime import date
import logging

logger = logging.getLogger(__name__)

class App(tk.Tk):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.title("SavePlate 테스트 앱")
        self.geometry("400x300")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        self.login_frame = LoginFrame(self.notebook, self.api_client, self.on_login_success)
        self.register_frame = RegisterFrame(self.notebook, self.api_client, self.on_register_success)
        self.ingredients_frame = IngredientsFrame(self.notebook, self.api_client)
        self.recipes_frame = RecipesFrame(self.notebook, self.api_client)

        self.notebook.add(self.login_frame, text="로그인")
        self.notebook.add(self.register_frame, text="회원가입")

    def on_login_success(self):
        logger.info("로그인 성공")
        self.add_main_tabs()

    def on_register_success(self):
        logger.info("회원가입 성공")
        self.add_main_tabs()

    def add_main_tabs(self):
        self.notebook.add(self.ingredients_frame, text="재료")
        self.notebook.add(self.recipes_frame, text="레시피")
        self.notebook.select(2)  # 재료 탭으로 이동

class LoginFrame(ttk.Frame):
    def __init__(self, parent, api_client, on_success):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success = on_success

        ttk.Label(self, text="이메일:").grid(row=0, column=0, padx=5, pady=5)
        self.email_entry = ttk.Entry(self)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="비밀번호:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self, text="로그인", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        if self.api_client.login(email, password):
            messagebox.showinfo("성공", "로그인 성공!")
            self.on_success()
        else:
            messagebox.showerror("오류", "로그인 실패. 이메일과 비밀번호를 확인해주세요.")

class RegisterFrame(ttk.Frame):
    def __init__(self, parent, api_client, on_success):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success = on_success

        ttk.Label(self, text="이메일:").grid(row=0, column=0, padx=5, pady=5)
        self.email_entry = ttk.Entry(self)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="비밀번호:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self, text="이름:").grid(row=2, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self, text="성별:").grid(row=3, column=0, padx=5, pady=5)
        self.gender_var = tk.StringVar()
        self.gender_combobox = ttk.Combobox(self, textvariable=self.gender_var, values=["male", "female", "other"])
        self.gender_combobox.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(self, text="생년월일:").grid(row=4, column=0, padx=5, pady=5)
        self.birth_date_entry = ttk.Entry(self)
        self.birth_date_entry.grid(row=4, column=1, padx=5, pady=5)
        ttk.Label(self, text="(YYYY-MM-DD)").grid(row=4, column=2, padx=5, pady=5)

        ttk.Button(self, text="회원가입", command=self.register).grid(row=5, column=0, columnspan=2, pady=10)

    def register(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        name = self.name_entry.get()
        gender = self.gender_var.get()
        birth_date = self.birth_date_entry.get()

        if email and password and name and gender and birth_date:
            try:
                birth_date = date.fromisoformat(birth_date)
                if self.api_client.register(email, password, name, gender, str(birth_date)):
                    messagebox.showinfo("성공", "회원가입 성공!")
                    self.on_success()
                else:
                    messagebox.showerror("오류", "회원가입 실패. 입력 정보를 확인해주세요.")
            except ValueError:
                messagebox.showerror("오류", "생년월일 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
        else:
            messagebox.showerror("오류", "모든 필드를 입력해주세요.")

class IngredientsFrame(ttk.Frame):
    def __init__(self, parent, api_client):
        super().__init__(parent)
        self.api_client = api_client

        self.ingredients_list = tk.Listbox(self)
        self.ingredients_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Button(self, text="재료 새로고침", command=self.refresh_ingredients).pack(pady=5)

        ttk.Label(self, text="재료 이름:").pack()
        self.ingredient_name = ttk.Entry(self)
        self.ingredient_name.pack()

        ttk.Label(self, text="수량:").pack()
        self.ingredient_amount = ttk.Entry(self)
        self.ingredient_amount.pack()

        ttk.Button(self, text="재료 추가", command=self.add_ingredient).pack(pady=5)

    def refresh_ingredients(self):
        ingredients = self.api_client.get_ingredients()
        self.ingredients_list.delete(0, tk.END)
        for ingredient in ingredients:
            self.ingredients_list.insert(tk.END, f"{ingredient['name']}: {ingredient['amount']}")

    def add_ingredient(self):
        name = self.ingredient_name.get()
        amount = self.ingredient_amount.get()
        if name and amount:
            result = self.api_client.add_ingredient(name, int(amount))
            if result:
                messagebox.showinfo("성공", "재료가 추가되었습니다.")
                self.refresh_ingredients()
            else:
                messagebox.showerror("오류", "재료 추가에 실패했습니다.")
        else:
            messagebox.showerror("오류", "재료 이름과 수량을 입력해주세요.")

class RecipesFrame(ttk.Frame):
    def __init__(self, parent, api_client):
        super().__init__(parent)
        self.api_client = api_client

        self.recipes_list = tk.Listbox(self)
        self.recipes_list.pack(fill=tk.BOTH, expand=True)

        ttk.Button(self, text="가능한 레시피 조회", command=self.get_available_recipes).pack(pady=5)

    def get_available_recipes(self):
        recipes = self.api_client.get_available_recipes()
        self.recipes_list.delete(0, tk.END)
        for recipe in recipes:
            self.recipes_list.insert(tk.END, f"{recipe['food']} - {recipe['recipe']} (유사도: {recipe['sim']:.2f})")
