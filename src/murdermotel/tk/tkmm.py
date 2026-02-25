import argparse

import tkinter as tk
from tkinter import ttk

import ttyio5 as ttyio
import bbsengine5 as bbsengine

class App(tk.Tk):
    def __init__(self, args):
        super().__init__()

        self.args = args
        self.sysop = False # bbsengine.checksysop(args)
        
        self.vars = {}

        self.title("Murder Motel")
        # UI options
        paddings = {"padx": 10, "pady": 10}

        # configure style
        self.style = ttk.Style(self)
        self.style.configure("TLabel",  font=("TkFixedFont", 11))
        self.style.configure("TButton", font=("TkFixedFont", 11)) #Helvetica", 11))
        self.style.configure("TEntry",  font=("TkFixedFont", 11))

        # configure the grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)

        self.dbh = bbsengine.databaseconnect(self.args)

        self.memberid = bbsengine.getcurrentmemberid(args)

        self.bind('<Escape>', lambda e: self.close(e))

    def close(self, e):
        self.quit()

def buildargs(args=None, **kw):
    parser = argparse.ArgumentParser("member")
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    parser.add_argument("--debug", action="store_true", dest="debug")

    defaults = {"databasename": "zoidweb5", "databasehost":"localhost", "databaseuser": None, "databaseport":15433, "databasepassword":None} # port=5432
#    defaults = {"databasename": "zoidweb5", "databasehost":"localhost", "databaseuser": None, "databaseport":5432, "databasepassword":None} # port=5432
    bbsengine.buildargdatabasegroup(parser, defaults)

    return parser

if __name__ == "__main__":
    parser = buildargs()
    args = parser.parse_args()

    app = App(args)
    app.mainloop()
