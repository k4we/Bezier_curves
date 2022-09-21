''' This program create Bezier curves

    Press Add Button to be allowed to create new lines
    You can extend the lines for having differents curves
    Keep in mind that if you wanna drag a point, the Add Button
    must be off.
    The others buttons speak by them-selves

    strongly inspired by PM 2Ring 2018.09.21
'''

import tkinter as tk
from collections import deque

def flat(x0, y0, x1, y1, tol):
    return abs(x0*y1 - x1*y0) < tol * abs(x0 * x1 + y0 * y1)

def bezier_points(x0, y0, x1, y1, x2, y2, x3, y3, tol=0.001):
    ''' Draw a cubic Bezier cirve by recursive subdivision
        The curve is subdivided until each of the 4 sections is
        sufficiently flat, determined by the angle between them.
        tol is the tolerance expressed as the tangent of the angle
    '''
    if (flat(x1-x0, y1-y0, x2-x0, y2-y0, tol) and
        flat(x2-x1, y2-y1, x3-x1, y3-y1, tol)):
        return [x0, y0, x3, y3]

    x01, y01 = (x0 + x1) / 2., (y0 + y1) / 2.
    x12, y12 = (x1 + x2) / 2., (y1 + y2) / 2.
    x23, y23 = (x2 + x3) / 2., (y2 + y3) / 2.
    xa, ya = (x01 + x12) / 2., (y01 + y12) / 2.
    xb, yb = (x12 + x23) / 2., (y12 + y23) / 2.
    xc, yc = (xa + xb) / 2., (ya + yb) / 2.

    # Double the tolerance angle
    tol = 2. / (1. / tol - tol)
    return (bezier_points(x0, y0, x01, y01, xa, ya, xc, yc, tol)[:-2] +
        bezier_points(xc, yc, xb, yb, x23, y23, x3, y3, tol))

class Dot:
    ''' Movable Canvas circles '''
    dots = {}
    def __init__(self, canvas, x, y, color, rad=1, tags=""):
        self.x, self.y = x, y
        self.canvas = canvas
        self.id = canvas.create_oval(x-rad, y-rad, x+rad, y+rad,
            outline=color, fill='white', tags=tags)
        Dot.dots[self.id] = self

    def update(self, x, y):
        dx, dy = x - self.x, y - self.y
        self.x, self.y = x, y
        self.canvas.move(self.id, dx, dy)

    def __repr__(self):
        return f'Dot({self.id}, {self.x}, {self.y})'

    def delete(self):
        self.canvas.delete(self.id)
        del Dot.dots[self.id]
class Line:
    '''Line between circles'''
    lines = {}
    def __init__(self, canvas, x1, y1, x2, y2, color):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.canvas = canvas
        self.id = canvas.create_line(x1, y1, x2, y2, fill=color)
        Line.lines[self.id] = self

    def __repr__(self):
        return f'Line({self.id})'

    def delete(self):
        self.canvas.delete(self.id)
        del Line.lines[self.id]

class GUI:
    def __init__(self):
        self.root = root = tk.Tk()
        width = root.winfo_screenwidth() * 4 // 5
        height = root.winfo_screenheight() * 4 // 5
        root.geometry(f'{width}x{height}')
        root.title('Bezier curve drawing')
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        self.canvas = canvas = tk.Canvas(root)
        canvas.grid(row=0, column=0, sticky='nsew')

        # The Bezier control points, and groups for each curve
        self.lines, self.dots, self.middots, self.groups = [], [], [], []

        # Various Canvas-related items: the current Dot being dragged, the
        # lines comprising the convex hull, the lines of the Bezier curve
        # and the animated spot.
        self.drag_item = self.curve = None

        # Add bindings for clicking & dragging any object with the "dot" tag
        canvas.tag_bind("dot", "<ButtonPress-1>", self.on_dot_press)
        canvas.tag_bind("dot", "<B1-Motion>", self.on_dot_motion)
        canvas.tag_bind("dot", "<ButtonRelease-1>", self.on_dot_release)

        canvas.tag_bind("mdot", "<ButtonPress-1>", self.on_mdot_press)
        canvas.tag_bind("mdot", "<B1-Motion>", self.on_mdot_motion)
        canvas.tag_bind("mdot", "<ButtonRelease-1>", self.on_dot_release)

        canvas.bind("<ButtonPress-1>", self.add_dot)
        canvas.bind("<ButtonRelease-1>", lambda evt: self.draw_lines())

        frame = tk.Frame(root, bd=1, relief=tk.SUNKEN)
        frame.grid(row=1, column=0, sticky='nsew')

        # Button to add new Dots to the canvas
        self.add_btn = tk.Button(frame, text="Add", relief="sunken",
            command=self.add_dot_cb)
        self.add_btn.pack(side=tk.LEFT)
        self.add_btn.state = True

        self.hide_btn = tk.Button(frame, text="Hide", relief="raised",\
            command=self.hide_cb)
        self.hide_btn.pack(side=tk.LEFT)
        self.hide_btn.state = False

        tk.Button(frame, text="Delete", command=self.delete_cb).pack(side=tk.LEFT)
        tk.Button(frame, text="Clear", command=self.clear_cb).pack(side=tk.LEFT)

        root.mainloop()

    def add_dot_cb(self):
        self.add_btn.state ^= 1
        self.add_btn["relief"] = "sunken" if self.add_btn.state else "raised"

    def add_dot(self, event):
        '''Add a new point'''
        if not self.add_btn.state:
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        color = "blue"
        self.dots.append(Dot(self.canvas, x, y, color, rad=4, tags="dot"))

    def clear_cb(self):
        for element in self.dots + self.middots + self.lines:
            element.delete()
        self.dots.clear()
        self.middots.clear()
        self.lines.clear()

        if self.curve:
            self.canvas.delete(self.curve)
            self.curve = None
        if not self.add_btn.state:
            self.add_dot_cb()

    def delete_cb(self):
        self.dots.pop().delete()
        if len(self.dots) % 2:
            self.lines.pop().delete()
            self.middots.pop().delete()
        self.draw_lines()

    def hide_cb(self):
        self.hide_btn.state ^= 1
        self.hide_btn["relief"] = "sunken" if self.hide_btn.state else "raised"
        state = tk.HIDDEN if self.hide_btn.state else tk.NORMAL
        for item in self.dots + self.middots + self.lines:
            self.canvas.itemconfig(item.id, state = state)

