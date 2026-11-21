/*
 * nhe-taj-mahal_x11ui.c
 *
 * Contributed by Maarten (Zynthian community), November 2026, for Zynthian
 * and other Linux LV2 hosts on the Raspberry Pi. Optional: built only with
 * `make X11UI=1`. MOD builds and the desktop formats never use it.
 *
 * Changes in this repo: the plugin URI and port offset can be set at build
 * time, so the same source serves Taj Mahal Stereo (ports shifted by one).
 * tools/check_x11ui.py checks the control table below against the TTL and
 * the pedal face CSS, so a face or port change can't silently drift.
 *
 * X11 user interface for the NHE Taj Mahal reverb (LV2 ui:X11UI), built from
 * the MOD GUI artwork in the bundle's modgui/ folder:
 *
 *   modgui/background.jpg   panel image (1200x700), drawn at the design size 600x350
 *   modgui/knob.png         strip of knob frames side by side; the frame count
 *                           is width / height (65 frames of 123x123)
 *   modgui/button.png       LED button strip: left half = LED off,
 *                           right half = LED on
 *
 * Layout (from modgui/stylesheet-tajmahal.css), in design px:
 *   knobs   62x62 at predelay(52,126) decay(131,126) diffusion(211,126)
 *           speed(321,126) depth(399,126) feedback(480,126)
 *           dry(399,245) reverb(477,245)
 *   buttons 95x29 at on/off(45,261) vintage(156,261) tails(267,261)
 *
 * The window scales with its size. The panel keeps its proportions
 * (600 x 350) and is centred in the window, so knobs and buttons stay in
 * place. Mouse positions are converted back to design px.
 *
 * Controls:
 *   drag a knob up or down, or use the mouse wheel over it
 *   click a button to toggle it (On/Off is the plugin's enable port 13)
 *
 * Build on the Pi (needs lv2-dev, libx11-dev, libimlib2-dev):
 *   gcc -shared -fPIC -O2 -o nhe-taj-mahal_x11ui.so nhe-taj-mahal_x11ui.c \
 *       $(pkg-config --cflags --libs x11 imlib2)
 *
 * The UI loads its images from <bundle>/modgui/ when it is created, so the
 * modgui/ folder must be installed in the plugin bundle next to the .so files.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <X11/Xlib.h>
#include <Imlib2.h>

#include <lv2/core/lv2.h>
#include <lv2/ui/ui.h>

/* Overridable at build time (see the X11UI rule in the root Makefile). */
#ifndef NHE_UI_URI
#define NHE_UI_URI  "https://github.com/Kiwooky/NHE-Taj-Mahal#X11UI"
#endif
/* Added to every port index below: 0 for mono, 1 for Taj Mahal Stereo,
 * which has two audio inputs. */
#ifndef NHE_PORT_OFFSET
#define NHE_PORT_OFFSET 0
#endif
#define URI_PARENT  "http://lv2plug.in/ns/extensions/ui#parent"
#define URI_IDLE    "http://lv2plug.in/ns/extensions/ui#idleInterface"
#define URI_SHOW    "http://lv2plug.in/ns/extensions/ui#showInterface"

/* Design size of the panel (CSS px) */
#define DESIGN_W        600
#define DESIGN_H        350
#define KNOB_SIZE       62
#define BTN_W           95
#define BTN_H           29
#define MAX_KNOB_FRAMES 128

typedef enum { KNOB, BUTTON } CtrlKind;

typedef struct {
    CtrlKind kind;
    uint32_t port;     /* LV2 port index in the mono plugin (nhe-taj-mahal.ttl) */
    float    min;
    float    max;
    float    def;
    int      x;        /* position inside the 600x350 design */
    int      y;
} Control;

