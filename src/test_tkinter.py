import tkinter as tk

def test_tkinter():
    """Test if tkinter is properly installed."""
    root = tk.Tk()
    root.title("Tkinter Test")
    label = tk.Label(root, text="Tkinter is working!")
    label.pack()
    root.after(1000, root.destroy)  # Close after 1 second
    root.mainloop()

if __name__ == '__main__':
    test_tkinter()
