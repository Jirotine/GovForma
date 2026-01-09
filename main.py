import customtkinter as ctk
from tkinter import messagebox, ttk
import sqlite3
import random
import json
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- STYLING & CONSTANTS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
SIDEBAR_BG, MAIN_BG = "#1e293b", "#0f172a"
EMERALD, CRIMSON, ACCENT_BLUE, WARNING_AMBER, LABEL_GREY = "#10b981", "#ef4444", "#3b82f6", "#f59e0b", "#94a3b8"

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
BARANGAYS = sorted([f"Barangay I-{c}" for c in "ABC"] + [f"Barangay II-{c}" for c in "ABCDEF"] + [f"Barangay III-{c}" for c in "ABCDEF"] + [f"Barangay IV-{c}" for c in "ABC"] + [f"Barangay V-{c}" for c in "ABCD"] + [f"Barangay VI-{c}" for c in "ABCDE"] + [f"Barangay VII-{c}" for c in "ABCDE"] + ["Bagong Bayan II-A", "Bagong Pook VI-C"] + ["Atisan", "Bautista", "Concepcion", "Del Remedio", "Dolores", "San Antonio 1", "San Antonio 2", "San Bartolome", "San Buenaventura", "San Crispin", "San Cristobal", "San Diego", "San Francisco", "San Gabriel", "San Gregorio", "San Ignacio", "San Isidro", "San Joaquin", "San Jose", "San Juan", "San Lorenzo", "San Lucas 1", "San Lucas 2", "San Marcos", "San Mateo", "San Miguel", "San Nicolas", "San Pedro", "San Rafael", "San Roque", "San Vicente", "Santa Ana", "Santa Catalina", "Santa Cruz", "Santa Elena", "Santa Filomena", "Santa Isabel", "Santa Maria", "Santa Maria Magdalena", "Santa Monica", "Santa Veronica", "Santiago I", "Santiago II", "Santisimo Rosario", "Santo Angel", "Santo Cristo", "Santo Niño", "Soledad"])

class ScrollSelection(ctk.CTkToplevel):
    def __init__(self, master, title, values, callback):
        super().__init__(master)
        self.title(title); self.geometry("350x500"); self.callback = callback; self.values = values
        self.attributes("-topmost", True); self.focus_force()
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search...", height=40)
        self.search_entry.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_items)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Enable Mouse Wheel for this pop-up
        self.scroll_frame.bind_all("<MouseWheel>", self._on_mousewheel)
        self.render_items(self.values)

    def _on_mousewheel(self, event):
        self.scroll_frame._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def render_items(self, items):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for item in items:
            ctk.CTkButton(self.scroll_frame, text=item, fg_color="transparent", anchor="w", 
                          command=lambda x=item: self.select(x)).pack(fill="x")

    def filter_items(self, event):
        q = self.search_entry.get().lower()
        self.render_items([v for v in self.values if q in v.lower()])

    def select(self, val): 
        self.scroll_frame.unbind_all("<MouseWheel>") # Clean up binding
        self.callback(val); self.destroy()

class GovRegistryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OSCA San Pablo City - Senior Citizen Registry"); self.geometry("1350x980")
        self.configure(fg_color=MAIN_BG); self.init_db(); self.editing_psn = None; self.entries = {}
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="GovForma", font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0, padx=20, pady=40)
        self.btn_main = ctk.CTkButton(self.sidebar, text="Register Citizen", height=45, fg_color=EMERALD, command=self.save_record)
        self.btn_main.grid(row=1, column=0, padx=20, pady=10)
        self.btn_pdf = ctk.CTkButton(self.sidebar, text="Generate PDF Form", height=45, fg_color=ACCENT_BLUE, command=self.generate_pdf)
        self.btn_pdf.grid(row=2, column=0, padx=20, pady=10)
        ctk.CTkButton(self.sidebar, text="Clear Form", height=40, fg_color="transparent", border_width=1, command=self.clear_form).grid(row=3, column=0, padx=20, pady=10)
        self.sidebar.grid_rowconfigure(4, weight=1)
        ctk.CTkButton(self.sidebar, text="Delete Record", height=40, fg_color=CRIMSON, command=self.delete_record).grid(row=5, column=0, padx=20, pady=30)

        # --- MAIN CONTENT ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=6); self.content_frame.grid_rowconfigure(1, weight=1) 

        self.form_scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="#1e293b", border_width=1, border_color="#334155")
        self.form_scroll.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.form_scroll.grid_columnconfigure((0, 1, 2), weight=1)

        # Enable Mouse Wheel for Main Form
        self.form_scroll.bind_all("<MouseWheel>", self._on_mousewheel)

        self.create_personal_info()
        self.create_family_section()
        self.create_membership_section()
        
        self.table_frame = ctk.CTkFrame(self.content_frame, fg_color="#1e293b", border_width=1, border_color="#334155")
        self.table_frame.grid(row=1, column=0, sticky="nsew")
        self.setup_table()

    def _on_mousewheel(self, event):
        self.form_scroll._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_personal_info(self):
        ctk.CTkLabel(self.form_scroll, text="PERSONAL INFORMATION", font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, columnspan=3, pady=(10, 20), sticky="w", padx=15)
        self.create_input("Surname*", 1, 0); self.create_input("First Name*", 1, 1); self.create_input("Middle Name", 1, 2)
        self.create_input("House No.*", 2, 0); self.create_input("Street*", 2, 1); self.create_scroll_selector("Barangay*", 2, 2, BARANGAYS)
        self.setup_dob_section(3, 0); self.create_input("Place of Birth*", 3, 1, span=2)
        self.create_dropdown("Sex", 4, 0, ["Male", "Female"]); self.create_dropdown("Civil Status", 4, 1, ["Single", "Married", "Widowed", "Separated"]); self.create_input("Tel/Cp No.", 4, 2)
        self.create_input("Citizenship*", 5, 0); self.create_input("Religion", 5, 1); self.create_input("Educational Attainment", 5, 2)

    def create_family_section(self):
        ctk.CTkLabel(self.form_scroll, text="FAMILY COMPOSITION", font=ctk.CTkFont(weight="bold", size=14)).grid(row=12, column=0, sticky="w", padx=15, pady=(30, 10))
        btn_f = ctk.CTkFrame(self.form_scroll, fg_color="transparent"); btn_f.grid(row=12, column=2, sticky="e", padx=15)
        ctk.CTkButton(btn_f, text="+", width=30, height=25, fg_color=EMERALD, command=self.add_family_row).pack(side="right", padx=2)
        ctk.CTkButton(btn_f, text="-", width=30, height=25, fg_color=CRIMSON, command=self.remove_family_row).pack(side="right", padx=2)
        self.family_frame = ctk.CTkFrame(self.form_scroll, fg_color="#2d3748")
        self.family_frame.grid(row=13, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        self.family_rows = []; self.add_family_row()

    def create_membership_section(self):
        ctk.CTkLabel(self.form_scroll, text="MEMBERSHIP", font=ctk.CTkFont(weight="bold", size=14)).grid(row=14, column=0, sticky="w", padx=15, pady=(30, 10))
        btn_m = ctk.CTkFrame(self.form_scroll, fg_color="transparent"); btn_m.grid(row=14, column=2, sticky="e", padx=15)
        ctk.CTkButton(btn_m, text="+", width=30, height=25, fg_color=EMERALD, command=self.add_membership_row).pack(side="right", padx=2)
        ctk.CTkButton(btn_m, text="-", width=30, height=25, fg_color=CRIMSON, command=self.remove_membership_row).pack(side="right", padx=2)
        self.membership_frame = ctk.CTkFrame(self.form_scroll, fg_color="#2d3748")
        self.membership_frame.grid(row=15, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        self.membership_rows = []; self.add_membership_row()

    def generate_pdf(self):
        surname = self.entries["Surname*"].get()
        if not surname:
            messagebox.showwarning("Warning", "Select a record first."); return
        
        fname = f"OSCA_Form_{surname}.pdf"
        try:
            c = canvas.Canvas(fname, pagesize=LETTER); w, h = LETTER
            
            c.setFont("Helvetica", 10)
            c.drawCentredString(w/2, h - 0.4*inch, "Republic of the Philippines")
            c.drawCentredString(w/2, h - 0.55*inch, "Office of the Mayor")
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(w/2, h - 0.75*inch, "OFFICE FOR SENIOR CITIZENS AFFAIRS (OSCA)")
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(w/2, h - 1.1*inch, "REGISTRATION FORM")
            
            box_size = 1.0 * inch
            box_x = w - 1.5 * inch
            box_y = h - 0.3 * inch
            c.rect(box_x, box_y - box_size, box_size, box_size) 
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(box_x + (box_size/2), box_y - box_size - 0.15*inch, "Signature/Thumbmark")

            y_box = h - 1.7*inch
            c.setLineWidth(1)
            c.rect(0.5*inch, y_box - 2.8*inch, 7.5*inch, 2.8*inch) 

            line_offsets = [0.5, 1.0, 1.5, 1.9, 2.3]
            for off in line_offsets:
                c.line(0.5*inch, y_box - off*inch, 8.0*inch, y_box - off*inch)

            c.setFont("Helvetica", 8); c.drawString(0.6*inch, y_box - 0.15*inch, "Name:")
            c.setFont("Helvetica-Bold", 10); c.drawString(1.2*inch, y_box - 0.35*inch, surname)
            c.drawString(3.5*inch, y_box - 0.35*inch, self.entries['First Name*'].get())
            c.drawString(6.5*inch, y_box - 0.35*inch, self.entries['Middle Name'].get())
            c.setFont("Helvetica", 6)
            c.drawString(1.2*inch, y_box - 0.45*inch, "Surname (Apelyido sa Asawa kung babae)")
            c.drawString(3.5*inch, y_box - 0.45*inch, "First Name (Pangalan)")
            c.drawString(6.5*inch, y_box - 0.45*inch, "Middle Name")

            y2 = y_box - 0.5*inch
            c.line(5.4*inch, y2, 5.4*inch, y2 - 0.5*inch)
            c.setFont("Helvetica", 8); c.drawString(0.6*inch, y2 - 0.15*inch, "Address:")
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.2*inch, y2 - 0.35*inch, f"{self.entries['House No.*'].get()} {self.entries['Street*'].get()}")
            c.drawString(5.5*inch, y2 - 0.35*inch, self.entries['Barangay*'].get())
            c.setFont("Helvetica", 6); c.drawString(1.2*inch, y2 - 0.45*inch, "House No. / Street"); c.drawString(5.5*inch, y2 - 0.45*inch, "Barangay")

            y3 = y_box - 1.0*inch
            c.line(5.4*inch, y3, 5.4*inch, y3 - 0.5*inch)
            c.setFont("Helvetica", 8); c.drawString(0.6*inch, y3 - 0.15*inch, "Date of Birth:"); c.drawString(5.5*inch, y3 - 0.15*inch, "Place of Birth:")
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.2*inch, y3 - 0.35*inch, f"{self.dob_m.get()} {self.dob_d.get()}, {self.dob_y.get()}")
            c.drawString(5.5*inch, y3 - 0.35*inch, self.entries['Place of Birth*'].get())

            y4 = y_box - 1.5*inch
            c.line(3.1*inch, y4, 3.1*inch, y4 - 0.4*inch); c.line(5.4*inch, y4, 5.4*inch, y4 - 0.4*inch)
            c.setFont("Helvetica", 8); c.drawString(0.6*inch, y4 - 0.15*inch, "Age:"); c.drawString(3.2*inch, y4 - 0.15*inch, "Sex:"); c.drawString(5.5*inch, y4 - 0.15*inch, "Tel/Cp No:")
            c.setFont("Helvetica-Bold", 9); c.drawString(3.2*inch, y4 - 0.32*inch, self.entries['Sex'].get()); c.drawString(5.5*inch, y4 - 0.32*inch, self.entries['Tel/Cp No.'].get())

            y5 = y_box - 1.9*inch
            c.line(3.1*inch, y5, 3.1*inch, y5 - 0.4*inch); c.line(6.1*inch, y5, 6.1*inch, y5 - 0.4*inch)
            c.setFont("Helvetica", 8); c.drawString(0.6*inch, y5 - 0.15*inch, "Citizenship:"); c.drawString(3.2*inch, y5 - 0.15*inch, "Civil Status:"); c.drawString(6.2*inch, y5 - 0.15*inch, "Religion:")
            c.setFont("Helvetica-Bold", 9); c.drawString(1.2*inch, y5 - 0.32*inch, self.entries['Citizenship*'].get()); c.drawString(3.2*inch, y5 - 0.32*inch, self.entries['Civil Status'].get()); c.drawString(6.2*inch, y5 - 0.32*inch, self.entries['Religion'].get())

            y6 = y_box - 2.3*inch
            c.setFont("Helvetica", 8); c.drawString(0.6*inch, y6 - 0.15*inch, "Educational Attainment (Pinagaralan):")
            c.setFont("Helvetica-Bold", 9); c.drawString(1.2*inch, y6 - 0.35*inch, self.entries['Educational Attainment'].get())

            y_fam = y_box - 3.1*inch
            c.setFont("Helvetica-Bold", 10); c.drawCentredString(w/2, y_fam, "FAMILY COMPOSITION")
            c.setFont("Helvetica", 7); c.drawCentredString(w/2, y_fam - 0.12*inch, "(Kasama sa Bahay)")
            
            ty = y_fam - 0.3*inch
            c.rect(0.5*inch, ty - 1.2*inch, 7.5*inch, 1.2*inch)
            c.line(0.5*inch, ty - 0.3*inch, 8.0*inch, ty - 0.3*inch) 
            cols = [0.5, 2.2, 4.0, 4.8, 5.8, 7.0, 8.0]
            for col in cols: c.line(col*inch, ty, col*inch, ty - 1.2*inch)
            
            c.setFont("Helvetica-Bold", 8)
            h_names = ["Name", "Relationship", "Age", "Status", "Occupation", "Income"]
            h_pos = [1.35, 3.1, 4.4, 5.3, 6.4, 7.5]
            for name, pos in zip(h_names, h_pos): c.drawCentredString(pos*inch, ty - 0.2*inch, name)

            c.setFont("Helvetica", 8); cy = ty - 0.5*inch
            for row in self.family_rows:
                if row[0].get():
                    c.drawString(0.6*inch, cy, row[0].get()[:28]); c.drawString(2.3*inch, cy, row[1].get()[:18])
                    c.drawCentredString(4.4*inch, cy, row[2].get()); c.drawCentredString(6.4*inch, cy, row[3].get()[:14])
                    cy -= 0.2*inch

            y_mem = ty - 1.5*inch
            c.setFont("Helvetica-Bold", 9); c.drawString(0.5*inch, y_mem, "MEMBERSHIP IN ANY SENIOR CITIZEN'S ASSOCIATION")
            m_ty = y_mem - 0.15*inch
            c.rect(0.5*inch, m_ty - 0.4*inch, 7.5*inch, 0.4*inch)
            c.line(0.5*inch, m_ty - 0.2*inch, 8.0*inch, m_ty - 0.2*inch)
            c.line(3.5*inch, m_ty, 3.5*inch, m_ty - 0.4*inch); c.line(6.0*inch, m_ty, 6.0*inch, m_ty - 0.4*inch)
            
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(2.0*inch, m_ty - 0.15*inch, "Name of Association")
            c.drawCentredString(4.75*inch, m_ty - 0.15*inch, "Address of Association")
            c.drawCentredString(7.0*inch, m_ty - 0.15*inch, "Date of Membership")

            c.setFont("Helvetica", 8); mcy = m_ty - 0.35*inch
            if self.membership_rows and self.membership_rows[0][0].get():
                m = self.membership_rows[0]
                c.drawString(0.6*inch, mcy, m[0].get()[:45])
                c.drawString(3.6*inch, mcy, m[1].get()[:35])
                c.drawString(6.1*inch, mcy, m[2].get())

            c.line(5.0*inch, 1.4*inch, 8.0*inch, 1.4*inch)
            c.setFont("Helvetica-Bold", 9); c.drawCentredString(6.5*inch, 1.25*inch, "Signature (PIRMA) or Thumbmark of")
            c.drawCentredString(6.5*inch, 1.1*inch, "Senior Citizen Applicant")

            c.save()
            if os.name == 'nt': os.startfile(fname)
            else: os.system(f'xdg-open "{fname}"')
        except Exception as e: messagebox.showerror("PDF Error", str(e))

    # --- SYSTEM LOGIC ---
    def add_family_row(self, data=None):
        r_idx = len(self.family_rows) + 1
        widgets = []
        placeholders = ["Full Name", "Relationship", "Age", "Occupation"]
        for i in range(4):
            e = ctk.CTkEntry(self.family_frame, height=28, placeholder_text=placeholders[i]); e.grid(row=r_idx, column=i, padx=5, pady=2, sticky="ew")
            if data: e.insert(0, data[i])
            widgets.append(e)
        self.family_rows.append(widgets)

    def remove_family_row(self):
        if len(self.family_rows) > 1:
            for w in self.family_rows.pop(): w.destroy()

    def add_membership_row(self, data=None):
        r_idx = len(self.membership_rows) + 1
        widgets = []
        placeholders = ["Name of Association", "Address of Association", "Date of Membership"]
        for i in range(3):
            e = ctk.CTkEntry(self.membership_frame, height=28, placeholder_text=placeholders[i]); e.grid(row=r_idx, column=i, padx=5, pady=2, sticky="ew")
            if data: e.insert(0, data[i])
            widgets.append(e)
        self.membership_rows.append(widgets)

    def remove_membership_row(self):
        if len(self.membership_rows) > 1:
            for w in self.membership_rows.pop(): w.destroy()

    def init_db(self):
        conn = sqlite3.connect("registry.db"); conn.execute("CREATE TABLE IF NOT EXISTS citizens (PSN TEXT PRIMARY KEY, Surname TEXT, Firstname TEXT, Middlename TEXT, HouseNo TEXT, Street TEXT, Barangay TEXT, DOB TEXT, POB TEXT, Sex TEXT, CivilStatus TEXT, Contact TEXT, Citizenship TEXT, Religion TEXT, Education TEXT, FamilyJSON TEXT, MemberJSON TEXT)"); conn.commit(); conn.close()

    def setup_table(self):
        self.search_bar = ctk.CTkEntry(self.table_frame, placeholder_text="Search Surname...", height=28); self.search_bar.pack(fill="x", padx=10, pady=5)
        self.search_bar.bind("<KeyRelease>", lambda e: self.refresh_table())
        self.tree = ttk.Treeview(self.table_frame, columns=("ID", "Last", "First", "Brgy"), show="headings", height=5)
        for c in ("ID", "Last", "First", "Brgy"): self.tree.heading(c, text=c); self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10); self.tree.bind("<Double-1>", self.load_for_edit); self.refresh_table()

    def save_record(self):
        # Citizenship added to required list
        req = ["Surname*", "First Name*", "Citizenship*"]
        if any(not self.entries[f].get() or self.entries[f].get() == "Select..." for f in req):
            messagebox.showerror("Error", "Missing required fields (Name or Citizenship)!"); return
            
        if not self.dob_d.get() or not self.dob_y.get():
            messagebox.showerror("Error", "Date of Birth (Day and Year) is required!"); return

        f_data = json.dumps([[e.get() for e in row] for row in self.family_rows])
        m_data = json.dumps([[e.get() for e in row] for row in self.membership_rows])
        vals = (self.entries["Surname*"].get(), self.entries["First Name*"].get(), self.entries["Middle Name"].get(), self.entries["House No.*"].get(), self.entries["Street*"].get(), self.entries["Barangay*"].get(), f"{self.dob_m.get()} {self.dob_d.get()}, {self.dob_y.get()}", self.entries["Place of Birth*"].get(), self.entries["Sex"].get(), self.entries["Civil Status"].get(), self.entries["Tel/Cp No."].get(), self.entries["Citizenship*"].get(), self.entries["Religion"].get(), self.entries["Educational Attainment"].get(), f_data, m_data)
        conn = sqlite3.connect("registry.db")
        if self.editing_psn: conn.execute("UPDATE citizens SET Surname=?, Firstname=?, Middlename=?, HouseNo=?, Street=?, Barangay=?, DOB=?, POB=?, Sex=?, CivilStatus=?, Contact=?, Citizenship=?, Religion=?, Education=?, FamilyJSON=?, MemberJSON=? WHERE PSN=?", vals + (self.editing_psn,))
        else: conn.execute("INSERT INTO citizens VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (f"SR-{random.randint(1000, 9999)}",) + vals)
        conn.commit(); conn.close(); self.refresh_table(); self.clear_form(); messagebox.showinfo("Success", "Record Saved.")

    def load_for_edit(self, event):
        sel = self.tree.focus()
        if not sel: return
        psn = self.tree.item(sel)['values'][0]
        conn = sqlite3.connect("registry.db"); r = conn.execute("SELECT * FROM citizens WHERE PSN=?", (psn,)).fetchone(); conn.close()
        if r:
            self.clear_form(); self.editing_psn = r[0]
            fields = ["Surname*", "First Name*", "Middle Name", "House No.*", "Street*"]
            for i, f in enumerate(fields): self.entries[f].insert(0, r[i+1])
            
            # Barangay and Place of Birth
            self.entries["Barangay*"].set(r[6])
            
            # --- FIX FOR BIRTH DATE FETCHING ---
            dob_raw = r[7] # Example: "January 01, 1960"
            try:
                # Remove comma and split by space
                parts = dob_raw.replace(',', '').split(' ')
                if len(parts) == 3:
                    self.dob_m.set(parts[0])      # Month
                    self.dob_d.insert(0, parts[1]) # Day
                    self.dob_y.insert(0, parts[2]) # Year
            except Exception: pass # Silence errors if date format is unexpected

            self.entries["Place of Birth*"].insert(0, r[8]); self.entries["Sex"].set(r[9]); self.entries["Civil Status"].set(r[10]); self.entries["Tel/Cp No."].insert(0, r[11]); self.entries["Citizenship*"].insert(0, r[12]); self.entries["Religion"].insert(0, r[13]); self.entries["Educational Attainment"].insert(0, r[14])
            
            # Re-render dynamic rows
            for row in self.family_rows: [w.destroy() for w in row]
            self.family_rows = []; [self.add_family_row(d) for d in json.loads(r[15])]
            for row in self.membership_rows: [w.destroy() for w in row]
            self.membership_rows = []; [self.add_membership_row(d) for d in json.loads(r[16])]
            
            self.btn_main.configure(text="Update Record", fg_color=WARNING_AMBER)

    def refresh_table(self):
        [self.tree.delete(i) for i in self.tree.get_children()]
        conn = sqlite3.connect("registry.db"); cur = conn.execute("SELECT PSN, Surname, Firstname, Barangay FROM citizens WHERE Surname LIKE ?", (f"{self.search_bar.get()}%",))
        for r in cur: self.tree.insert("", "end", values=r)
        conn.close()

    def clear_form(self):
        self.editing_psn = None; self.btn_main.configure(text="Register Citizen", fg_color=EMERALD)
        for v in self.entries.values(): 
            if hasattr(v, 'delete'): v.delete(0, 'end')
            elif hasattr(v, 'set'): v.set("Select...")
        
        self.dob_d.delete(0, 'end'); self.dob_y.delete(0, 'end'); self.dob_m.set("January")
        for row in self.family_rows: [w.destroy() for w in row]
        self.family_rows = []; self.add_family_row()
        for row in self.membership_rows: [w.destroy() for w in row]
        self.membership_rows = []; self.add_membership_row()

    def delete_record(self):
        sel = self.tree.selection()
        if sel:
            psn = self.tree.item(sel[0])['values'][0]
            if messagebox.askyesno("Delete", "Are you sure?"):
                conn = sqlite3.connect("registry.db"); conn.execute("DELETE FROM citizens WHERE PSN=?", (psn,)); conn.commit(); conn.close(); self.refresh_table(); self.clear_form()

    def create_input(self, label, r, c, span=1):
        ctk.CTkLabel(self.form_scroll, text=label, text_color=LABEL_GREY).grid(row=r*2, column=c, sticky="w", padx=15)
        e = ctk.CTkEntry(self.form_scroll, height=35, fg_color=MAIN_BG); e.grid(row=r*2+1, column=c, columnspan=span, sticky="we", padx=15, pady=(0, 10)); self.entries[label] = e

    def create_dropdown(self, label, r, c, vals):
        ctk.CTkLabel(self.form_scroll, text=label, text_color=LABEL_GREY).grid(row=r*2, column=c, sticky="w", padx=15)
        v = ctk.StringVar(value=vals[0]); ctk.CTkOptionMenu(self.form_scroll, values=vals, variable=v).grid(row=r*2+1, column=c, sticky="we", padx=15, pady=(0, 10)); self.entries[label] = v

    def create_scroll_selector(self, label, r, c, vals):
        ctk.CTkLabel(self.form_scroll, text=label, text_color=LABEL_GREY).grid(row=r*2, column=c, sticky="w", padx=15)
        v = ctk.StringVar(value="Select..."); btn = ctk.CTkButton(self.form_scroll, textvariable=v, fg_color=MAIN_BG, anchor="w", command=lambda: ScrollSelection(self, label, vals, v.set))
        btn.grid(row=r*2+1, column=c, sticky="we", padx=15, pady=(0, 10)); self.entries[label] = v

    def setup_dob_section(self, r, c):
        ctk.CTkLabel(self.form_scroll, text="Date of Birth*", text_color=LABEL_GREY).grid(row=r*2, column=c, sticky="w", padx=15)
        f = ctk.CTkFrame(self.form_scroll, fg_color="transparent"); f.grid(row=r*2+1, column=c, sticky="we", padx=15)
        self.dob_m = ctk.StringVar(value="January"); ctk.CTkButton(f, textvariable=self.dob_m, width=90, command=lambda: ScrollSelection(self, "Month", MONTHS, self.dob_m.set)).pack(side="left")
        self.dob_d = ctk.CTkEntry(f, width=40, placeholder_text="DD"); self.dob_d.pack(side="left", padx=2)
        self.dob_y = ctk.CTkEntry(f, width=60, placeholder_text="YYYY"); self.dob_y.pack(side="left", padx=2)

if __name__ == "__main__":
    app = GovRegistryApp(); app.mainloop()