static const Control CTRL[] = {
    { KNOB,   3,   0, 140, 81, 52,  126 },   /* Pre-delay      */
    { KNOB,   4,   1,  99, 72, 131, 126 },   /* Decay          */
    { KNOB,   5,   0,   9,  9, 211, 126 },   /* Diffusion      */
    { KNOB,   6,   0,  99, 61, 321, 126 },   /* Chorus speed   */
    { KNOB,   7,   0,  99, 31, 399, 126 },   /* Chorus depth   */
    { KNOB,   8,   0,  99, 20, 480, 126 },   /* Chorus feedback*/
    { KNOB,   9,   0,  99,  0, 399, 245 },   /* Dry level      */
    { KNOB,  10,   0,  99, 99, 477, 245 },   /* Reverb level   */
    { BUTTON,13,   0,   1,  1,  45, 261 },   /* On/Off (enable)*/
    { BUTTON,11,   0,   1,  1, 156, 261 },   /* Vintage        */
    { BUTTON,12,   0,   1,  1, 267, 261 },   /* Tails          */
};

#define NUM_CTRL ((int)(sizeof(CTRL) / sizeof(CTRL[0])))

typedef struct {
    LV2UI_Write_Function write;
    LV2UI_Controller     controller;
    Display             *dpy;
    Window               win;
    Window               parent;

    int                  win_w;      /* window size in px */
    int                  win_h;
    int dirty;
    Imlib_Image back;
    Imlib_Image bgc;
    int bgc_w;
    int bgc_h;
    Imlib_Image fe_src[8];
    Imlib_Image fe_img[8];
    int fe_pw[8];
    int fe_ph[8];
    int fe_q[8];
    double               scale;      /* px per design px */
    double               ox;         /* px offset of the design area */
    double               oy;

    Imlib_Image          bg_src;                   /* full-size panel */
    Imlib_Image          bg_cache;                 /* panel at the drawn size */
    int                  bg_cw;
    int                  bg_ch;
    Imlib_Image          knob[MAX_KNOB_FRAMES];    /* full-size frames */
    int                  nframes;
    Imlib_Image          btn[2];                   /* [0] LED off, [1] LED on */

    float                value[NUM_CTRL];
    int                  dragging;                 /* control index, or -1 */
    int                  drag_y;                   /* px */
    float                drag_start;
} NHEUI;

/* ---------- layout ---------- */

static void update_layout(NHEUI *ui)
{
    double sx = ui->win_w / (double)DESIGN_W;
    double sy = ui->win_h / (double)DESIGN_H;

    ui->scale = sx < sy ? sx : sy;
    ui->ox = (ui->win_w - DESIGN_W * ui->scale) / 2.0;
    ui->oy = (ui->win_h - DESIGN_H * ui->scale) / 2.0;
}

static int to_px_x(const NHEUI *ui, double x) { return (int)(ui->ox + x * ui->scale + 0.5); }
static int to_px_y(const NHEUI *ui, double y) { return (int)(ui->oy + y * ui->scale + 0.5); }
static int to_px_len(const NHEUI *ui, double len)
{
    int v = (int)(len * ui->scale + 0.5);
    return v < 1 ? 1 : v;
}

static void to_design(const NHEUI *ui, int x, int y, double *dx, double *dy)
{
    *dx = (x - ui->ox) / ui->scale;
    *dy = (y - ui->oy) / ui->scale;
}

static int inside(double dx, double dy, double x, double y, double w, double h)
{
    return dx >= x && dx < x + w && dy >= y && dy < y + h;
}

/* Off-screen buffer at window size: everything is drawn here, then copied
 * to the window in one go, so nothing flickers. */
static void ensure_back(NHEUI *ui)
{
    if (ui->back) {
        imlib_context_set_image(ui->back);
        if (imlib_image_get_width() == ui->win_w &&
            imlib_image_get_height() == ui->win_h) {
            return;
        }
        imlib_free_image();
        ui->back = NULL;
    }
    ui->back = imlib_create_image(ui->win_w, ui->win_h);
}

