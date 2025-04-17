import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os

SAVE_FILE = "grades_data.json"

class GradeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grade Tracker")
        self.courses = {}  # year -> {course_name -> {"target": float, "categories": {category: {"weight": x, "grades": []}}}}
        self.selected_year = None
        self.selected_course = None

        self.load_data()
        self.setup_ui()

    def setup_ui(self):
        self.root.geometry("900x500")

        self.sidebar = tk.Frame(self.root, bg="#f0f0f0", width=250)
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)

        self.year_label = tk.Label(self.sidebar, text="Year Categories")
        self.year_label.pack(pady=5)

        self.year_combobox = ttk.Combobox(self.sidebar, values=list(self.courses.keys()))
        self.year_combobox.pack(pady=5, padx=10, fill=tk.X)
        self.year_combobox.bind("<<ComboboxSelected>>", self.change_year)

        self.add_year_btn = tk.Button(self.sidebar, text="+ Add Year", command=self.add_year)
        self.add_year_btn.pack(pady=2, padx=10)

        self.course_listbox = tk.Listbox(self.sidebar)
        self.course_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.course_listbox.bind("<<ListboxSelect>>", self.change_course)

        self.add_course_btn = tk.Button(self.sidebar, text="+ Add Course", command=self.add_course)
        self.add_course_btn.pack(pady=2, padx=10)

        self.delete_course_btn = tk.Button(self.sidebar, text="🗑 Delete Course", command=self.delete_course)
        self.delete_course_btn.pack(pady=2, padx=10)

        self.main_area = tk.Frame(self.root, bg="white")
        self.main_area.pack(fill=tk.BOTH, expand=True)

        self.course_title = tk.Label(self.main_area, text="Select a course", font=("Helvetica", 16), bg="white")
        self.course_title.pack(pady=10)

        self.add_category_btn = tk.Button(self.main_area, text="+ Add Category", command=self.add_category)
        self.add_category_btn.pack(pady=5)

        self.category_frames = tk.Frame(self.main_area, bg="white")
        self.category_frames.pack(pady=10, fill=tk.BOTH, expand=True)

        self.refresh_year_dropdown()

    def refresh_year_dropdown(self):
        self.year_combobox['values'] = list(self.courses.keys())
        if self.selected_year:
            self.year_combobox.set(self.selected_year)
        self.refresh_course_list()

    def refresh_course_list(self):
        self.course_listbox.delete(0, tk.END)
        if self.selected_year and self.selected_year in self.courses:
            for course in self.courses[self.selected_year]:
                self.course_listbox.insert(tk.END, course)

    def refresh_course_display(self):
        for widget in self.category_frames.winfo_children():
            widget.destroy()

        if not self.selected_course or not self.selected_year:
            return

        course_data = self.courses[self.selected_year][self.selected_course]
        categories = course_data["categories"]
        target = course_data.get("target")

        total_weight = 0
        total_score = 0
        remaining_weight = 0

        for category, data in categories.items():
            cat_frame = tk.LabelFrame(self.category_frames, text=f"{category} ({data['weight']}%)", padx=10, pady=5)
            cat_frame.pack(fill=tk.X, padx=10, pady=5)

            grades_frame = tk.Frame(cat_frame)
            grades_frame.pack(fill=tk.X)

            for i, grade in enumerate(data['grades']):
                grade_label = tk.Label(grades_frame, text=str(grade))
                grade_label.grid(row=0, column=i*2, padx=2)
                del_btn = tk.Button(grades_frame, text="x", command=lambda c=category, idx=i: self.delete_grade(c, idx), fg="red")
                del_btn.grid(row=0, column=i*2+1, padx=1)

            button_frame = tk.Frame(cat_frame)
            button_frame.pack(anchor="e")

            tk.Button(button_frame, text="Add Grade", command=lambda c=category: self.add_grade(c)).pack(side=tk.LEFT)
            tk.Button(button_frame, text="Delete Category", command=lambda c=category: self.delete_category(c)).pack(side=tk.LEFT, padx=5)

            if data['grades']:
                avg = sum(data['grades']) / len(data['grades'])
                total_weight += data['weight']
                total_score += avg * (data['weight'] / 100)
            else:
                remaining_weight += data['weight']

        grade_summary = f"\nCurrent Grade: {total_score:.2f}%"
        if target is not None and remaining_weight > 0:
            needed = (target - total_score) / (remaining_weight / 100)
            grade_summary += f"\nTarget: {target:.2f}% → Need: {needed:.2f}%"

        self.course_title.config(text=f"{self.selected_course}{grade_summary}")

    def add_year(self):
        year = simpledialog.askstring("New Year", "Enter year (e.g., First Year, Second Year):")
        if year and year not in self.courses:
            self.courses[year] = {}
            self.selected_year = year
            self.refresh_year_dropdown()
            self.save_data()

    def add_course(self):
        if not self.selected_year:
            messagebox.showwarning("No Year Selected", "Please select a year first.")
            return
        name = simpledialog.askstring("New Course", "Enter course name:")
        if name and name not in self.courses[self.selected_year]:
            target = simpledialog.askfloat("Target Grade", f"Enter your target grade for {name} (%):")
            self.courses[self.selected_year][name] = {"target": target, "categories": {}}
            self.course_listbox.insert(tk.END, name)
            self.save_data()

    def delete_course(self):
        if not self.selected_year or not self.selected_course:
            return
        confirm = messagebox.askyesno("Delete Course", f"Are you sure you want to delete '{self.selected_course}'?")
        if confirm:
            del self.courses[self.selected_year][self.selected_course]
            self.selected_course = None
            self.refresh_course_list()
            self.save_data()
            self.course_title.config(text="Select a course")
            self.refresh_course_display()

    def delete_category(self, category):
        if not self.selected_course:
            return
        confirm = messagebox.askyesno("Delete Category", f"Delete category '{category}'?")
        if confirm:
            del self.courses[self.selected_year][self.selected_course]['categories'][category]
            self.save_data()
            self.refresh_course_display()

    def delete_grade(self, category, index):
        if not self.selected_course:
            return
        try:
            del self.courses[self.selected_year][self.selected_course]['categories'][category]['grades'][index]
            self.save_data()
            self.refresh_course_display()
        except IndexError:
            messagebox.showerror("Error", "Grade not found.")

    def change_year(self, event):
        self.selected_year = self.year_combobox.get()
        self.refresh_course_list()

    def change_course(self, event):
        selection = self.course_listbox.curselection()
        if selection:
            self.selected_course = self.course_listbox.get(selection[0])
            self.refresh_course_display()

    def add_category(self):
        if not self.selected_course:
            messagebox.showwarning("No Course Selected", "Please select a course first.")
            return

        name = simpledialog.askstring("New Category", "Enter category name:")
        weight = simpledialog.askfloat("Category Weight", "Enter category weight (%):")
        if name and weight is not None:
            existing_weight = sum(cat['weight'] for cat in self.courses[self.selected_year][self.selected_course]['categories'].values())
            if existing_weight + weight > 100:
                messagebox.showerror("Weight Limit Exceeded", "Total category weight cannot exceed 100%.")
                return
            self.courses[self.selected_year][self.selected_course]["categories"][name] = {"weight": weight, "grades": []}
            self.save_data()
            self.refresh_course_display()

    def add_grade(self, category):
        grade = simpledialog.askfloat("New Grade", f"Enter grade for {category}:")
        if grade is not None:
            self.courses[self.selected_year][self.selected_course]["categories"][category]['grades'].append(grade)
            self.save_data()
            self.refresh_course_display()

    def save_data(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump(self.courses, f, indent=2)

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                self.courses = json.load(f)

if __name__ == "__main__":
    root = tk.Tk()
    app = GradeTrackerApp(root)
    root.mainloop()
