from tkinter import Frame, Label, Entry, Button, StringVar, OptionMenu

def create_label(parent, text, pady=5):
    label = Label(parent, text=text)
    label.pack(pady=pady)
    return label

def create_entry(parent, width=50, textvariable=None, pady=5):
    entry = Entry(parent, width=width, textvariable=textvariable)
    entry.pack(pady=pady)
    return entry

def create_button(parent, text, command, pady=10):
    button = Button(parent, text=text, command=command)
    button.pack(pady=pady)
    return button

def create_option_menu(parent, variable, options, default=None, pady=5):
    if default:
        variable.set(default)
    option_menu = OptionMenu(parent, variable, *options)
    option_menu.pack(pady=pady)
    return option_menu

def create_frame(parent, pady=5):
    frame = Frame(parent)
    frame.pack(pady=pady)
    return frame