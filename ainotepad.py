import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, font
import os
import sys
from datetime import datetime
import tempfile

class Notepad(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Untitled - Notepad")
        self.geometry("800x600")

        # State
        self.filename = None
        self.modified = False
        self.find_text = ""
        self.find_match_case = False

        # Font state
        self.current_font_family = "Consolas" if "Consolas" in font.families() else "Courier New"
        self.current_font_size = 11
        self.current_font_weight = "normal"
        self.current_font_slant = "roman"
        self.text_font = font.Font(family=self.current_font_family,
                                   size=self.current_font_size,
                                   weight=self.current_font_weight,
                                   slant=self.current_font_slant)

        # Word wrap & statusbar state
        self.word_wrap_var = tk.BooleanVar(value=False)
        self.status_bar_var = tk.BooleanVar(value=True)

        self._create_widgets()
        self._create_menus()
        self._bind_shortcuts()

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    # ----------------------------------------------------------------------
    # UI creation
    # ----------------------------------------------------------------------
    def _create_widgets(self):
        # Text area + scrollbars
        self.text_frame = tk.Frame(self)
        self.text_frame.pack(fill=tk.BOTH, expand=True)

        self.v_scroll = tk.Scrollbar(self.text_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scroll = tk.Scrollbar(self.text_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.text = tk.Text(
            self.text_frame,
            wrap="none",
            undo=True,
            maxundo=-1,
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
            font=self.text_font
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        self.v_scroll.config(command=self.text.yview)
        self.h_scroll.config(command=self.text.xview)

        # Modified tracking
        self.text.bind("<<Modified>>", self._on_text_modified)
        self.text.bind("<KeyRelease>", self._update_status_bar)
        self.text.bind("<ButtonRelease>", self._update_status_bar)

        # Status bar
        self.status_bar = tk.Label(self, text="Ln 1, Col 1", anchor="w", relief=tk.SUNKEN, bd=1)
        if self.status_bar_var.get():
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_menus(self):
        self.menu_bar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=False)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Page Setup...", command=self.page_setup)
        file_menu.add_command(label="Print...", command=self.print_file, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.edit_menu.add_command(label="Undo", command=self.edit_undo, accelerator="Ctrl+Z")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.edit_cut, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", command=self.edit_copy, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", command=self.edit_paste, accelerator="Ctrl+V")
        self.edit_menu.add_command(label="Delete", command=self.edit_delete, accelerator="Del")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Find...", command=self.find_dialog, accelerator="Ctrl+F")
        self.edit_menu.add_command(label="Find Next", command=self.find_next, accelerator="F3")
        self.edit_menu.add_command(label="Replace...", command=self.replace_dialog, accelerator="Ctrl+H")
        self.edit_menu.add_command(label="Go To...", command=self.goto_dialog, accelerator="Ctrl+G")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        self.edit_menu.add_command(label="Time/Date", command=self.insert_time_date, accelerator="F5")
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)

        # Format menu
        format_menu = tk.Menu(self.menu_bar, tearoff=False)
        format_menu.add_checkbutton(label="Word Wrap", command=self.toggle_word_wrap,
                                    variable=self.word_wrap_var)
        format_menu.add_command(label="Font...", command=self.font_dialog)
        self.menu_bar.add_cascade(label="Format", menu=format_menu)

        # View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.view_menu.add_checkbutton(label="Status Bar", command=self.toggle_status_bar,
                                       variable=self.status_bar_var)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=False)
        help_menu.add_command(label="View Help", command=self.view_help)
        help_menu.add_separator()
        help_menu.add_command(label="About Notepad", command=self.about_dialog)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=self.menu_bar)
        self._update_view_menu_state()

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_file_as())
        self.bind("<Control-p>", lambda e: self.print_file())
        self.bind("<Control-z>", lambda e: self.edit_undo())
        self.bind("<Control-x>", lambda e: self.edit_cut())
        self.bind("<Control-c>", lambda e: self.edit_copy())
        self.bind("<Control-v>", lambda e: self.edit_paste())
        self.bind("<Delete>", lambda e: self.edit_delete())
        self.bind("<Control-f>", lambda e: self.find_dialog())
        self.bind("<F3>", lambda e: self.find_next())
        self.bind("<Control-h>", lambda e: self.replace_dialog())
        self.bind("<Control-g>", lambda e: self.goto_dialog())
        self.bind("<Control-a>", lambda e: self.select_all())
        self.bind("<F5>", lambda e: self.insert_time_date())

    # ----------------------------------------------------------------------
    # File operations
    # ----------------------------------------------------------------------
    def new_file(self):
        if not self._maybe_save_changes():
            return
        self.text.delete("1.0", tk.END)
        self.filename = None
        self.modified = False
        self._update_title()

    def open_file(self):
        if not self._maybe_save_changes():
            return
        filetypes = [
            ("Text Documents", "*.txt"),
            ("All Files", "*.*")
        ]
        path = filedialog.Open(self, filetypes=filetypes).show()
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(path, "r", encoding="cp1252", errors="replace") as f:
                    content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.filename = path
            self.text.edit_modified(False)
            self.modified = False
            self._update_title()

    def save_file(self):
        if self.filename is None:
            return self.save_file_as()
        else:
            return self._write_to_file(self.filename)

    def save_file_as(self):
        filetypes = [
            ("Text Documents", "*.txt"),
            ("All Files", "*.*")
        ]
        initialfile = "Untitled.txt" if self.filename is None else os.path.basename(self.filename)
        path = filedialog.SaveAs(self, filetypes=filetypes, initialfile=initialfile).show()
        if path:
            if not os.path.splitext(path)[1]:
                path += ".txt"
            return self._write_to_file(path)
        return False

    def _write_to_file(self, path):
        try:
            text = self.text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.rstrip("\n") + "\n")
            self.filename = path
            self.text.edit_modified(False)
            self.modified = False
            self._update_title()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
            return False

    def page_setup(self):
        # Simple stub; real Notepad uses printer/page options
        messagebox.showinfo("Page Setup", "Page Setup is not implemented.\n\n"
                             "You can still use Print... to print the current document.")

    def print_file(self):
        # Simple Windows-oriented print: save to temp file and use default printer
        if sys.platform.startswith("win"):
            # Ensure content is saved somewhere
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "notepad_clone_print.txt")
            try:
                text = self.text.get("1.0", tk.END)
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(text)
                os.startfile(temp_path, "print")
            except Exception as e:
                messagebox.showerror("Print", f"Printing failed:\n{e}")
        else:
            messagebox.showinfo("Print", "Printing is only implemented on Windows using the default printer.")

    def on_exit(self):
        if not self._maybe_save_changes():
            return
        self.destroy()

    def _maybe_save_changes(self):
        if not self.modified:
            return True
        result = messagebox.askyesnocancel("Notepad", "Do you want to save changes?")
        if result is None:  # Cancel
            return False
        if result:  # Yes
            if not self.save_file():
                return False
        return True

    # ----------------------------------------------------------------------
    # Edit operations
    # ----------------------------------------------------------------------
    def edit_undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def edit_cut(self):
        self.text.event_generate("<<Cut>>")

    def edit_copy(self):
        self.text.event_generate("<<Copy>>")

    def edit_paste(self):
        self.text.event_generate("<<Paste>>")

    def edit_delete(self):
        try:
            self.text.delete("sel.first", "sel.last")
        except tk.TclError:
            pass

    def select_all(self):
        self.text.tag_add("sel", "1.0", "end-1c")
        self.text.mark_set("insert", "1.0")
        self.text.see("insert")

    def insert_time_date(self):
        now = datetime.now().strftime("%H:%M %m/%d/%Y")
        self.text.insert("insert", now)

    # ----------------------------------------------------------------------
    # Find / Replace / Go To
    # ----------------------------------------------------------------------
    def find_dialog(self):
        FindDialog(self)

    def find_next(self):
        if not self.find_text:
            self.find_dialog()
            return
        self._do_find_next(self.find_text, self.find_match_case)

    def _do_find_next(self, text, match_case):
        if not text:
            return
        start = self.text.index("insert")
        if self.text.compare(start, "==", "end-1c"):
            start = "1.0"
        flags = {} if match_case else {"nocase": 1}

        pos = self.text.search(text, start, stopindex="end", **flags)
        if not pos:
            # Wrap search
            pos = self.text.search(text, "1.0", stopindex="end", **flags)
            if not pos:
                messagebox.showinfo("Notepad", f"Cannot find '{text}'")
                return
        end_pos = f"{pos}+{len(text)}c"
        self.text.tag_remove("sel", "1.0", "end")
        self.text.tag_add("sel", pos, end_pos)
        self.text.mark_set("insert", end_pos)
        self.text.see(pos)

    def replace_dialog(self):
        ReplaceDialog(self)

    def _replace_once(self, find_text, replace_text, match_case):
        if not find_text:
            return

        # If selection matches the find text, replace it, else find next
        try:
            sel_start = self.text.index("sel.first")
            sel_end = self.text.index("sel.last")
            sel_text = self.text.get(sel_start, sel_end)
        except tk.TclError:
            sel_text = ""

        compare = (lambda a, b: a == b) if match_case else (lambda a, b: a.lower() == b.lower())

        if sel_text and compare(sel_text, find_text):
            self.text.delete(sel_start, sel_end)
            self.text.insert(sel_start, replace_text)
            new_end = f"{sel_start}+{len(replace_text)}c"
            self.text.tag_add("sel", sel_start, new_end)
            self.text.mark_set("insert", new_end)
        else:
            self._do_find_next(find_text, match_case)

    def _replace_all(self, find_text, replace_text, match_case):
        if not find_text:
            return
        count = 0
        start = "1.0"
        flags = {} if match_case else {"nocase": 1}
        while True:
            pos = self.text.search(find_text, start, stopindex="end", **flags)
            if not pos:
                break
            end_pos = f"{pos}+{len(find_text)}c"
            self.text.delete(pos, end_pos)
            self.text.insert(pos, replace_text)
            start = f"{pos}+{len(replace_text)}c"
            count += 1
        messagebox.showinfo("Notepad", f"Replaced {count} occurrence(s).")

    def goto_dialog(self):
        if self.word_wrap_var.get():
            messagebox.showinfo("Notepad", "Go To is not available with Word Wrap turned on.")
            return

        line_count = int(float(self.text.index("end-1c").split(".")[0]))
        line_no = simpledialog.askinteger("Go To Line", f"Line number (1 - {line_count}):",
                                          minvalue=1, maxvalue=line_count, parent=self)
        if line_no is not None:
            index = f"{line_no}.0"
            self.text.mark_set("insert", index)
            self.text.see(index)
            self._update_status_bar()

    # ----------------------------------------------------------------------
    # Format & View
    # ----------------------------------------------------------------------
    def toggle_word_wrap(self):
        if self.word_wrap_var.get():
            # Enable word wrap: no horizontal scrollbar
            self.text.config(wrap="word")
            self.h_scroll.pack_forget()
        else:
            self.text.config(wrap="none")
            self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self._update_view_menu_state()

    def font_dialog(self):
        FontDialog(self)

    def toggle_status_bar(self):
        if self.status_bar_var.get():
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            self.status_bar.pack_forget()
        self._update_view_menu_state()

    def _update_view_menu_state(self):
        # In classic Notepad, when Word Wrap is on, Status Bar is disabled
        if self.word_wrap_var.get():
            self.view_menu.entryconfig("Status Bar", state="disabled")
            # Also Go To is disabled when Word Wrap is on
            self.edit_menu.entryconfig("Go To...", state="disabled")
        else:
            self.view_menu.entryconfig("Status Bar", state="normal")
            self.edit_menu.entryconfig("Go To...", state="normal")

    # ----------------------------------------------------------------------
    # Help
    # ----------------------------------------------------------------------
    def view_help(self):
        messagebox.showinfo("Notepad Help",
                            "This is a Notepad-like editor written in Python with Tkinter.\n\n"
                            "It supports basic editing, find/replace, word wrap, font selection,\n"
                            "status bar, and basic printing (on Windows).")

    def about_dialog(self):
        messagebox.showinfo("About Notepad",
                            "Notepad Clone\n\n"
                            "Written in Python using Tkinter.\n"
                            "Designed to resemble Windows XP/7 Notepad.")

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------
    def _on_text_modified(self, event=None):
        if self.text.edit_modified():
            self.modified = True
            self._update_title()
            self._update_status_bar()
            self.text.edit_modified(False)

    def _update_title(self):
        name = self.filename if self.filename else "Untitled"
        base = os.path.basename(name)
        if self.modified:
            self.title(f"*{base} - Notepad")
        else:
            self.title(f"{base} - Notepad")

    def _update_status_bar(self, event=None):
        if not self.status_bar_var.get():
            return
        try:
            index = self.text.index("insert")
            line, col = index.split(".")
            # Notepad shows column as 1-based
            col = str(int(col) + 1)
            self.status_bar.config(text=f"Ln {line}, Col {col}")
        except Exception:
            self.status_bar.config(text="Ln 1, Col 1")


