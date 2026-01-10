import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import random
import json
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- CONSTANTS ---
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
BARANGAYS = sorted(["Atisan", "Bautista", "Concepcion", "Del Remedio", "San Jose", "San Juan", "Santa Cruz", "San Pablo City"]) 
OUTPUT_FOLDER = "OSCA FORMS"

# Create the folder if it doesn't exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- GLOBAL STATE ---
entries = {}
family_rows = []
membership_rows = []
editing_psn = None

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect("registry.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS citizens (
                    PSN TEXT PRIMARY KEY, Surname TEXT, Firstname TEXT, Middlename TEXT, 
                    HouseNo TEXT, Street TEXT, Barangay TEXT, DOB TEXT, POB TEXT, 
                    Sex TEXT, CivilStatus TEXT, Contact TEXT, Citizenship TEXT, 
                    Religion TEXT, Education TEXT, FamilyJSON TEXT, MemberJSON TEXT)""")
    conn.commit()
    conn.close()

# --- PDF GENERATION ---
def generate_pdf():
    surname = entries["Surname*"].get()
    if not surname:
        messagebox.showwarning("Warning", "Please select or enter a record first.")
        return
        
    filename = f"OSCA_Form_{surname}.pdf"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    try:
        c = canvas.Canvas(filepath, pagesize=LETTER)
        w, h = LETTER
        
        # Header Section
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h - 0.4*inch, "Republic of the Philippines")
        c.drawCentredString(w/2, h - 0.55*inch, "Office of the Mayor")
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w/2, h - 0.75*inch, "OFFICE FOR SENIOR CITIZENS AFFAIRS (OSCA)")
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(w/2, h - 1.1*inch, "REGISTRATION FORM")
        
        # Photo/Sign Box
        box_size = 1.0 * inch
        box_x = w - 1.5 * inch
        box_y = h - 0.3 * inch
        c.rect(box_x, box_y - box_size, box_size, box_size) 
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(box_x + (box_size/2), box_y - box_size - 0.15*inch, "Signature/Thumbmark")

        # Information Box
        y_box = h - 1.7*inch
        c.setLineWidth(1)
        c.rect(0.5*inch, y_box - 2.8*inch, 7.5*inch, 2.8*inch) 

        line_offsets = [0.5, 1.0, 1.5, 1.9, 2.3]
        for off in line_offsets:
            c.line(0.5*inch, y_box - off*inch, 8.0*inch, y_box - off*inch)

        # Row 1: Name
        c.setFont("Helvetica", 8); c.drawString(0.6*inch, y_box - 0.15*inch, "Name:")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.2*inch, y_box - 0.35*inch, entries["Surname*"].get())
        c.drawString(3.5*inch, y_box - 0.35*inch, entries['First Name*'].get())
        c.drawString(6.5*inch, y_box - 0.35*inch, entries['Middle Name'].get())
        c.setFont("Helvetica", 6)
        c.drawString(1.2*inch, y_box - 0.45*inch, "Surname (Apelyido)")
        c.drawString(3.5*inch, y_box - 0.45*inch, "First Name (Pangalan)")
        c.drawString(6.5*inch, y_box - 0.45*inch, "Middle Name")

        # Row 2: Address
        y2 = y_box - 0.5*inch
        c.line(5.4*inch, y2, 5.4*inch, y2 - 0.5*inch)
        c.setFont("Helvetica", 8); c.drawString(0.6*inch, y2 - 0.15*inch, "Address:")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.2*inch, y2 - 0.35*inch, f"{entries['House No.*'].get()} {entries['Street*'].get()}")
        c.drawString(5.5*inch, y2 - 0.35*inch, entries['Barangay*'].get())
        c.setFont("Helvetica", 6); c.drawString(1.2*inch, y2 - 0.45*inch, "House No. / Street"); c.drawString(5.5*inch, y2 - 0.45*inch, "Barangay")

        # Row 3: DOB / POB
        y3 = y_box - 1.0*inch
        c.line(5.4*inch, y3, 5.4*inch, y3 - 0.5*inch)
        c.setFont("Helvetica", 8); c.drawString(0.6*inch, y3 - 0.15*inch, "Date of Birth:"); c.drawString(5.5*inch, y3 - 0.15*inch, "Place of Birth:")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.2*inch, y3 - 0.35*inch, f"{dob_m.get()} {dob_d.get()}, {dob_y.get()}")
        c.drawString(5.5*inch, y3 - 0.35*inch, entries['Place of Birth*'].get())

        # Row 4: Sex / Contact
        y4 = y_box - 1.5*inch
        c.line(3.1*inch, y4, 3.1*inch, y4 - 0.4*inch); c.line(5.4*inch, y4, 5.4*inch, y4 - 0.4*inch)
        c.setFont("Helvetica", 8); c.drawString(3.2*inch, y4 - 0.15*inch, "Sex:"); c.drawString(5.5*inch, y4 - 0.15*inch, "Tel/Cp No:")
        c.setFont("Helvetica-Bold", 9); c.drawString(3.2*inch, y4 - 0.32*inch, entries['Sex'].get()); c.drawString(5.5*inch, y4 - 0.32*inch, entries['Tel/Cp No.'].get())

        # Row 5: Citizenship / Status / Religion
        y5 = y_box - 1.9*inch
        c.line(3.1*inch, y5, 3.1*inch, y5 - 0.4*inch); c.line(6.1*inch, y5, 6.1*inch, y5 - 0.4*inch)
        c.setFont("Helvetica", 8); c.drawString(0.6*inch, y5 - 0.15*inch, "Citizenship:"); c.drawString(3.2*inch, y5 - 0.15*inch, "Civil Status:"); c.drawString(6.2*inch, y5 - 0.15*inch, "Religion:")
        c.setFont("Helvetica-Bold", 9); c.drawString(1.2*inch, y5 - 0.32*inch, entries['Citizenship*'].get()); c.drawString(3.2*inch, y5 - 0.32*inch, entries['Civil Status'].get()); c.drawString(6.2*inch, y5 - 0.32*inch, entries['Religion'].get())

        # Row 6: Education
        y6 = y_box - 2.3*inch
        c.setFont("Helvetica", 8); c.drawString(0.6*inch, y6 - 0.15*inch, "Educational Attainment:")
        c.setFont("Helvetica-Bold", 9); c.drawString(1.2*inch, y6 - 0.35*inch, entries['Educational Attainment'].get())

        # Family Table
        y_fam = y_box - 3.1*inch
        c.setFont("Helvetica-Bold", 10); c.drawCentredString(w/2, y_fam, "FAMILY COMPOSITION")
        ty = y_fam - 0.3*inch
        c.rect(0.5*inch, ty - 1.2*inch, 7.5*inch, 1.2*inch)
        c.line(0.5*inch, ty - 0.3*inch, 8.0*inch, ty - 0.3*inch) 
        cols = [0.5, 2.2, 4.0, 4.8, 5.8, 7.0, 8.0]
        for col in cols: c.line(col*inch, ty, col*inch, ty - 1.2*inch)
        
        c.setFont("Helvetica-Bold", 8)
        h_names = ["Name", "Relationship", "Age", "Occupation"]
        h_pos = [1.35, 3.1, 4.4, 6.4]
        for name, pos in zip(h_names, h_pos): c.drawCentredString(pos*inch, ty - 0.2*inch, name)

        c.setFont("Helvetica", 8); cy = ty - 0.5*inch
        for row in family_rows:
            widgets = row["widgets"]
            if widgets[0].get():
                c.drawString(0.6*inch, cy, widgets[0].get()[:28])
                c.drawString(2.3*inch, cy, widgets[1].get()[:18])
                c.drawCentredString(4.4*inch, cy, widgets[2].get())
                c.drawString(5.9*inch, cy, widgets[3].get()[:20])
                cy -= 0.2*inch

        # Membership Table (Centered Heading)
        y_mem = ty - 1.5*inch
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(w/2, y_mem, "MEMBERSHIP IN ANY SENIOR CITIZEN'S ASSOCIATION")
        
        m_ty = y_mem - 0.15*inch
        c.rect(0.5*inch, m_ty - 0.4*inch, 7.5*inch, 0.4*inch)
        c.line(0.5*inch, m_ty - 0.2*inch, 8.0*inch, m_ty - 0.2*inch)
        c.line(3.5*inch, m_ty, 3.5*inch, m_ty - 0.4*inch); c.line(6.0*inch, m_ty, 6.0*inch, m_ty - 0.4*inch)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(2.0*inch, m_ty - 0.15*inch, "Name of Association")
        c.drawCentredString(4.75*inch, m_ty - 0.15*inch, "Address of Association")
        c.drawCentredString(7.0*inch, m_ty - 0.15*inch, "Date of Membership")

        c.setFont("Helvetica", 8); mcy = m_ty - 0.35*inch
        for m_row in membership_rows:
            m_widgets = m_row["widgets"]
            if m_widgets[0].get():
                c.drawString(0.6*inch, mcy, m_widgets[0].get()[:45])
                c.drawString(3.6*inch, mcy, m_widgets[1].get()[:35])
                c.drawString(6.1*inch, mcy, m_widgets[2].get())
                mcy -= 0.2*inch

        # Footer Signatures
        c.line(5.0*inch, 1.4*inch, 8.0*inch, 1.4*inch)
        c.setFont("Helvetica-Bold", 9); c.drawCentredString(6.5*inch, 1.25*inch, "Signature / Thumbmark of Applicant")

        c.save()
        if os.name == 'nt': os.startfile(filepath)
        else: os.system(f'xdg-open "{filepath}"')
        messagebox.showinfo("Success", f"PDF saved to {OUTPUT_FOLDER}")
    except Exception as e: messagebox.showerror("PDF Error", f"Error: {str(e)}")

# --- BACKEND FUNCTIONS ---
def save_record():
    global editing_psn
    surname = entries["Surname*"].get()
    first = entries["First Name*"].get()
    
    if not surname or not first:
        messagebox.showerror("Error", "Surname and First Name are required!")
        return

    f_json = json.dumps([[w.get() for w in r["widgets"]] for r in family_rows])
    m_json = json.dumps([[w.get() for w in r["widgets"]] for r in membership_rows])
    dob = f"{dob_m.get()} {dob_d.get()}, {dob_y.get()}"
    
    vals = (surname, first, entries["Middle Name"].get(), 
            entries["House No.*"].get(), entries["Street*"].get(), entries["Barangay*"].get(), 
            dob, entries["Place of Birth*"].get(), entries["Sex"].get(), 
            entries["Civil Status"].get(), entries["Tel/Cp No."].get(), 
            entries["Citizenship*"].get(), entries["Religion"].get(), 
            entries["Educational Attainment"].get(), f_json, m_json)

    conn = sqlite3.connect("registry.db")
    if editing_psn:
        conn.execute("""UPDATE citizens SET 
                    Surname=?, Firstname=?, Middlename=?, HouseNo=?, Street=?, Barangay=?, 
                    DOB=?, POB=?, Sex=?, CivilStatus=?, Contact=?, Citizenship=?, 
                    Religion=?, Education=?, FamilyJSON=?, MemberJSON=? WHERE PSN=?""", vals + (editing_psn,))
        msg = "Record Updated Successfully"
    else:
        psn = f"SR-{random.randint(1000, 9999)}"
        conn.execute("INSERT INTO citizens VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (psn,) + vals)
        msg = "Citizen Registered Successfully"
    
    conn.commit()
    conn.close()
    refresh_table()
    clear_form()
    messagebox.showinfo("Success", msg)

def delete_record():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a record to delete.")
        return
    if messagebox.askyesno("Confirm", "Are you sure you want to delete this record?"):
        psn = tree.item(selected[0])['values'][0]
        conn = sqlite3.connect("registry.db")
        conn.execute("DELETE FROM citizens WHERE PSN=?", (psn,))
        conn.commit()
        conn.close()
        refresh_table()
        clear_form()

def load_for_edit(event):
    global editing_psn
    selected = tree.focus()
    if not selected: return
    psn = tree.item(selected)['values'][0]
    
    conn = sqlite3.connect("registry.db")
    r = conn.execute("SELECT * FROM citizens WHERE PSN=?", (psn,)).fetchone()
    conn.close()

    if r:
        clear_form()
        editing_psn = r[0]
        mapping = {"Surname*":1, "First Name*":2, "Middle Name":3, "House No.*":4, "Street*":5, "Barangay*":6, "Place of Birth*":8, "Sex":9, "Civil Status":10, "Tel/Cp No.":11, "Citizenship*":12, "Religion":13, "Educational Attainment":14}
        
        for key, idx in mapping.items():
            if isinstance(entries[key], tk.Entry): 
                entries[key].insert(0, r[idx])
            else: 
                entries[key].set(r[idx])

        try:
            p = r[7].replace(',', '').split(' ')
            dob_m.set(p[0]); dob_d.insert(0, p[1]); dob_y.insert(0, p[2])
        except: pass

        for row in family_rows: row["frame"].destroy()
        for row in membership_rows: row["frame"].destroy()
        family_rows.clear(); membership_rows.clear()
        
        for item in json.loads(r[15]): add_family_row(item)
        for item in json.loads(r[16]): add_membership_row(item)
        
        btn_main.config(text="Update Record", bg="#f59e0b")

def clear_form():
    global editing_psn
    editing_psn = None
    for key, widget in entries.items():
        if isinstance(widget, tk.Entry): widget.delete(0, tk.END)
        else: widget.set("")
    dob_d.delete(0, tk.END); dob_y.delete(0, tk.END); dob_m.set("January")
    
    for r in family_rows: r["frame"].destroy()
    for r in membership_rows: r["frame"].destroy()
    family_rows.clear(); membership_rows.clear()
    add_family_row(); add_membership_row()
    btn_main.config(text="Register Citizen", bg="#10b981")

def refresh_table():
    for i in tree.get_children(): tree.delete(i)
    conn = sqlite3.connect("registry.db")
    for row in conn.execute("SELECT PSN, Surname, Firstname, Barangay FROM citizens"):
        tree.insert("", "end", values=row)
    conn.close()

# --- DYNAMIC ROWS ---
def add_family_row(data=None):
    row_frame = tk.Frame(family_inner_container, bg="#f8fafc")
    row_frame.pack(fill="x", pady=2)
    row_frame.columnconfigure((0, 1, 3), weight=3); row_frame.columnconfigure(2, weight=1)
    row_widgets = []
    for i in range(4):
        e = tk.Entry(row_frame, font=("Arial", 10))
        e.grid(row=0, column=i, padx=5, sticky="ew")
        if data: e.insert(0, data[i])
        row_widgets.append(e)
    family_rows.append({"frame": row_frame, "widgets": row_widgets})

def remove_family_row():
    if len(family_rows) > 1:
        row = family_rows.pop()
        row["frame"].destroy()

def add_membership_row(data=None):
    row_frame = tk.Frame(membership_inner_container, bg="#f8fafc")
    row_frame.pack(fill="x", pady=2)
    row_frame.columnconfigure((0, 1, 2), weight=1)
    row_widgets = []
    for i in range(3):
        e = tk.Entry(row_frame, font=("Arial", 10))
        e.grid(row=0, column=i, padx=5, sticky="ew")
        if data: e.insert(0, data[i])
        row_widgets.append(e)
    membership_rows.append({"frame": row_frame, "widgets": row_widgets})

def remove_membership_row():
    if len(membership_rows) > 1:
        row = membership_rows.pop()
        row["frame"].destroy()

# --- UI SETUP ---
root = tk.Tk()
root.title("OSCA San Pablo City - Senior Citizen Registry")
root.geometry("1200x900")
root.configure(bg="#f8fafc")

# Sidebar
sidebar = tk.Frame(root, width=220, bg="#0f172a")
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="OSCA SYSTEM", fg="white", font=("Arial", 14, "bold"), bg="#0f172a", pady=20).pack()

btn_main = tk.Button(sidebar, text="Register Citizen", bg="#10b981", fg="white", font=("Arial", 10, "bold"), relief="flat", height=2, command=save_record)
btn_main.pack(fill="x", padx=20, pady=10)

tk.Button(sidebar, text="Print OSCA Form", bg="#6366f1", fg="white", font=("Arial", 10, "bold"), relief="flat", height=2, command=generate_pdf).pack(fill="x", padx=20, pady=5)

tk.Button(sidebar, text="Clear Form", bg="#64748b", fg="white", relief="flat", height=2, command=clear_form).pack(fill="x", padx=20, pady=5)
tk.Button(sidebar, text="Delete Record", bg="#ef4444", fg="white", relief="flat", height=2, command=delete_record).pack(fill="x", padx=20, pady=40)

# Form Area
main_container = tk.Frame(root, bg="#f8fafc")
main_container.pack(side="left", fill="both", expand=True, padx=20, pady=10)
main_container.columnconfigure((0, 1, 2), weight=1)

def create_field(label, r, c):
    tk.Label(main_container, text=label, font=("Arial", 9, "bold"), fg="#475569", bg="#f8fafc").grid(row=r, column=c, sticky="sw", padx=10, pady=(10, 0))
    e = tk.Entry(main_container, font=("Arial", 10))
    e.grid(row=r+1, column=c, padx=10, pady=(2, 10), sticky="ew")
    entries[label] = e

# Fields
create_field("Surname*", 0, 0); create_field("First Name*", 0, 1); create_field("Middle Name", 0, 2)
create_field("House No.*", 2, 0); create_field("Street*", 2, 1)

tk.Label(main_container, text="Barangay*", font=("Arial", 9, "bold"), fg="#475569", bg="#f8fafc").grid(row=2, column=2, sticky="sw", padx=10)
entries["Barangay*"] = ttk.Combobox(main_container, values=BARANGAYS, font=("Arial", 10))
entries["Barangay*"].grid(row=3, column=2, padx=10, pady=(2, 10), sticky="ew")

tk.Label(main_container, text="Date of Birth*", font=("Arial", 9, "bold"), fg="#475569", bg="#f8fafc").grid(row=4, column=0, sticky="sw", padx=10)
dob_frame = tk.Frame(main_container, bg="#f8fafc")
dob_frame.grid(row=5, column=0, padx=10, sticky="ew")
dob_m = ttk.Combobox(dob_frame, values=MONTHS, width=12); dob_m.set("January"); dob_m.pack(side="left", expand=True, fill="x")
dob_d = tk.Entry(dob_frame, width=5); dob_d.pack(side="left", padx=5)
dob_y = tk.Entry(dob_frame, width=8); dob_y.pack(side="left")

create_field("Place of Birth*", 4, 1); create_field("Tel/Cp No.", 4, 2)

tk.Label(main_container, text="Sex", font=("Arial", 9, "bold"), fg="#475569", bg="#f8fafc").grid(row=6, column=0, sticky="sw", padx=10)
entries["Sex"] = ttk.Combobox(main_container, values=["Male", "Female"], font=("Arial", 10))
entries["Sex"].grid(row=7, column=0, padx=10, pady=(2, 10), sticky="ew")

tk.Label(main_container, text="Civil Status", font=("Arial", 9, "bold"), fg="#475569", bg="#f8fafc").grid(row=6, column=1, sticky="sw", padx=10)
entries["Civil Status"] = ttk.Combobox(main_container, values=["Single", "Married", "Widowed", "Separated"], font=("Arial", 10))
entries["Civil Status"].grid(row=7, column=1, padx=10, pady=(2, 10), sticky="ew")

create_field("Citizenship*", 8, 0); create_field("Religion", 8, 1); create_field("Educational Attainment", 8, 2)

# Family Section
f_header = tk.Frame(main_container, bg="#f8fafc")
f_header.grid(row=10, column=0, columnspan=3, sticky="ew", pady=(15, 0), padx=10)
tk.Label(f_header, text="FAMILY COMPOSITION", font=("Arial", 10, "bold"), bg="#f8fafc").pack(side="left")
btn_f = tk.Frame(f_header, bg="#f8fafc")
btn_f.pack(side="right")
tk.Button(btn_f, text="-", width=3, bg="#fee2e2", command=remove_family_row).pack(side="left", padx=2)
tk.Button(btn_f, text="+", width=3, bg="#dcfce7", command=add_family_row).pack(side="left", padx=2)

f_labels = tk.Frame(main_container, bg="#f8fafc")
f_labels.grid(row=11, column=0, columnspan=3, sticky="ew", padx=10)
f_labels.columnconfigure((0, 1, 3), weight=3); f_labels.columnconfigure(2, weight=1)
for i, txt in enumerate(["Full Name", "Relationship", "Age", "Occupation"]):
    tk.Label(f_labels, text=txt, font=("Arial", 8, "italic"), bg="#f8fafc", fg="#64748b").grid(row=0, column=i, sticky="w")

family_inner_container = tk.Frame(main_container, bg="#f8fafc")
family_inner_container.grid(row=12, column=0, columnspan=3, sticky="ew", padx=5)

# Membership Section
m_header = tk.Frame(main_container, bg="#f8fafc")
m_header.grid(row=13, column=0, columnspan=3, sticky="ew", pady=(15, 0), padx=10)
tk.Label(m_header, text="MEMBERSHIP", font=("Arial", 10, "bold"), bg="#f8fafc").pack(side="left")
btn_m = tk.Frame(m_header, bg="#f8fafc")
btn_m.pack(side="right")
tk.Button(btn_m, text="-", width=3, bg="#fee2e2", command=remove_membership_row).pack(side="left", padx=2)
tk.Button(btn_m, text="+", width=3, bg="#dcfce7", command=add_membership_row).pack(side="left", padx=2)

m_labels = tk.Frame(main_container, bg="#f8fafc")
m_labels.grid(row=14, column=0, columnspan=3, sticky="ew", padx=10)
m_labels.columnconfigure((0, 1, 2), weight=1)
for i, txt in enumerate(["Name of Association", "Address of Association", "Date Join"]):
    tk.Label(m_labels, text=txt, font=("Arial", 8, "italic"), bg="#f8fafc", fg="#64748b").grid(row=0, column=i, sticky="w")

membership_inner_container = tk.Frame(main_container, bg="#f8fafc")
membership_inner_container.grid(row=15, column=0, columnspan=3, sticky="ew", padx=5)

# Table
tree = ttk.Treeview(main_container, columns=("ID", "Last", "First", "Brgy"), show="headings", height=6)
for col in ("ID", "Last", "First", "Brgy"):
    tree.heading(col, text=col); tree.column(col, anchor="center")
tree.grid(row=16, column=0, columnspan=3, sticky="nsew", pady=20, padx=10)
tree.bind("<Double-1>", load_for_edit)

init_db(); refresh_table(); add_family_row(); add_membership_row()
root.mainloop()
