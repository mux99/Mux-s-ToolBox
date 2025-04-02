import tkinter as tk
from tkinter import filedialog, messagebox
import csv

def read_file_lines(filename):
    print(filename)
    with open(filename, "r") as file:
        return file.readlines()

def swap(haystack, needles):
    #create switch table
    switch_table = {}
    for line in read_file_lines(needles):
        tmp = line.split(",")
        switch_table[tmp[0].strip()] = tmp[1].strip()

    #the swap
    out = f"{".".join(haystack.split(".")[:-1])}_out.{haystack.split(".")[-1]}"
    with open(haystack, mode="r", newline="") as infile, open(out, mode="w", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            for i in range(len(row)):
                row[i] = switch_table.get(row[i], row[i])
            writer.writerow(row)
    return True

def select_haystack():
    file_path = filedialog.askopenfilename(title="Select Haystack")
    if file_path:
        tk_haystack.set(file_path)

def select_needles():
    file_path = filedialog.askopenfilename(title="Select Needles")
    if file_path:
        tk_needles.set(file_path)

def continue_program():
    if not tk_needles.get() or not tk_haystack.get():
        messagebox.showerror("Error", "Please select both files before continuing.")
    else:
        if swap(tk_haystack.get(), tk_needles.get()):
            root.destroy()
        else:
            messagebox.showerror("Error", "An error occured")

def massReplace():
    global root
    root = tk.Tk()
    root.title("File Selector")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    global tk_needles, tk_haystack
    tk_needles = tk.StringVar()
    tk_haystack = tk.StringVar()

    frame = tk.Frame(root)
    frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    frame.columnconfigure(1, weight=1)

    tk.Label(frame, text="Select Haystack:").grid(row=0, column=0, columnspan=3, sticky="w", pady=5)
    tk.Entry(frame, textvariable=tk_haystack, state='readonly', width=40).grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
    tk.Button(frame, text="Browse", command=select_haystack).grid(row=1, column=2, padx=5, pady=5)

    tk.Label(frame, text="Select Needles:").grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
    tk.Entry(frame, textvariable=tk_needles, state='readonly', width=40).grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
    tk.Button(frame, text="Browse", command=select_needles).grid(row=4, column=2, padx=5, pady=5)

    tk.Frame(frame, height=1, bg="black").grid(row=5, column=0, columnspan=3, sticky="ew", pady=10)

    tk.Button(frame, text="Continue", bg="green", fg="white", command=continue_program).grid(row=6, column=0, columnspan=3, pady=20)
    root.mainloop()

if __name__ == "__main__":
    massReplace()



