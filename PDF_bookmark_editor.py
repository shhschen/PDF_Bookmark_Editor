# file: bookmark_gui_with_scrollbar_and_autofill.py

from pypdf import PdfReader, PdfWriter
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

class BookmarkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 書籤添加工具（支援層級 + 滾動）")
        self.root.geometry("700x800")

        self.input_pdf_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar()
        self.entries = []
        self.total_pages = 0

        tk.Button(root, text="選擇 PDF 檔案", command=self.select_pdf).pack(pady=5)
        tk.Entry(root, textvariable=self.input_pdf_path, width=60).pack(pady=5)

        self.page_label = tk.Label(root, text="PDF 總頁數：0")
        self.page_label.pack()

        # Scrollable entry frame
        canvas = tk.Canvas(root, height=300)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        self.entry_container = tk.Frame(canvas)

        self.entry_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.entry_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(self.entry_container, text="層級", width=8).grid(row=0, column=0)
        tk.Label(self.entry_container, text="頁碼 (從1)", width=12).grid(row=0, column=1)
        tk.Label(self.entry_container, text="書籤標題", width=40).grid(row=0, column=2)

        self.entry_row = 1
        for _ in range(20):
            self.add_entry()

        tk.Button(root, text="+ 新增書籤欄位", command=self.add_entry).pack(pady=5)
        tk.Button(root, text="讀取 PDF 現有書籤", command=self.load_bookmarks_from_pdf).pack(pady=5)
        tk.Button(root, text="從文字檔匯入書籤", command=self.import_from_txt).pack(pady=5)
        tk.Button(root, text="預覽書籤內容", command=self.preview_bookmarks).pack(pady=5)

        self.preview_box = tk.Text(root, height=10, width=70, state='disabled')
        self.preview_box.pack(pady=5)

        tk.Button(root, text="匯出書籤模板", command=self.export_template).pack(pady=5)

        tk.Button(root, text="選擇輸出檔名", command=self.select_output).pack(pady=5)
        tk.Entry(root, textvariable=self.output_pdf_path, width=60).pack(pady=5)

        tk.Button(root, text="產生書籤 PDF", command=self.apply_bookmarks, bg="green", fg="white").pack(pady=10)

    def add_entry(self, level_val="0", page_val="", title_val=""):
        level_var = tk.StringVar(value=level_val)
        page_var = tk.StringVar(value=page_val)
        title_var = tk.StringVar(value=title_val)

        tk.Entry(self.entry_container, textvariable=level_var, width=5).grid(row=self.entry_row, column=0, padx=2, pady=2)
        tk.Entry(self.entry_container, textvariable=page_var, width=8).grid(row=self.entry_row, column=1, padx=2, pady=2)
        tk.Entry(self.entry_container, textvariable=title_var, width=40).grid(row=self.entry_row, column=2, padx=2, pady=2)
        self.entries.append((level_var, page_var, title_var))
        self.entry_row += 1
        self.root.update_idletasks()

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.input_pdf_path.set(path)
            try:
                reader = PdfReader(path)
                self.total_pages = len(reader.pages)
                self.page_label.config(text=f"PDF 總頁數：{self.total_pages}")
            except Exception as e:
                messagebox.showerror("錯誤", f"無法讀取 PDF：{e}")

    def select_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.output_pdf_path.set(path)

    def import_from_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        failed_lines = []
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    self.add_entry(parts[0], parts[1], parts[2])
                else:
                    failed_lines.append(line.strip())
            if failed_lines:
                messagebox.showwarning("匯入警告", "格式錯誤行：\n" + "\n".join(failed_lines))
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取書籤文字檔失敗：{e}")

    def load_bookmarks_from_pdf(self):
        path = self.input_pdf_path.get()
        if not path:
            messagebox.showerror("錯誤", "請先選擇 PDF")
            return
        try:
            reader = PdfReader(path)
            self.clear_all_entries()
            def recurse(outlines, level=0):
                for item in outlines:
                    if isinstance(item, list):
                        recurse(item, level + 1)
                    else:
                        title = item.title
                        page_index = reader.pages.index(item.page)
                        self.add_entry(str(level), str(page_index + 1), title)
            recurse(reader.outline)
        except Exception as e:
            messagebox.showerror("錯誤", f"載入 PDF 書籤失敗：{e}")

    def clear_all_entries(self):
        for widget in self.entry_container.winfo_children()[3:]:
            widget.destroy()
        self.entries.clear()
        self.entry_row = 1

    def preview_bookmarks(self):
        self.preview_box.configure(state='normal')
        self.preview_box.delete("1.0", tk.END)
        for level_var, page_var, title_var in self.entries:
            lvl = level_var.get().strip()
            page = page_var.get().strip()
            title = title_var.get().strip()
            if page and title:
                indent = '  ' * int(lvl) if lvl.isdigit() else ''
                self.preview_box.insert(tk.END, f"{indent}第 {page} 頁：{title}\n")
        self.preview_box.configure(state='disabled')

    def export_template(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 層級\t頁碼\t標題\n")
            f.write("0\t1\t第一章\n")
            f.write("1\t2\t1.1 小節\n")
            f.write("0\t4\t第二章\n")
        messagebox.showinfo("完成", "範例已匯出")

    def apply_bookmarks(self):
        input_path = self.input_pdf_path.get()
        output_path = self.output_pdf_path.get()
        if not input_path or not output_path:
            messagebox.showerror("錯誤", "請指定輸入與輸出檔")
            return

        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        bookmarks = []
        for level_var, page_var, title_var in self.entries:
            try:
                level = int(level_var.get().strip())
                page = int(page_var.get().strip()) - 1
                title = title_var.get().strip()
                if title and 0 <= page < len(reader.pages):
                    bookmarks.append((level, page, title))
            except:
                continue

        bookmarks.sort(key=lambda x: x[1])

        stack = []
        for lvl, pg, ttl in bookmarks:
            while len(stack) > lvl:
                stack.pop()
            parent = stack[-1] if lvl > 0 and len(stack) >= lvl else None
            bookmark = writer.add_outline_item(ttl, pg, parent=parent)
            stack.append(bookmark)

        with open(output_path, "wb") as f:
            writer.write(f)

        messagebox.showinfo("完成", "PDF 書籤已寫入")

if __name__ == "__main__":
    root = tk.Tk()
    app = BookmarkGUI(root)
    root.mainloop()
