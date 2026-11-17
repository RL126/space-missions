"""
COSC3000 CG Component - Global Space Launch Sites 1957-2022
PyOpenGL + GLUT
操作：鼠标拖拽旋转 | 滚轮缩放 | A键自动旋转 | Q/ESC退出
"""
import json, math, sys, os, random, urllib.request
from collections import defaultdict
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image

# ── 全局状态 ──────────────────────────────────────────────────────
W, H = 1000, 700
rot_x, rot_y = 20.0, 0.0
last_x, last_y = 0, 0
is_dragging = False
zoom = -4.5
auto_rotate = True
earth_tex_id = None
QUAD = None
SITES = []

BLOC_COLORS = {
    'Soviet/Russia': (0.91, 0.30, 0.24),
    'US Government': (0.14, 0.44, 0.64),
    'US Commercial': (0.52, 0.76, 0.91),
    'China':         (0.90, 0.49, 0.13),
    'Joint Venture': (0.56, 0.27, 0.68),
    'Other':         (0.58, 0.65, 0.65),
}

# ── 数据加载 ──────────────────────────────────────────────────────
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launch_data.json')
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    site_info = {}
    for r in data['records']:
        s = r['site']
        if s not in site_info:
            site_info[s] = {'lat': r['lat'], 'lng': r['lng'], 'count': 0, 'blocs': defaultdict(int)}
        site_info[s]['count'] += r['count']
        site_info[s]['blocs'][r['bloc']] += r['count']
    sites = []
    for site, info in site_info.items():
        top_bloc = max(info['blocs'], key=info['blocs'].get)
        color = BLOC_COLORS.get(top_bloc, (0.58, 0.65, 0.65))
        count = info['count']
        if   count <= 50:  pt = 10
        elif count <= 200: pt = 16
        elif count <= 500: pt = 24
        else:              pt = 36
        sites.append({'lat': info['lat'], 'lng': info['lng'],
                      'count': count, 'color': color, 'pt': pt, 'name': site})
    return sites

# ── 贴图 ──────────────────────────────────────────────────────────
EARTH_URL   = 'https://raw.githubusercontent.com/turban/webgl-earth/master/images/2_no_clouds_4k.jpg'
EARTH_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'earth_texture.jpg')

def download_texture():
    if not os.path.exists(EARTH_LOCAL):
        print("下载地球贴图...")
        try:
            urllib.request.urlretrieve(EARTH_URL, EARTH_LOCAL)
        except Exception as e:
            print(f"下载失败：{e}")

def load_texture():
    global earth_tex_id
    if not os.path.exists(EARTH_LOCAL):
        return
    img = Image.open(EARTH_LOCAL).convert('RGB').transpose(Image.FLIP_TOP_BOTTOM)
    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, img.tobytes())
    earth_tex_id = tid

# ── 坐标转换 ──────────────────────────────────────────────────────
def latlng_xyz(lat, lng, r=1.0):
    phi   = math.radians(90.0 - lat)
    theta = math.radians(lng)
    return (-r*math.sin(phi)*math.cos(theta),
             r*math.cos(phi),
             r*math.sin(phi)*math.sin(theta))

# ── 背面剔除：用旋转矩阵判断站点是否朝向相机 ────────────────────
def is_front_facing(lat, lng):
    """
    将站点位置向量经过当前旋转变换，
    若变换后z分量 > 0 则在相机一侧（可见），否则在背面（隐藏）
    """
    cx, cy, cz = latlng_xyz(lat, lng, 1.0)
    rx = math.radians(rot_x)
    ry = math.radians(rot_y)
    z1 = cy * math.sin(rx) + cz * math.cos(rx)
    z2 = -cx * math.sin(ry) + z1 * math.cos(ry)
    return z2 > -0.05

# ── 星空 ──────────────────────────────────────────────────────────
random.seed(42)
STARS = []
for _ in range(2000):
    x,y,z = random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)
    d = math.sqrt(x*x+y*y+z*z)
    STARS.append((x/d*50, y/d*50, z/d*50))

def draw_stars():
    glDisable(GL_LIGHTING)
    glPointSize(1.2)
    glColor3f(1,1,1)
    glBegin(GL_POINTS)
    for x,y,z in STARS:
        glVertex3f(x,y,z)
    glEnd()

# ── 地球 ──────────────────────────────────────────────────────────
def draw_globe():
    global QUAD
    if QUAD is None:
        QUAD = gluNewQuadric()
    glDisable(GL_LIGHTING)
    if earth_tex_id:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, earth_tex_id)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        gluQuadricTexture(QUAD, GL_TRUE)
    else:
        glColor3f(0.1, 0.3, 0.6)
    gluQuadricNormals(QUAD, GLU_SMOOTH)
    gluSphere(QUAD, 1.0, 64, 64)
    glDisable(GL_TEXTURE_2D)

