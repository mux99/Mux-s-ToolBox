import tkinter as tk
from tkinter import ttk, messagebox, HORIZONTAL
from csv_data import CSV_Data
from fcts import open_csv, save_csv
import icon_b64
from time import time
import multiprocessing

def fork(new_data):
    App(data=new_data).start()


class App():
    def __init__(self, background_update_frequancy: int=20, data: CSV_Data=None):
        self.__root = tk.Tk()
        self.__root.title("CSV Table Viewer")
        self.__root.geometry("800x400")
        self.__root.wm_iconphoto(True, icon_b64.get_icon())

        self.__btn_frame = tk.Frame(self.__root)
        self.__btn_frame.pack(pady=10)

        ttk.Button(self.__btn_frame, text="📂- Open CSV", command=lambda: self.open_csv()).pack(side="left", padx=5)
        ttk.Button(self.__btn_frame, text="📄- Export Columns", command=self.export_column_popup).pack(side="left", padx=5)
        ttk.Button(self.__btn_frame, text="🗑- Remove Dupes", command=self.remove_dupes).pack(side="left", padx=5)
        ttk.Button(self.__btn_frame, text="🔍- Search", command=self.search_popup).pack(side="left", padx=5)
        ttk.Button(self.__btn_frame, text="💾- Save CSV", command=lambda: save_csv(self.data.data)).pack(side="left", padx=5)

        self.__frame = ttk.Frame(self.__root)
        self.__frame.pack(expand=True, fill="both")

        ttk.Frame(self.__frame, width=15).pack(side="left", fill="y")

        x_scroll = ttk.Scrollbar(self.__frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")
        y_scroll = ttk.Scrollbar(self.__frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        self.__tree = ttk.Treeview(self.__frame, show="headings", xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        self.__tree.pack(side="left", expand=True, fill="both")

        x_scroll.config(command=self.__tree.xview)
        y_scroll.config(command=self.__tree.yview)

        self.__tree.bind("<Button-3>", self.context_menu)
        self.__tree.bind("<ButtonPress-1>", self.__start_drag)
        self.__tree.bind("<ButtonRelease-1>", self.__drop_column)
        self.__tree.bind("<Double-1>", self.__copy_value)

        self.__progress = ttk.Progressbar(self.__root, orient = HORIZONTAL, mode = 'determinate')
        self.__progress.pack(fill="x")

        self.background_update_frequancy=background_update_frequancy
        self.__drag_col = None
        self.__columns_to_display = []
        self.__last_update=time()
        self.data = CSV_Data(data=data, pb_tick=self.progressTick, show=self.show_table)


    def start(self):
        self.show_table()
        self.__root.mainloop()


    def open_csv(self):
        self.data.set(open_csv())
        self.show_table()


# -------------------------------------------------------------------------------------------------
#   Display
# -------------------------------------------------------------------------------------------------

    def progressTick(self):
        self.__progress["value"] += 1
        now = time()
        if now-self.__last_update > 1/self.background_update_frequancy:
            self.__root.update()

    
    def show_table(self):
        for i in self.__tree.get_children():
            self.__tree.delete(i)

        if self.data.isEmpty():
            return

        self.__columns_to_display = ["#"]+self.data[0]
        self.__tree.config(columns=self.__columns_to_display)

        column_widths = [len(str(len(self.data)))]+[len(x) for x in self.data[-1]]

        for i,col in enumerate(self.__columns_to_display):
            self.__tree.heading(col, text=col)
            if col=="#":
                self.__tree.column(col, anchor='center', stretch=False, width=column_widths[i] * 10)
            else:
                self.__tree.column(col, anchor='center', stretch=True, minwidth=column_widths[i] * 10)
        for i,row in enumerate(self.data[1:]):
            values = [i+1]+row[:len(self.__columns_to_display)]
            tag = "grey" if i % 2 == 0 else ""
            self.__tree.insert("", "end", values=values, tags=tag)

        self.__tree.tag_configure("grey", background="#E8E8E8")
        self.__progress.config(maximum=len(self.data))
        self.__progress["value"] = 0


# -------------------------------------------------------------------------------------------------
#   Context Menus
# -------------------------------------------------------------------------------------------------

    def context_menu(self, event):
        region = self.__tree.identify_region(event.x, event.y)
        if region == "heading":
            self.column_context_menu(event)
        else:
            self.lines_context_menu(event)


    def column_context_menu(self, event):
        column = int(self.__tree.identify_column(event.x).replace("#", ""))-2

        context_menu_2 = tk.Menu(self.__root, tearoff=0)
        context_menu_2.add_command(label="integer", command=lambda: self.randomize_column_int_popup(column))
        context_menu_2.add_command(label="floating point", command=lambda: self.randomize_column_float_popup(column))
        context_menu_2.add_command(label="regex", command=lambda: self.randomize_column_regex_popup(column))
        context_menu_2.add_command(label="shuffle", command=lambda: self.data.shuffle_column(column))

        context_menu = tk.Menu(self.__root, tearoff=0)
        context_menu.add_command(label="Sort Ascending", command=lambda: self.data.sort_column(column, False))
        context_menu.add_command(label="Sort Descending", command=lambda: self.data.sort_column(column, True))
        context_menu.add_cascade(label="Randomize Column", menu=context_menu_2)
        context_menu.add_command(label="Delete column", command=lambda: self.data.delete_column(column))
        context_menu.add_command(label="Show DISTINCT", command=lambda: self.show_distinct(column))
        context_menu.add_command(label="Sum", command=lambda: self.sum_popup(column))

        context_menu.post(event.x_root, event.y_root)


    def lines_context_menu(self, event):
        selected_items = self.__tree.selection()
        if not selected_items:
            return
        selected_lines = [int(self.__tree.item(x, "values")[0]) for x in selected_items] 
        context_menu = tk.Menu(self.__root, tearoff=0)
        context_menu.add_command(label="Edit", command=lambda: self.data.delete_lines(selected_lines))
        context_menu.add_command(label="Delete", command=lambda: self.data.delete_lines(selected_lines))

        context_menu.post(event.x_root, event.y_root)


# -------------------------------------------------------------------------------------------------
#   POPUPS
# -------------------------------------------------------------------------------------------------

    def randomize_column_regex_popup(self,col):
        def ok():
            popup.destroy()
            self.data.randomize_regex(col, regex_entry.get())
            self.show_table()
        popup = tk.Toplevel(self.__root); popup.title("Randomize Column")
        tk.Label(popup, text="Regex pattern:").pack()
        regex_entry = tk.Entry(popup); regex_entry.pack()
        tk.Button(popup, text="Apply", command= lambda: ok()).pack()


    def randomize_column_float_popup(self,col):
        def ok():
            popup.destroy()
            self.data.randomize_float(col, int(float_min.get()), int(float_max.get()))
            self.show_table()
        popup = tk.Toplevel(self.__root); popup.title("Randomize Column")
        tk.Label(popup, text="Min Float:").pack()
        float_min = tk.Entry(popup); float_min.pack()
        tk.Label(popup, text="Max Float:").pack()
        float_max = tk.Entry(popup); float_max.pack()
        tk.Label(popup, text="DEcimal point:").pack()
        dec_point = tk.Entry(popup); dec_point.pack()
        tk.Button(popup, text="Apply", command=lambda: ok()).pack()


    def randomize_column_int_popup(self,col):
        def ok():
            popup.destroy()
            self.data.randomize_int(col, int(int_min.get()), int(int_max.get()))
            self.show_table()
        popup = tk.Toplevel(self.__root); popup.title("Randomize Column")
        tk.Label(popup, text="Min Int:").pack()
        int_min = tk.Entry(popup); int_min.pack()
        tk.Label(popup, text="Max Int:").pack()
        int_max = tk.Entry(popup); int_max.pack()
        tk.Button(popup, text="Apply", command=lambda: ok()).pack()


    def export_column_popup(self):
        def ok():
            select = []
            for i, v in enumerate(cols):
                if v.get():
                    select.append(i)
            new_data = self.data.export_columns(select)
            multiprocessing.Process(target=fork, args=[new_data], daemon=False).start()
            popup.destroy()
        if self.data.isEmpty():
            return
        popup = tk.Toplevel(self.__root); popup.title("Export Columns")
        cols = []
        tk.Label(popup, text="Choose Columns:").grid(row=0, sticky=tk.W)
        for i, header in enumerate(self.data[0]):
            cols.append(tk.IntVar())
            tmp = tk.Checkbutton(popup, text=header, variable=cols[-1])
            tmp.grid(row=i+1, sticky=tk.W)
        tk.Button(popup, text="Export", command=lambda: ok()).grid(sticky=tk.E)


    def search_popup(self):
        def ok():
            new_data = self.data.search(regex.get())
            multiprocessing.Process(target=fork, args=[new_data], daemon=False).start()
            popup.destroy()
        if self.data.isEmpty():
            return
        popup = tk.Toplevel(self.__root); popup.title("Search in data")
        tk.Label(popup, text="Value or Regular Expression:").pack()
        regex = tk.Entry(popup); regex.pack()
        tk.Button(popup, text="Search", command=lambda: ok()).pack()


    def show_line_popup(self, lines):
        popup = tk.Toplevel(self.__root)
        popup.title("Line Viewer")
        popup.geometry("400x300")

        line_count_label = tk.Label(popup, text=f"Total Lines: {len(lines)}", font=("Arial", 12, "bold")); line_count_label.pack(pady=5)
        text_area = tk.Text(popup, wrap="word", height=10, width=50); text_area.pack(padx=10, pady=5, fill="both", expand=True)

        for line in lines:
            text_area.insert("end", line + "\n")
        text_area.config(state="disabled")

        close_btn = ttk.Button(popup, text="Close", command=popup.destroy); close_btn.pack(pady=5)

    
    def sum_popup(self, col):
        total = self.data.sum_column(col)
        messagebox.showinfo(title="Success", message=f"total: {total}")


# -------------------------------------------------------------------------------------------------
#   Functionalities
# -------------------------------------------------------------------------------------------------

    def remove_dupes(self):
        if self.data.isEmpty():
            return
        len_b4 = len(self.data)
        self.data.remove_duplicates()
        self.show_table()
        messagebox.showinfo(title="Success", message=f"{len_b4-len(self.data)} lines removed")


    def __start_drag(self,event):
        region = self.__tree.identify_region(event.x, event.y)
        if region == "heading":
            self.__drag_col = self.__tree.identify_column(event.x)


    def __drop_column(self,event):
        region = self.__tree.identify_region(event.x, event.y)
        if region == "heading":
            drop_col = self.__tree.identify_column(event.x)
            if self.__drag_col and drop_col and self.__drag_col != drop_col:
                drag_index = int(self.__drag_col.replace("#", "")) - 1
                drop_index = int(drop_col.replace("#", "")) - 1
                self.data.swap_columns(drag_index-1, drop_index-1)
                self.show_table()
                self.__drag_col = None


    def __copy_value(self, event):
        selected_item = self.__tree.selection()
        if selected_item:
            column_id = self.__tree.identify_column(event.x)
            column_index = int(column_id[1:]) - 1
            cell_value = self.__tree.item(selected_item, 'values')[column_index]

            # Copy to clipboard
            self.__root.clipboard_clear()
            self.__root.clipboard_append(cell_value)
            self.__root.update()

    
    def show_distinct(self, col):
        seen = set()
        unique = []
        for list in self.data.data:
            self.progressTick()
            if list[col] not in seen:
                seen.add(list[col])
                unique.append(list[col])
        self.show_line_popup(unique)
        









if __name__ == "__main__":
    w = App()
    w.start()