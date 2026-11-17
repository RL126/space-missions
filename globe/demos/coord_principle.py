"""
球坐标系转换原理演示
展示经纬度 → 3D球面坐标的几何原理

依赖：pip install PyOpenGL PyOpenGL_accelerate
运行：python coord_principle.py
操作：鼠标拖拽旋转 | 滚轮缩放 | Q退出
"""

import sys, math
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

W, H = 900, 700
rot_x, rot_y = 20.0, 30.0
last_x, last_y = 0, 0
is_dragging = False
zoom = -4.0

# 示例点：lat=45°, lng=45°
LAT, LNG = 45.0, 45.0

def lat_lng_xyz(lat, lng, r=1.0):
    phi   = math.radians(90.0 - lat)
    theta = math.radians(lng + 180.0)
    x = -r * math.sin(phi) * math.cos(theta)
    y =  r * math.cos(phi)
    z =  r * math.sin(phi) * math.sin(theta)
    return x, y, z

# ── 绘制函数 ──────────────────────────────────────────────────────
def draw_line(p1, p2, color, width=1.5):
    glLineWidth(width)
    glColor3f(*color)
    glBegin(GL_LINES)
    glVertex3f(*p1)
    glVertex3f(*p2)
    glEnd()

def draw_arc(radius, axis1, axis2, a0, a1, color, n=60, width=2.0):
    """在axis1-axis2平面内画弧"""
    glLineWidth(width)
    glColor3f(*color)
    glBegin(GL_LINE_STRIP)
    for i in range(n+1):
        a = a0 + (a1-a0)*i/n
        x = radius*(math.cos(a)*axis1[0] + math.sin(a)*axis2[0])
        y = radius*(math.cos(a)*axis1[1] + math.sin(a)*axis2[1])
        z = radius*(math.cos(a)*axis1[2] + math.sin(a)*axis2[2])
        glVertex3f(x, y, z)
    glEnd()

def draw_dot(pos, color, size=8.0):
    glPointSize(size)
    glColor3f(*color)
    glBegin(GL_POINTS)
    glVertex3f(*pos)
    glEnd()

def draw_sphere_wire(r=1.0, slices=12, stacks=12):
    """半透明线框球体"""
    quad = gluNewQuadric()
    gluQuadricDrawStyle(quad, GLU_LINE)
    glColor4f(0.2, 0.4, 0.6, 0.3)
    gluSphere(quad, r, slices, stacks)

def draw_text_3d(pos, text):
    glColor3f(0.8, 0.8, 0.8)
    glRasterPos3f(*pos)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

def draw_axis_arrow(direction, color, length=1.4):
    """画带箭头的坐标轴"""
    glLineWidth(2.0)
    glColor3f(*color)
    glBegin(GL_LINES)
    glVertex3f(0, 0, 0)
    glVertex3f(direction[0]*length, direction[1]*length, direction[2]*length)
    glEnd()
    # 端点小球
    glPointSize(6)
    glBegin(GL_POINTS)
    glVertex3f(direction[0]*(length+0.05),
               direction[1]*(length+0.05),
               direction[2]*(length+0.05))
    glEnd()