# ----------------------------------------------------------------------
# Find dialog
# ----------------------------------------------------------------------
class FindDialog(tk.Toplevel):
    def __init__(self, parent: Notepad):
        super().__init__(parent)
        self.parent = parent
        self.title("Find")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.find_var = tk.StringVar(value=parent.find_text)
        self.match_case_var = tk.BooleanVar(value=parent.find_match_case)

        tk.Label(self, text="Find what:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.entry = tk.Entry(self, textvariable=self.find_var, width=30)
        self.entry.grid(row=0, column=1, padx=8, pady=8)

        self.match_case_cb = tk.Checkbutton(self, text="Match case", variable=self.match_case_var)
        self.match_case_cb.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="w")

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=0, column=2, rowspan=2, padx=8, pady=8, sticky="ns")

        find_next_btn = tk.Button(btn_frame, text="Find Next", width=12, command=self.on_find_next)
        find_next_btn.pack(fill=tk.X, pady=(0, 4))

        cancel_btn = tk.Button(btn_frame, text="Cancel", width=12, command=self.destroy)
        cancel_btn.pack(fill=tk.X)

        self.entry.focus_set()
        self.bind("<Return>", lambda e: self.on_find_next())

    def on_find_next(self):
        text = self.find_var.get()
        match_case = self.match_case_var.get()
        self.parent.find_text = text
        self.parent.find_match_case = match_case
        self.parent._do_find_next(text, match_case)


