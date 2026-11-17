"""
COSC3000 CG Component - Global Space Launch Sites 3D Bar Chart
PyOpenGL + GLUT - 东西半球分屏显示

操作：鼠标拖拽旋转 | 滚轮缩放 | Q/ESC退出
"""

import json, math, sys, os
from collections import defaultdict
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

W, H = 1200, 650
rot_x, rot_y = 35.0, 20.0
last_x, last_y = 0, 0
is_dragging = False
zoom = -5.0
SITES_EAST = []
SITES_WEST = []

BLOC_COLORS = {
    'Soviet/Russia': (0.91, 0.30, 0.24),
    'US Government': (0.14, 0.44, 0.64),
    'US Commercial': (0.52, 0.76, 0.91),
    'China':         (0.90, 0.49, 0.13),
    'Joint Venture': (0.56, 0.27, 0.68),
    'Other':         (0.58, 0.65, 0.65),
}

def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launch_data.json')
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    site_info = {}
    for r in data['records']:
        s = r['site']
        if s not in site_info:
            site_info[s] = {'lat': r['lat'], 'lng': r['lng'],
                            'count': 0, 'blocs': defaultdict(int)}
        site_info[s]['count'] += r['count']
        site_info[s]['blocs'][r['bloc']] += r['count']

    max_count = max(info['count'] for info in site_info.values())
    east, west = [], []
    for site, info in site_info.items():
        top_bloc = max(info['blocs'], key=info['blocs'].get)
        color = BLOC_COLORS.get(top_bloc, (0.58, 0.65, 0.65))
        h = (info['count'] / max_count) * 3.0
        entry = {
            'name':   site.split(',')[0][:14],
            'lat':    info['lat'],
            'lng':    info['lng'],
            'count':  info['count'],
            'height': h,
            'color':  color,
            'x':      info['lng'] / 36.0,
            'z':     -info['lat'] / 36.0,
        }
        if info['lng'] >= 0:
            east.append(entry)
        else:
            west.append(entry)
    return east, west, max_count

def draw_bar(x, z, height, color, width=0.10):
    w = width / 2
    h = height
    r, g, b = color
    glColor3f(min(r*1.3,1), min(g*1.3,1), min(b*1.3,1))
    glBegin(GL_QUADS)
    glVertex3f(x-w,h,z-w); glVertex3f(x+w,h,z-w)
    glVertex3f(x+w,h,z+w); glVertex3f(x-w,h,z+w)
    glEnd()
    glColor3f(r,g,b)
    glBegin(GL_QUADS)
    glVertex3f(x-w,0,z+w); glVertex3f(x+w,0,z+w)
    glVertex3f(x+w,h,z+w); glVertex3f(x-w,h,z+w)
    glEnd()
    glColor3f(r*0.6,g*0.6,b*0.6)
    glBegin(GL_QUADS)
    glVertex3f(x-w,0,z-w); glVertex3f(x+w,0,z-w)
    glVertex3f(x+w,h,z-w); glVertex3f(x-w,h,z-w)
    glEnd()
    glColor3f(r*0.75,g*0.75,b*0.75)
    glBegin(GL_QUADS)
    glVertex3f(x-w,0,z-w); glVertex3f(x-w,0,z+w)
    glVertex3f(x-w,h,z+w); glVertex3f(x-w,h,z-w)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(x+w,0,z-w); glVertex3f(x+w,0,z+w)
    glVertex3f(x+w,h,z+w); glVertex3f(x+w,h,z-w)
    glEnd()

def draw_grid(x_min, x_max):
    glColor3f(0.12, 0.22, 0.32)
    glLineWidth(0.8)
    for lat in range(-90, 91, 30):
        z = -lat/36.0
        glBegin(GL_LINES); glVertex3f(x_min,0,z); glVertex3f(x_max,0,z); glEnd()
    lng = int(x_min*36)
    while lng <= int(x_max*36):
        x = lng/36.0
        glBegin(GL_LINES); glVertex3f(x,0,-2.6); glVertex3f(x,0,2.6); glEnd()
        lng += 30
    glColor3f(0.3,0.5,0.6); glLineWidth(1.5)
    glBegin(GL_LINE_LOOP)
    glVertex3f(x_min,0,-2.5); glVertex3f(x_max,0,-2.5)
    glVertex3f(x_max,0, 2.5); glVertex3f(x_min,0, 2.5)
    glEnd()

def draw_labels(sites):
    glColor3f(0.95,0.95,0.95)
    for s in sites:
        if s['count'] >= 50:
            glRasterPos3f(s['x'], s['height']+0.1, s['z'])
            for ch in s['name']:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(ch))