/* Blend an image into the off-screen buffer at pixel coordinates. */
static void blend_px(NHEUI *ui, Imlib_Image img, int px, int py, int pw, int ph)
{
    int iw, ih;

    if (!img || pw < 1 || ph < 1) {
        return;
    }
    imlib_context_set_image(img);
    iw = imlib_image_get_width();
    ih = imlib_image_get_height();

    imlib_context_set_image(ui->back);
    imlib_blend_image_onto_image(img, 1, 0, 0, iw, ih, px, py, pw, ph);
}

static void sync_size(NHEUI *ui)
{
    Window       root;
    int          px, py;
    unsigned int pw, ph, border, depth;

    if (!ui->parent) {
        return;
    }
    if (XGetGeometry(ui->dpy, ui->parent, &root, &px, &py, &pw, &ph, &border, &depth) &&
        pw > 0 && ph > 0 &&
        ((int)pw != ui->win_w || (int)ph != ui->win_h)) {
        ui->win_w = (int)pw;
        ui->win_h = (int)ph;
        XResizeWindow(ui->dpy, ui->win, pw, ph);
        update_layout(ui);
        ensure_back(ui);
    }
}

/* ---------- imlib2 helpers ---------- */

static void imlib_setup(NHEUI *ui)
{
    int screen = DefaultScreen(ui->dpy);

    imlib_context_set_display(ui->dpy);
    imlib_context_set_visual(DefaultVisual(ui->dpy, screen));
    imlib_context_set_colormap(DefaultColormap(ui->dpy, screen));
    imlib_context_set_drawable(ui->win);
    imlib_context_set_blend(1);
}

static void free_img(Imlib_Image *img)
{
    if (*img) {
        imlib_context_set_image(*img);
        imlib_free_image();
        *img = NULL;
    }
}

/* Rebuild the panel at the size it is drawn at, when that size changes. */
static void ensure_bg_cache(NHEUI *ui)
{
    int dw = to_px_len(ui, DESIGN_W);
    int dh = to_px_len(ui, DESIGN_H);
    int w, h;

    if (ui->bg_cache && dw == ui->bg_cw && dh == ui->bg_ch) {
        return;
    }
    free_img(&ui->bg_cache);

    imlib_context_set_image(ui->bg_src);
    w = imlib_image_get_width();
    h = imlib_image_get_height();
    ui->bg_cache = imlib_create_cropped_scaled_image(0, 0, w, h, dw, dh);
    ui->bg_cw = dw;
    ui->bg_ch = dh;
}

static int load_assets(NHEUI *ui, const char *bundle_path)
{
    char        path[1024];
    Imlib_Image src;
    int         w, h, i, fw;

    /* panel background, kept at full size and scaled when drawn */
    snprintf(path, sizeof path, "%s/modgui/background.jpg", bundle_path);
    ui->bg_src = imlib_load_image(path);
    if (!ui->bg_src) {
        fprintf(stderr, "nhe-taj-mahal UI: cannot load %s\n", path);
        return -1;
    }

    /* knob strip: frames are side by side and square */
    snprintf(path, sizeof path, "%s/modgui/knob.png", bundle_path);
    src = imlib_load_image(path);
    if (!src) {
        fprintf(stderr, "nhe-taj-mahal UI: cannot load %s\n", path);
        return -1;
    }
    imlib_context_set_image(src);
    w = imlib_image_get_width();
    h = imlib_image_get_height();
    ui->nframes = w / h;
    if (ui->nframes < 1) ui->nframes = 1;
    if (ui->nframes > MAX_KNOB_FRAMES) ui->nframes = MAX_KNOB_FRAMES;
    fw = w / ui->nframes;
    for (i = 0; i < ui->nframes; i++) {
        imlib_context_set_image(src);
        ui->knob[i] = imlib_create_cropped_image(i * fw, 0, fw, h);
    }
    imlib_context_set_image(src);
    imlib_free_image();

    /* LED button strip: left half off, right half on */
    snprintf(path, sizeof path, "%s/modgui/button.png", bundle_path);
    src = imlib_load_image(path);
    if (!src) {
        fprintf(stderr, "nhe-taj-mahal UI: cannot load %s\n", path);
        return -1;
    }
    imlib_context_set_image(src);
    w = imlib_image_get_width();
    h = imlib_image_get_height();
    ui->btn[0] = imlib_create_cropped_image(0, 0, w / 2, h);
    imlib_context_set_image(src);
    ui->btn[1] = imlib_create_cropped_image(w / 2, 0, w - w / 2, h);
    imlib_context_set_image(src);
    imlib_free_image();

    return 0;
}