# ----------------------------------------------------------------------
# Replace dialog
# ----------------------------------------------------------------------
class ReplaceDialog(tk.Toplevel):
    def __init__(self, parent: Notepad):
        super().__init__(parent)
        self.parent = parent
        self.title("Replace")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.find_var = tk.StringVar(value=parent.find_text)
        self.replace_var = tk.StringVar()
        self.match_case_var = tk.BooleanVar(value=parent.find_match_case)

        tk.Label(self, text="Find what:").grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")
        self.find_entry = tk.Entry(self, textvariable=self.find_var, width=30)
        self.find_entry.grid(row=0, column=1, padx=8, pady=(8, 4))

        tk.Label(self, text="Replace with:").grid(row=1, column=0, padx=8, pady=4, sticky="w")
        self.replace_entry = tk.Entry(self, textvariable=self.replace_var, width=30)
        self.replace_entry.grid(row=1, column=1, padx=8, pady=4)

        self.match_case_cb = tk.Checkbutton(self, text="Match case", variable=self.match_case_var)
        self.match_case_cb.grid(row=2, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="w")

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=0, column=2, rowspan=3, padx=8, pady=8, sticky="ns")

        tk.Button(btn_frame, text="Find Next", width=12, command=self.on_find_next).pack(fill=tk.X, pady=(0, 4))
        tk.Button(btn_frame, text="Replace", width=12, command=self.on_replace).pack(fill=tk.X, pady=4)
        tk.Button(btn_frame, text="Replace All", width=12, command=self.on_replace_all).pack(fill=tk.X, pady=4)
        tk.Button(btn_frame, text="Cancel", width=12, command=self.destroy).pack(fill=tk.X, pady=(4, 0))

        self.find_entry.focus_set()

    def on_find_next(self):
        text = self.find_var.get()
        match_case = self.match_case_var.get()
        self.parent.find_text = text
        self.parent.find_match_case = match_case
        self.parent._do_find_next(text, match_case)

    def on_replace(self):
        find_text = self.find_var.get()
        replace_text = self.replace_var.get()
        match_case = self.match_case_var.get()
        self.parent.find_text = find_text
        self.parent.find_match_case = match_case
        self.parent._replace_once(find_text, replace_text, match_case)

    def on_replace_all(self):
        find_text = self.find_var.get()
        replace_text = self.replace_var.get()
        match_case = self.match_case_var.get()
        self.parent.find_text = find_text
        self.parent.find_match_case = match_case
        self.parent._replace_all(find_text, replace_text, match_case)


