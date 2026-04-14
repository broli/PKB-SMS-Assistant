import tkinter as tk
import customtkinter as ctk

def add_context_menu(widget):
    """Adds a functional right-click context menu to CTkEntry and CTkTextbox widgets."""
    
    # Create the context menu
    menu = tk.Menu(widget, tearoff=0)
    
    def on_copy():
        target = _get_target(widget)
        target.event_generate("<<Copy>>")

    def on_paste():
        target = _get_target(widget)
        target.event_generate("<<Paste>>")

    def on_cut():
        target = _get_target(widget)
        target.event_generate("<<Cut>>")

    menu.add_command(label="Copy", command=on_copy)
    menu.add_command(label="Paste", command=on_paste)
    menu.add_command(label="Cut", command=on_cut)

    def show_menu(event):
        # Set focus to the clicked widget so the events target it correctly
        target = _get_target(widget)
        target.focus_set()
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _get_target(w):
        """Helper to get the underlying tkinter widget of a CustomTkinter widget."""
        if hasattr(w, "_textbox"):
            return w._textbox
        if hasattr(w, "_entry"):
            return w._entry
        return w

    # Bind right-click (Button-3 is standard for Windows/Linux)
    target_widget = _get_target(widget)
    target_widget.bind("<Button-3>", show_menu)