static void free_assets(NHEUI *ui)
{
    free_img(&ui->bgc);
    { int k_; for (k_ = 0; k_ < 8; k_++) free_img(&ui->fe_img[k_]); }
    if (ui->back) {
        imlib_context_set_image(ui->back);
        imlib_free_image();
        ui->back = NULL;
    }
    int i;

    free_img(&ui->bg_cache);
    free_img(&ui->bg_src);
    for (i = 0; i < MAX_KNOB_FRAMES; i++) {
        free_img(&ui->knob[i]);
    }
    for (i = 0; i < 2; i++) {
        free_img(&ui->btn[i]);
    }
}

/* Draw an image at a design-space position and size. */
static void draw_at(NHEUI *ui, Imlib_Image img, double x, double y, double w, double h)
{
    blend_px(ui, img, to_px_x(ui, x), to_px_y(ui, y), to_px_len(ui, w), to_px_len(ui, h));
}

/* ---------- value handling ---------- */

/* Clamp, round (all controls are integers) and send to the plugin. */
static void set_value(NHEUI *ui, int i, float v)
{
    const Control *c = &CTRL[i];

    if (v < c->min) v = c->min;
    if (v > c->max) v = c->max;
    v = (float)((int)(v + 0.5f));

    ui->value[i] = v;
    ui->write(ui->controller, c->port + NHE_PORT_OFFSET, sizeof(float), 0, &v);
}

/* ---------- drawing ---------- */

static void draw(NHEUI *ui)
{
    int i;

    imlib_setup(ui);

    /* clear the area around the panel */
    XSetForeground(ui->dpy, DefaultGC(ui->dpy, DefaultScreen(ui->dpy)),
                   BlackPixel(ui->dpy, DefaultScreen(ui->dpy)));
    imlib_context_set_image(ui->back);
    imlib_context_set_color(0, 0, 0, 255);
    imlib_image_fill_rectangle(0, 0, ui->win_w, ui->win_h);

    ensure_bg_cache(ui);
    draw_at(ui, ui->bg_cache, 0, 0, DESIGN_W, DESIGN_H);

    for (i = 0; i < NUM_CTRL; i++) {
        const Control *c = &CTRL[i];
        float v = ui->value[i];

        if (c->kind == BUTTON) {
            int on = v >= 0.5f;
            draw_at(ui, ui->btn[on ? 1 : 0], c->x, c->y, BTN_W, BTN_H);
        } else {
            float frac = (v - c->min) / (c->max - c->min);
            int   f = (int)(frac * (ui->nframes - 1) + 0.5f);

            if (f < 0) f = 0;
            if (f >= ui->nframes) f = ui->nframes - 1;
            draw_at(ui, ui->knob[f], c->x, c->y, KNOB_SIZE, KNOB_SIZE);
        }
    }

    imlib_context_set_image(ui->back);
    imlib_context_set_drawable(ui->win);
    imlib_render_image_on_drawable(0, 0);
    XFlush(ui->dpy);
}

/* ---------- mouse handling ---------- */