# ----------------------------------------------------------------------
# Font dialog (simple)
# ----------------------------------------------------------------------
class FontDialog(tk.Toplevel):
    def __init__(self, parent: Notepad):
        super().__init__(parent)
        self.parent = parent
        self.title("Font")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.family_var = tk.StringVar(value=parent.current_font_family)
        self.size_var = tk.StringVar(value=str(parent.current_font_size))
        self.bold_var = tk.BooleanVar(value=(parent.current_font_weight == "bold"))
        self.italic_var = tk.BooleanVar(value=(parent.current_font_slant == "italic"))

        families = sorted(font.families())

        # Family listbox
        tk.Label(self, text="Font:").grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")
        self.family_listbox = tk.Listbox(self, listvariable=tk.StringVar(value=families),
                                         height=10, exportselection=False)
        self.family_listbox.grid(row=1, column=0, padx=8, pady=(0, 8))
        # Preselect current family
        try:
            idx = families.index(self.family_var.get())
            self.family_listbox.selection_set(idx)
            self.family_listbox.see(idx)
        except ValueError:
            pass

        # Size listbox
        tk.Label(self, text="Size:").grid(row=0, column=1, padx=8, pady=(8, 4), sticky="w")
        sizes = [str(s) for s in range(8, 33, 2)]
        self.size_listbox = tk.Listbox(self, listvariable=tk.StringVar(value=sizes),
                                       height=10, exportselection=False, width=4)
        self.size_listbox.grid(row=1, column=1, padx=8, pady=(0, 8), sticky="n")
        try:
            idx = sizes.index(self.size_var.get())
            self.size_listbox.selection_set(idx)
            self.size_listbox.see(idx)
        except ValueError:
            pass

        # Style checkboxes
        style_frame = tk.Frame(self)
        style_frame.grid(row=1, column=2, padx=8, pady=(0, 8), sticky="n")
        tk.Checkbutton(style_frame, text="Bold", variable=self.bold_var).pack(anchor="w")
        tk.Checkbutton(style_frame, text="Italic", variable=self.italic_var).pack(anchor="w")

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=(0, 8))
        tk.Button(btn_frame, text="OK", width=10, command=self.on_ok).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Cancel", width=10, command=self.destroy).pack(side=tk.LEFT, padx=4)

    def on_ok(self):
        # Get selected family
        try:
            idxs = self.family_listbox.curselection()
            if idxs:
                family = self.family_listbox.get(idxs[0])
            else:
                family = self.parent.current_font_family
        except Exception:
            family = self.parent.current_font_family

        # Get selected size
        try:
            idxs = self.size_listbox.curselection()
            if idxs:
                size = int(self.size_listbox.get(idxs[0]))
            else:
                size = self.parent.current_font_size
        except Exception:
            size = self.parent.current_font_size

        weight = "bold" if self.bold_var.get() else "normal"
        slant = "italic" if self.italic_var.get() else "roman"

        self.parent.current_font_family = family
        self.parent.current_font_size = size
        self.parent.current_font_weight = weight
        self.parent.current_font_slant = slant

        self.parent.text_font.config(family=family, size=size, weight=weight, slant=slant)
        self.destroy()


if __name__ == "__main__":
    app = Notepad()
    app.mainloop()
