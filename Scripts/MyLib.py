# Store newly created image
images = []


# Define a function to make the transparent rectangle
# Unused for now but might become usefull
def create_rectangle(window, x, y, a, b, **options):
    if 'alpha' in options:
        # Calculate the alpha transparency for every color(RGB)
        alpha = int(options.pop('alpha') * 255)
        # Use the fill variable to fill the shape with transparent color
        fill = options.pop('fill')
        fill = window.win.winfo_rgb(fill) + (alpha,)
        image = Image.new('RGBA', (a - x, b - y), fill)
        images.append(ImageTk.PhotoImage(image))
        window.canvas.create_image(x, y, image=images[-1], anchor='nw')


class Event(object):
    """Event that methods can subscribe/unsubscribe to
        When called, it calls all the methods that have subscribed"""
    def __init__(self):
        self.methods = []

    def __iadd__(self, method):
        self.methods.append(method)
        return self

    def __isub__(self, handler):
        self.methods.remove(handler)
        return self

    def __call__(self, *args, **keywargs):
        for method in self.methods:
            method(*args, **keywargs)


class Vector2:
    """A two-dimensional vector with Cartesian coordinates."""

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, vec):
        self.x += vec.x
        self.y += vec.y
        return self

    def __sub__(self, vec):
        self.x -= vec.x
        self.y -= vec.y
        return self


def rectIntersecting(r1, r2):

    """
    Method to check if two entities are colliding
    :param r1: entity1
    :param r2: entity2
    :return: True if colliding, False if not
    """

    pos1 = r1.getModule("RigidBody").pos
    pos2 = r2.getModule("RigidBody").pos

    bounds1 = r1.getModule("Body2D").bounds
    bounds2 = r2.getModule("Body2D").bounds

    Xbound = pos1.x < pos2.x + bounds2.x and pos1.x + bounds1.x > pos2.x
    Ybound = pos1.y < pos2.y + bounds2.y and pos1.y + bounds1.y > pos2.y

    return Xbound and Ybound


def create_circle(x, y, r, canvas, color):
    """
    Creates circle
    :param x: centerX
    :param y: centerY
    :param r: radius
    :param canvas: canvas the circle will belong to
    :param color: fill color
    :return: returns index to oval on canvas
    """
    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    return canvas.create_oval(x0, y0, x1, y1, fill=color, outline="")


def edit_circle(x, y, r, circle, canvas):
    """Edit circle element with [circle] index"""
    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    canvas.coords(circle, x0, y0, x1, y1)


def AABBresolution(body1, body2):

    """Checks if two entities are colliding and resolves them"""

    col1 = body1.getModule("Body2D")
    col2 = body2.getModule("Body2D")

    rb1 = body1.getModule("RigidBody")
    rb2 = body2.getModule("RigidBody")

    if rb2.ifSimulated or not rb1.ifSimulated:
        return

    lastPosX1 = rb1.pos.x - rb1.vel.x * 9.81
    lastPosY1 = rb1.pos.y - rb1.vel.y * 9.81

    resolution = Vector2(0, 0)

    if lastPosY1 + col1.height() > rb2.pos.y and lastPosY1 < rb2.pos.y + col2.height():
        if lastPosX1 > rb2.pos.x + col2.width() / 2:
            resolution = Vector2(rb2.pos.x + col2.width() - rb1.pos.x, 0)
            rb1.vel.x = 0
            col1.colliding = True
        if lastPosX1 + col1.width() < rb2.pos.x + col2.width() / 2:
            resolution = Vector2(rb2.pos.x - (rb1.pos.x + col1.width()), 0)
            rb1.vel.x = 0
            col1.colliding = True

    if lastPosX1 < rb2.pos.x + col2.width() and lastPosX1 + col1.width() > rb2.pos.x:
        if lastPosY1 > rb2.pos.y + col2.height() / 2:
            resolution = Vector2(0, rb2.pos.y + col2.height() - rb1.pos.y)
            rb1.vel.y = 0
            col1.colliding = True
        if lastPosY1 + col1.height() < rb2.pos.y + col2.height() / 2:
            resolution = Vector2(0, rb2.pos.y - (rb1.pos.y + col1.height()))
            rb1.vel.y = 0
            col1.colliding = True
            col1.collidingDown = True

    rb1.pos += resolution


def interpolateCanvasItem(index, canvas, x, y, speed):
    """Uses a reciprocal interpolation to get canvas element from where they are to (x,y)"""
    coords = canvas.coords(index)
    canvas.move(index, (x - coords[0]) / speed, (y - coords[1]) / speed)