# ── 发射场（Billboard + 深度缓冲清空 + 背面剔除）────────────────
def draw_sites():
    glDisable(GL_LIGHTING)

    # 关键：清空深度缓冲，让圆盘始终画在地球表面前面，不被截断
    glClear(GL_DEPTH_BUFFER_BIT)

    mv = glGetFloatv(GL_MODELVIEW_MATRIX)
    right = (mv[0][0], mv[1][0], mv[2][0])
    up    = (mv[0][1], mv[1][1], mv[2][1])
    SEGS  = 20

    for site in SITES:
        # 背面剔除：只画朝向相机的站点
        if not is_front_facing(site['lat'], site['lng']):
            continue

        cx, cy, cz = latlng_xyz(site['lat'], site['lng'], 1.005)
        r  = site['pt'] * 0.0013
        c  = site['color']
        dk = (c[0]*0.5, c[1]*0.5, c[2]*0.5)

        def circle(radius, color):
            glColor3f(*color)
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(cx, cy, cz)
            for i in range(SEGS + 1):
                a = 2 * math.pi * i / SEGS
                ca, sa = math.cos(a), math.sin(a)
                glVertex3f(
                    cx + radius*(ca*right[0] + sa*up[0]),
                    cy + radius*(ca*right[1] + sa*up[1]),
                    cz + radius*(ca*right[2] + sa*up[2])
                )
            glEnd()

        circle(r*1.4, dk)
        circle(r,     c)
        circle(r*0.4, (1.0, 1.0, 1.0))

# ── 图例 ──────────────────────────────────────────────────────────
def draw_text(x, y, text, color=(1,1,1)):
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

def draw_legend():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, W, 0, H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()
    glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)

    items = [('Soviet/Russia', BLOC_COLORS['Soviet/Russia']),
             ('US Government', BLOC_COLORS['US Government']),
             ('US Commercial', BLOC_COLORS['US Commercial']),
             ('China',         BLOC_COLORS['China']),
             ('Other',         BLOC_COLORS['Other'])]
    x0, y0 = 15, 140
    draw_text(x0, y0, 'Bloc:', (0.8,0.8,0.8))
    for i,(label,color) in enumerate(items):
        y = y0 - 18*(i+1)
        glColor3f(*color); glPointSize(10)
        glBegin(GL_POINTS); glVertex2f(x0+5, y+4); glEnd()
        draw_text(x0+16, y, label, (0.85,0.85,0.85))

    draw_text(x0, y0-18*6-10, 'Size = Launch Count:', (0.8,0.8,0.8))
    for i,(label,ps) in enumerate([('1-50',8),('51-200',14),('201-500',22),('500+',34)]):
        y = y0-18*6-10-18*(i+1)
        glColor3f(0.7,0.7,0.7); glPointSize(ps)
        glBegin(GL_POINTS); glVertex2f(x0+9, y+4); glEnd()
        draw_text(x0+22, y, label, (0.85,0.85,0.85))

    draw_text(W//2-170, H-25, 'Global Space Launch Sites 1957-2022', (1,1,1))
    draw_text(15, H-25, 'Drag:rotate  Scroll:zoom  A:auto  Q:quit', (0.5,0.5,0.5))

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ── GLUT 回调 ─────────────────────────────────────────────────────
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0, zoom)
    glRotatef(rot_x, 1, 0, 0)
    glRotatef(rot_y, 0, 1, 0)
    draw_stars()
    draw_globe()
    draw_sites()   # 深度缓冲在draw_sites内部清空，圆盘不被截断
    draw_legend()
    glutSwapBuffers()

def reshape(w, h):
    global W, H
    W, H = w, max(h,1)
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45, w/h, 0.1, 200)
    glMatrixMode(GL_MODELVIEW)

def mouse_button(button, state, x, y):
    global is_dragging, last_x, last_y, zoom
    if button == GLUT_LEFT_BUTTON:
        is_dragging = (state == GLUT_DOWN)
        last_x, last_y = x, y
    if button == 3: zoom = min(zoom+0.2, -1.5);  glutPostRedisplay()
    if button == 4: zoom = max(zoom-0.2, -10.0); glutPostRedisplay()

def mouse_motion(x, y):
    global rot_x, rot_y, last_x, last_y
    if is_dragging:
        rot_y += (x-last_x)*0.5
        rot_x  = max(-90, min(90, rot_x+(y-last_y)*0.5))
        last_x, last_y = x, y
        glutPostRedisplay()

def keyboard(key, x, y):
    global auto_rotate
    if key in (b'q', b'Q', b'\x1b'): sys.exit(0)
    if key in (b'a', b'A'): auto_rotate = not auto_rotate

def idle():
    global rot_y
    if auto_rotate:
        rot_y += 0.1
        glutPostRedisplay()

# ── 主程序 ────────────────────────────────────────────────────────
def main():
    global SITES
    download_texture()
    SITES = load_data()
    print(f"loaded {len(SITES)} sites")

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W, H)
    glutCreateWindow(b'Global Space Launch Sites 1957-2022')

    glClearColor(0.02, 0.02, 0.08, 1)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glShadeModel(GL_SMOOTH)

    load_texture()

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse_button)
    glutMotionFunc(mouse_motion)
    glutKeyboardFunc(keyboard)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == '__main__':
    main()