from tkinter import *

window = None
selected_val = None
flag = True


def get_selected_val():
    global selected_val
    return selected_val


def select():
    global selected_val
    selected_val = optionVar.get()
    print("Selected value :", selected_val)
    on_quit()


def set_classes(classes):
    global option
    pass


def on_quit():
    global flag
    print("called")
    flag = False
    window.destroy()


def select_class_name(classes):
    global selected_val, option, flag, window, optionVar
    window = Tk()
    selected_val = None
    window.title("Class Selection")
    w, h = 200, 100
    x = window.winfo_pointerx()
    y = window.winfo_pointery()  # height of the screen
    window.geometry('%dx%d+%d+%d' % (w, h, x, y))
    window.protocol("WM_DESTROY_WINDOW", on_quit)
    optionVar = StringVar()
    optionVar.set("class")
    option = OptionMenu(window, optionVar, *classes)
    option.pack()
    btnShow = Button(window, text="Select", command=select)
    btnShow.pack()
    flag = True
    show()
    while flag:
        pass
    return selected_val


def show():
    window.mainloop()


if __name__ == "__main__":
    show()
