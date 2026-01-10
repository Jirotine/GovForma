# OSCA Senior Citizen Registry System

A dedicated desktop application developed for the **Office for Senior Citizens Affairs (OSCA)** in San Pablo City. This system streamlines the registration process for senior citizens, manages a local database of members, and automates the generation of official OSCA Registration Forms in PDF format.

## 🚀 Features

* **Citizen Registration**: Comprehensive form covering personal details, family composition, and association memberships.
* **Automated PDF Generation**: Generates standardized OSCA forms with centered headers and organized data tables.
* **Folder Management**: Automatically saves all generated forms into a dedicated `OSCA FORMS` folder.
* **Database Management**: Full CRUD (Create, Read, Update, Delete) capabilities using SQLite.
* **Dynamic Data Entry**: Add or remove rows for family members and memberships on the fly.
* **User-Friendly Interface**: Modern sidebar navigation with a clean, scannable layout.

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **GUI Framework:** Tkinter
* **Database:** SQLite3
* **PDF Engine:** ReportLab
* **File Handling:** OS & JSON

## 📂 Project Structure

```text
GovForma/
├── OSCA FORMS/          # Generated PDF forms are saved here
├── venv/                # Virtual environment
├── main.py              # Main application logic
├── registry.db          # SQLite database file
└── README.md            # Documentation