static int knob_at(const NHEUI *ui, int x, int y)
{
    double dx, dy;
    int    i;

    to_design(ui, x, y, &dx, &dy);
    for (i = 0; i < NUM_CTRL; i++) {
        const Control *c = &CTRL[i];
        if (c->kind == KNOB && inside(dx, dy, c->x, c->y, KNOB_SIZE, KNOB_SIZE)) {
            return i;
        }
    }
    return -1;
}

static int button_at(const NHEUI *ui, int x, int y)
{
    double dx, dy;
    int    i;

    to_design(ui, x, y, &dx, &dy);
    for (i = 0; i < NUM_CTRL; i++) {
        const Control *c = &CTRL[i];
        if (c->kind == BUTTON && inside(dx, dy, c->x, c->y, BTN_W, BTN_H)) {
            return i;
        }
    }
    return -1;
}

static void on_press(NHEUI *ui, int x, int y)
{
    int i = knob_at(ui, x, y);

    if (i >= 0) {
        ui->dragging   = i;
        ui->drag_y     = y;
        ui->drag_start = ui->value[i];
        return;
    }

    i = button_at(ui, x, y);
    if (i >= 0) {
        set_value(ui, i, ui->value[i] >= 0.5f ? 0.0f : 1.0f);
    }
}

static void on_motion(NHEUI *ui, int y)
{
    const Control *c;
    float          range;

    if (ui->dragging < 0) {
        return;
    }
    c = &CTRL[ui->dragging];
    range = c->max - c->min;

    /* 150 design px of drag cover the full range, at any window size */
    set_value(ui, ui->dragging,
              ui->drag_start + (float)((ui->drag_y - y) / ui->scale) * range / 150.0f);
}

static void on_wheel(NHEUI *ui, int x, int y, int up)
{
    int   i = knob_at(ui, x, y);
    float step;

    if (i < 0) {
        return;
    }
    step = (CTRL[i].max - CTRL[i].min) / 100.0f;
    if (step < 1.0f) {
        step = 1.0f;
    }
    set_value(ui, i, ui->value[i] + (up ? step : -step));
}

/* ---------- LV2 UI callbacks ---------- */

static LV2UI_Handle instantiate(const LV2UI_Descriptor *descriptor,
                                const char *plugin_uri,
                                const char *bundle_path,
                                LV2UI_Write_Function write_function,
                                LV2UI_Controller controller,
                                LV2UI_Widget *widget,
                                const LV2_Feature *const *features)
{
    NHEUI  *ui;
    Window  parent = 0;
    int     screen, i;

    (void)descriptor;
    (void)plugin_uri;

    for (i = 0; features && features[i]; i++) {
        if (!strcmp(features[i]->URI, URI_PARENT)) {
            parent = (Window)(uintptr_t)features[i]->data;
        }
    }
    if (!parent || !bundle_path) {
        return NULL;
    }

    ui = calloc(1, sizeof *ui);
    if (!ui) {
        return NULL;
    }

    ui->write      = write_function;
    ui->controller = controller;
    ui->parent     = parent;
    ui->dragging   = -1;
    for (i = 0; i < NUM_CTRL; i++) {
        ui->value[i] = CTRL[i].def;
    }

    ui->dpy = XOpenDisplay(NULL);
    if (!ui->dpy) {
        free(ui);
        return NULL;
    }
    screen = DefaultScreen(ui->dpy);

    if (load_assets(ui, bundle_path) != 0) {
        free_assets(ui);
        XCloseDisplay(ui->dpy);
        free(ui);
        return NULL;
    }

    ui->win_w = DESIGN_W;
    ui->win_h = DESIGN_H;
    update_layout(ui);
    ensure_back(ui);

    ui->win = XCreateSimpleWindow(ui->dpy, parent, 0, 0, ui->win_w, ui->win_h, 0,
                                  BlackPixel(ui->dpy, screen),
                                  WhitePixel(ui->dpy, screen));
    XSetWindowBackgroundPixmap(ui->dpy, ui->win, None);
    XSelectInput(ui->dpy, ui->win,
                 ExposureMask | ButtonPressMask | ButtonReleaseMask |
                 PointerMotionMask);
    XMapWindow(ui->dpy, ui->win);
    XFlush(ui->dpy);

    *widget = (LV2UI_Widget)(uintptr_t)ui->win;
    return ui;
}