#######################################################

    def on_dot_press(self, event):
        ''' Beginning drag of a dot '''
        # Record the item being dragged
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.drag_item = Dot.dots[self.canvas.find_closest(x, y)[0]]
        self.canvas.config(cursor = 'fleur')


    def on_dot_motion(self, event):
        ''' Handle dragging of a dot '''
        if self.drag_item is None:
            return
        id = self.dots.index(self.drag_item)
        # Get the mouse location
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        # Move the Dot to the new location
        self.drag_item.update(x, y)
        self.canvas.tag_raise(self.drag_item.id)
        if id % 2 or not id == len(self.dots):
            if 1 < id < len(self.dots)-2:
                mp = self.middots[id//2 - 1]
                pair = self.dots[id-1] if id % 2 else self.dots[id+1]
                x, y = 2*mp.x - x, 2*mp.y - y
                pair.update(x, y)
                self.canvas.tag_raise(pair.id)
        self.draw_lines()

    def on_mdot_press(self, event):
        # Record the item being dragged
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.drag_item = Dot.dots[self.canvas.find_closest(x, y)[0]]

    def on_mdot_motion(self, event):
        ''' Handle dragging of an mdot object '''
        if self.drag_item is None:
            return
        # Find the control points of the segment containing this mdot
        idx = self.middots.index(self.drag_item) * 2 + 2
        d0, d1 = self.dots[idx:idx+2]
        dx, dy = d0.x - self.drag_item.x, d0.y - self.drag_item.y,
        # Get the mouse location
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.drag_item.update(x, y)
        d0.update(x+dx, y+dy)
        d1.update(x-dx, y-dy)

        self.draw_lines()

    def on_dot_release(self, event):
        ''' End drag of an object '''
        # Reset the drag information
        self.drag_item = None
        self.canvas.config(cursor = 'arrow')

################################################################

    def draw_lines(self):
        ''' Draw the lines of the Bezier curve '''
        if len(self.dots) < 2:
            return
        if self.lines:
            for i in range(len(self.lines)):
                self.lines.pop().delete()
        coords = []
        for dot in self.dots:
            coords.extend((dot.x, dot.y))
        # draw the lines
        max = (len(coords))//4 * 4
        for i in range(0, max, 4):
            self.lines.append(Line(self.canvas, *coords[i:i+4], "blue"))
            self.canvas.tag_lower(self.lines[-1].id)

        self.draw_curve()

    def draw_curve(self):
        ''' Draw midpoints and the curve'''
        if len(self.dots) < 4:
            return

        dot_queue = deque(self.middots)

        # Draw midpoints
        coords = []
        for i, dot in enumerate(self.dots):
            x, y = dot.x, dot.y
            if i % 2 and 1 < i < len(self.dots)-2:
                px, py = coords[-2:]
                if dot_queue:
                    mdot = dot_queue.popleft()
                    mx, my = (px+x)*0.5, (py+y)*0.5
                    mdot.update(mx, my)
                    self.canvas.tag_raise(mdot.id)
                else:
                    mx, my = (px+x)*0.5, (py+y)*0.5
                    mdot = Dot(self.canvas, mx, my, "white", tags="mdot", rad=4)
                    self.middots.append(mdot)
                coords.extend((mx, my))
            coords.extend((x, y))

        # Draw the Bezier curves
        points = []
        self.groups.clear()
        maxi = (len(coords)) // 6 * 6
        for i in range(0, maxi, 6):
            group = coords[i:i+8]
            #print(group)
            if len(group) < 8:
                break
            points.extend(bezier_points(*group)[:-2])
            self.groups.append(group)

        if self.curve:
            self.canvas.coords(self.curve, points)
        else:
            self.curve = self.canvas.create_line(points, fill="red")

if __name__ == "__main__":
    GUI()