# ── 主绘制 ────────────────────────────────────────────────────────
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0, zoom)
    glRotatef(rot_x, 1, 0, 0)
    glRotatef(rot_y, 0, 1, 0)

    glDisable(GL_LIGHTING)

    # 半透明球体线框
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    draw_sphere_wire(1.0, 12, 12)

    # ── 坐标轴 ────────────────────────────────────────────────────
    draw_axis_arrow((1,0,0), (1.0, 0.27, 0.27))  # X 红
    draw_axis_arrow((0,1,0), (0.27, 1.0, 0.27))  # Y 绿
    draw_axis_arrow((0,0,1), (0.27, 0.53, 1.0))  # Z 蓝

    # 轴标签
    draw_text_3d((1.5, 0, 0),  'X')
    draw_text_3d((0, 1.5, 0),  'Y (North)')
    draw_text_3d((0, 0, 1.55), 'Z')

    # ── 计算点P的坐标 ─────────────────────────────────────────────
    phi   = math.radians(90.0 - LAT)
    theta = math.radians(LNG + 180.0)
    Px, Py, Pz = lat_lng_xyz(LAT, LNG, 1.0)

    # ── 径向向量 r ────────────────────────────────────────────────
    draw_line((0,0,0), (Px,Py,Pz), (0.7,0.7,0.7), 1.5)

    # ── 极角 φ 弧线（Y轴 → 径向方向）────────────────────────────
    # 在包含Y轴和P的平面内
    # 计算与Y轴垂直且在Y-P平面内的向量
    Pn = [Px, Py, Pz]
    Plen = math.sqrt(Px*Px+Py*Py+Pz*Pz)
    Pn = [v/Plen for v in Pn]
    yAxis = [0,1,0]
    # perp = yAxis × Pn
    perp = [
        yAxis[1]*Pn[2]-yAxis[2]*Pn[1],
        yAxis[2]*Pn[0]-yAxis[0]*Pn[2],
        yAxis[0]*Pn[1]-yAxis[1]*Pn[0],
    ]
    pl = math.sqrt(sum(v*v for v in perp))
    perp = [v/pl for v in perp]
    draw_arc(0.45, yAxis, perp, 0, phi, (1.0, 1.0, 0.0), width=2.5)

    # φ 标签
    mid_phi = phi/2
    lx = 0.45*(math.cos(mid_phi)*yAxis[0]+math.sin(mid_phi)*perp[0])
    ly = 0.45*(math.cos(mid_phi)*yAxis[1]+math.sin(mid_phi)*perp[1])
    lz = 0.45*(math.cos(mid_phi)*yAxis[2]+math.sin(mid_phi)*perp[2])
    glColor3f(1,1,0)
    draw_text_3d((lx+0.08, ly+0.05, lz), 'phi (%.0f deg)' % math.degrees(phi))

    # ── 方位角 θ 弧线（赤道平面内，从-X轴旋转）──────────────────
    negX = [-1,0,0]
    posZ = [0,0,1]
    draw_arc(0.6, negX, posZ, 0, theta, (1.0, 0.53, 0.0), width=2.5)

    # θ 标签
    mid_theta = theta/2
    tx = 0.6*(math.cos(mid_theta)*negX[0]+math.sin(mid_theta)*posZ[0])
    tz = 0.6*(math.cos(mid_theta)*negX[2]+math.sin(mid_theta)*posZ[2])
    glColor3f(1, 0.53, 0)
    draw_text_3d((tx, -0.15, tz), 'theta (%.0f deg)' % math.degrees(theta))

    # 赤道面辅助线
    draw_line((0,0,0), (Px,0,Pz), (1.0,0.53,0.0), 1.0)  # 赤道投影
    draw_line((Px,0,Pz), (Px,Py,Pz), (0.4,0.4,0.4), 1.0) # 垂直辅助线

    # ── 点P ──────────────────────────────────────────────────────
    glEnable(GL_POINT_SMOOTH)
    draw_dot((Px,Py,Pz), (1,1,1), 12)
    glColor3f(1,1,1)
    draw_text_3d((Px+0.06, Py+0.06, Pz),
                 'P(%.2f, %.2f, %.2f)' % (Px,Py,Pz))

    # ── 2D文字说明（左下角）──────────────────────────────────────
    draw_2d_info()

    glutSwapBuffers()

def draw_2d_info():
    """在屏幕左下角绘制公式说明"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, W, 0, H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    lines = [
        ((1.0,1.0,0.3), 'phi   = (90 - lat) * pi/180'),
        ((1.0,0.6,0.1), 'theta = (lng + 180) * pi/180'),
        ((1.0,0.4,0.4), 'x = -r * sin(phi) * cos(theta)'),
        ((0.4,1.0,0.4), 'y =  r * cos(phi)'),
        ((0.4,0.6,1.0), 'z =  r * sin(phi) * sin(theta)'),
        ((0.6,0.6,0.6), 'Example: lat=%.0f, lng=%.0f' % (LAT, LNG)),
    ]
    y = 140
    for color, text in lines:
        glColor3f(*color)
        glRasterPos2f(15, y)
        for ch in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
        y -= 20

    glColor3f(0.4,0.4,0.4)
    glRasterPos2f(15, H-25)
    for ch in 'Drag: rotate  |  Scroll: zoom  |  Q: quit':
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ── GLUT 回调 ─────────────────────────────────────────────────────
def reshape(w, h):
    global W, H
    W, H = w, max(h,1)
    glViewport(0,0,w,h)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45, w/h, 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def mouse_btn(button, state, x, y):
    global is_dragging, last_x, last_y, zoom
    if button == GLUT_LEFT_BUTTON:
        is_dragging = (state == GLUT_DOWN)
        last_x, last_y = x, y
    if button == 3: zoom = min(zoom+0.2, -1.5); glutPostRedisplay()
    if button == 4: zoom = max(zoom-0.2, -12.0); glutPostRedisplay()

def mouse_move(x, y):
    global rot_x, rot_y, last_x, last_y
    if is_dragging:
        rot_y += (x-last_x)*0.5
        rot_x  = max(-90, min(90, rot_x+(y-last_y)*0.5))
        last_x, last_y = x, y
        glutPostRedisplay()

def keyboard(key, x, y):
    if key in (b'q', b'Q', b'\x1b'): sys.exit(0)

# ── 主程序 ────────────────────────────────────────────────────────
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W, H)
    glutCreateWindow(b'Spherical Coordinate Transformation Principle')

    glClearColor(0.02, 0.02, 0.08, 1)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_POINT_SMOOTH)
    glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse_btn)
    glutMotionFunc(mouse_move)
    glutKeyboardFunc(keyboard)
    glutMainLoop()

if __name__ == '__main__':
    main()