static void cleanup(LV2UI_Handle handle)
{
    NHEUI *ui = (NHEUI *)handle;

    free_assets(ui);
    if (ui->dpy) {
        XDestroyWindow(ui->dpy, ui->win);
        XCloseDisplay(ui->dpy);
    }
    free(ui);
}

/* Called by the host when a control value changes (e.g. preset loaded). */
static void port_event(LV2UI_Handle handle,
                       uint32_t port_index,
                       uint32_t buffer_size,
                       uint32_t format,
                       const void *buffer)
{
    NHEUI *ui = (NHEUI *)handle;
    int    i;

    if (format != 0 || buffer_size != sizeof(float) || !buffer) {
        return;
    }

    for (i = 0; i < NUM_CTRL; i++) {
        if (CTRL[i].port + NHE_PORT_OFFSET == port_index) {
            ui->value[i] = *(const float *)buffer;
            ui->dirty = 1;
            return;
        }
    }
}

/* Called regularly by the host: follow the window size, process X events. */
static int ui_idle(LV2UI_Handle handle)
{
    NHEUI *ui = (NHEUI *)handle;
    XEvent ev;

    sync_size(ui);

    while (XPending(ui->dpy)) {
        XNextEvent(ui->dpy, &ev);

        switch (ev.type) {
        case Expose:
            if (ev.xexpose.count == 0) {
                ui->dirty = 1;
            }
            break;

        case ButtonPress:
            if (ev.xbutton.button == Button1) {
                on_press(ui, ev.xbutton.x, ev.xbutton.y);
                ui->dirty = 1;
            } else if (ev.xbutton.button == Button4) {
                on_wheel(ui, ev.xbutton.x, ev.xbutton.y, 1);
                ui->dirty = 1;
            } else if (ev.xbutton.button == Button5) {
                on_wheel(ui, ev.xbutton.x, ev.xbutton.y, 0);
                ui->dirty = 1;
            }
            break;

        case ButtonRelease:
            if (ev.xbutton.button == Button1) {
                ui->dragging = -1;
            }
            break;

        case MotionNotify:
            if (ui->dragging >= 0) {
                on_motion(ui, ev.xmotion.y);
                ui->dirty = 1;
            }
            break;

        default:
            break;
        }
    }

    if (ui->dirty) {
        ui->dirty = 0;
        draw(ui);
    }
    XFlush(ui->dpy);
    return 0;   /* non-zero would ask the host to close the UI */
}

static int ui_show(LV2UI_Handle handle)
{
    NHEUI *ui = (NHEUI *)handle;

    XMapRaised(ui->dpy, ui->win);
    XFlush(ui->dpy);
    return 0;
}

static int ui_hide(LV2UI_Handle handle)
{
    NHEUI *ui = (NHEUI *)handle;

    XUnmapWindow(ui->dpy, ui->win);
    XFlush(ui->dpy);
    return 0;
}

static const LV2UI_Idle_Interface idle_iface = { ui_idle };
static const LV2UI_Show_Interface show_iface = { ui_show, ui_hide };

static const void *extension_data(const char *uri)
{
    if (!strcmp(uri, URI_IDLE)) {
        return &idle_iface;
    }
    if (!strcmp(uri, URI_SHOW)) {
        return &show_iface;
    }
    return NULL;
}

static const LV2UI_Descriptor descriptor = {
    NHE_UI_URI,
    instantiate,
    cleanup,
    port_event,
    extension_data
};

LV2_SYMBOL_EXPORT const LV2UI_Descriptor *lv2ui_descriptor(uint32_t index)
{
    return index == 0 ? &descriptor : NULL;
}