def draw_axis_labels(x_min, x_max):
    glColor3f(0.45,0.55,0.65)
    lng = int(x_min*36)
    while lng <= int(x_max*36):
        x = lng/36.0
        glRasterPos3f(x, 0.02, 2.75)
        for ch in (str(lng)+'E' if lng>=0 else str(-lng)+'W'):
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(ch))
        lng += 60
    for lat in [-60,-30,0,30,60]:
        z = -lat/36.0
        glRasterPos3f(x_max+0.05, 0.02, z)
        label = str(abs(lat))+('N' if lat>=0 else 'S')
        for ch in label:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(ch))

def set_camera():
    glLoadIdentity()
    glTranslatef(0, -0.8, zoom)
    glRotatef(rot_x, 1,0,0)
    glRotatef(rot_y, 0,1,0)

def draw_ui():
    glViewport(0, 0, W, H)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, W, 0, H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    glColor3f(1,1,1)
    glRasterPos2f(W//2-180, H-22)
    for ch in 'Global Space Launch Sites 1957-2022  |  Bar Height = Launch Count':
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glColor3f(0.7,0.9,1.0)
    glRasterPos2f(W//4-80, H-40)
    for ch in 'Eastern Hemisphere  (0 ~ 180E)':
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    glRasterPos2f(3*W//4-80, H-40)
    for ch in 'Western Hemisphere  (180W ~ 0)':
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    # 分割线
    glColor3f(0.3,0.4,0.5); glLineWidth(1.5)
    glBegin(GL_LINES); glVertex2f(W//2,0); glVertex2f(W//2,H); glEnd()

    # 图例
    items = [
        ('Soviet/Russia', BLOC_COLORS['Soviet/Russia']),
        ('US Government', BLOC_COLORS['US Government']),
        ('US Commercial', BLOC_COLORS['US Commercial']),
        ('China',         BLOC_COLORS['China']),
        ('Other',         BLOC_COLORS['Other']),
    ]
    x0, y0 = 15, 130
    glColor3f(0.7,0.7,0.7)
    glRasterPos2f(x0, y0+16)
    for ch in 'Bloc:':
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    for i,(label,color) in enumerate(items):
        y = y0 - i*18
        glColor3f(*color); glPointSize(10)
        glBegin(GL_POINTS); glVertex2f(x0+5,y+4); glEnd()
        glColor3f(0.85,0.85,0.85)
        glRasterPos2f(x0+18, y)
        for ch in label:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glColor3f(0.4,0.4,0.4)
    glRasterPos2f(15, 15)
    for ch in 'Drag: rotate  |  Scroll: zoom  |  Q: quit':
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    half = W // 2

    # 左：东半球
    glViewport(0, 0, half, H)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45, half/max(H,1), 0.1, 200)
    glMatrixMode(GL_MODELVIEW)
    set_camera()
    glTranslatef(-2.5, 0, 0)
    draw_grid(0, 5.0)
    for s in SITES_EAST:
        draw_bar(s['x'], s['z'], s['height'], s['color'])
    draw_labels(SITES_EAST)
    draw_axis_labels(0, 5.0)

    # 右：西半球
    glViewport(half, 0, half, H)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45, half/max(H,1), 0.1, 200)
    glMatrixMode(GL_MODELVIEW)
    set_camera()
    glTranslatef(2.5, 0, 0)
    draw_grid(-5.0, 0)
    for s in SITES_WEST:
        draw_bar(s['x'], s['z'], s['height'], s['color'])
    draw_labels(SITES_WEST)
    draw_axis_labels(-5.0, 0)

    draw_ui()
    glutSwapBuffers()

def reshape(w, h):
    global W, H
    W, H = w, max(h,1)
    glutPostRedisplay()

def mouse_button(button, state, x, y):
    global is_dragging, last_x, last_y, zoom
    if button == GLUT_LEFT_BUTTON:
        is_dragging = (state == GLUT_DOWN)
        last_x, last_y = x, y
    if button == 3: zoom = min(zoom+0.3, -2.0);  glutPostRedisplay()
    if button == 4: zoom = max(zoom-0.3, -15.0); glutPostRedisplay()

def mouse_motion(x, y):
    global rot_x, rot_y, last_x, last_y
    if is_dragging:
        rot_y += (x-last_x)*0.5
        rot_x  = max(-90, min(90, rot_x+(y-last_y)*0.5))
        last_x, last_y = x, y
        glutPostRedisplay()

def keyboard(key, x, y):
    if key in (b'q', b'Q', b'\x1b'): sys.exit(0)

def main():
    global SITES_EAST, SITES_WEST
    SITES_EAST, SITES_WEST, max_count = load_data()
    print(f"East:{len(SITES_EAST)} West:{len(SITES_WEST)} max={max_count}")

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W, H)
    glutCreateWindow(b'Space Launch Sites - 3D Bar Chart')

    glClearColor(0.02, 0.05, 0.10, 1)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_FLAT)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse_button)
    glutMotionFunc(mouse_motion)
    glutKeyboardFunc(keyboard)
    glutMainLoop()

if __name__ == '__main__':
    main()