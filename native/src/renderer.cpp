#include "renderer.h"

#ifdef _WIN32
#include <windows.h>
#include <GL/gl.h>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>

class Win32OpenGLRenderer final : public Renderer {
public:
    bool create(int width, int height, const char* title) override {
        width_ = width > 0 ? width : 1280;
        height_ = height > 0 ? height : 720;

        WNDCLASSA wc{};
        wc.style = CS_OWNDC;
        wc.lpfnWndProc = &Win32OpenGLRenderer::window_proc;
        wc.hInstance = GetModuleHandleA(nullptr);
        wc.lpszClassName = "Paralox3DWindow";
        wc.hCursor = LoadCursor(nullptr, IDC_ARROW);

        if (!RegisterClassA(&wc) && GetLastError() != ERROR_CLASS_ALREADY_EXISTS)
            return false;

        hwnd_ = CreateWindowExA(
            0, wc.lpszClassName, title ? title : "Paralox3D",
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT, CW_USEDEFAULT, width_, height_,
            nullptr, nullptr, wc.hInstance, this
        );
        if (!hwnd_) return false;

        hdc_ = GetDC(hwnd_);

        PIXELFORMATDESCRIPTOR pfd{};
        pfd.nSize = sizeof(pfd);
        pfd.nVersion = 1;
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
        pfd.iPixelType = PFD_TYPE_RGBA;
        pfd.cColorBits = 32;
        pfd.cDepthBits = 24;
        pfd.cStencilBits = 8;
        pfd.iLayerType = PFD_MAIN_PLANE;

        const int format = ChoosePixelFormat(hdc_, &pfd);
        if (!format || !SetPixelFormat(hdc_, format, &pfd))
            return false;

        hglrc_ = wglCreateContext(hdc_);
        if (!hglrc_ || !wglMakeCurrent(hdc_, hglrc_))
            return false;

        glEnable(GL_DEPTH_TEST);
        glClearColor(0.08f, 0.10f, 0.14f, 1.0f);
        resize(width_, height_);
        running_ = true;
        return true;
    }

    bool begin_frame() override {
        if (!running_) return false;
        MSG msg;
        while (PeekMessageA(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) {
                running_ = false;
                return false;
            }
            TranslateMessage(&msg);
            DispatchMessageA(&msg);
        }
        if (!running_) return false;
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();

        if (camera_enabled_) {
            glRotatef(-camera_pitch_, 1.0f, 0.0f, 0.0f);
            glRotatef(-camera_yaw_, 0.0f, 1.0f, 0.0f);
            glRotatef(-camera_roll_, 0.0f, 0.0f, 1.0f);
            glTranslatef(-camera_x_, -camera_y_, -camera_z_);
        }

        glScalef(1.0f, 1.0f, -1.0f);
        return true;
    }

    void draw_cube(float x, float y, float z) override {
        const float s = 0.5f;
        glPushMatrix();
        glTranslatef(x, y, z);
        glBegin(GL_QUADS);

        glColor3f(0.15f, 0.65f, 1.0f);
        glVertex3f(-s,-s,s); glVertex3f(s,-s,s); glVertex3f(s,s,s); glVertex3f(-s,s,s);

        glColor3f(0.10f, 0.45f, 0.80f);
        glVertex3f(s,-s,-s); glVertex3f(-s,-s,-s); glVertex3f(-s,s,-s); glVertex3f(s,s,-s);

        glColor3f(0.12f, 0.55f, 0.90f);
        glVertex3f(-s,-s,-s); glVertex3f(-s,-s,s); glVertex3f(-s,s,s); glVertex3f(-s,s,-s);

        glColor3f(0.20f, 0.75f, 1.0f);
        glVertex3f(s,-s,s); glVertex3f(s,-s,-s); glVertex3f(s,s,-s); glVertex3f(s,s,s);

        glColor3f(0.30f, 0.85f, 1.0f);
        glVertex3f(-s,s,s); glVertex3f(s,s,s); glVertex3f(s,s,-s); glVertex3f(-s,s,-s);

        glColor3f(0.08f, 0.35f, 0.65f);
        glVertex3f(-s,-s,-s); glVertex3f(s,-s,-s); glVertex3f(s,-s,s); glVertex3f(-s,-s,s);

        glEnd();
        glPopMatrix();
    }

    void end_frame() override {
        SwapBuffers(hdc_);
        if (developer_overlay_) draw_developer_overlay();
    }

    bool running() const override { return running_; }

    void camera_set_enabled(bool enabled) override { camera_enabled_ = enabled; }

    void camera_set_transform(float x, float y, float z, float pitch, float yaw, float roll) override {
        camera_x_ = x; camera_y_ = y; camera_z_ = z;
        camera_pitch_ = pitch; camera_yaw_ = yaw; camera_roll_ = roll;
    }

    bool key_held(int key_code) const override {
        if (key_code < 0 || key_code > 255) return false;
        return (GetAsyncKeyState(key_code) & 0x8000) != 0;
    }

    void set_developer_overlay(bool enabled, int object_count, float fps,
                               const char* current_task, int warning_count) override {
        developer_overlay_ = enabled;
        object_count_ = object_count;
        fps_ = fps;
        warning_count_ = warning_count;
        current_task_ = current_task ? current_task : "Idle";
    }

    bool diagnostics_clicked() override {
        const bool clicked = diagnostics_clicked_;
        diagnostics_clicked_ = false;
        return clicked;
    }

    ~Win32OpenGLRenderer() override {
        if (hglrc_) { wglMakeCurrent(nullptr, nullptr); wglDeleteContext(hglrc_); }
        if (hdc_ && hwnd_) ReleaseDC(hwnd_, hdc_);
        if (hwnd_) DestroyWindow(hwnd_);
    }

private:
    void draw_text(HDC dc, int x, int y, const char* text, COLORREF color) {
        SetTextColor(dc, color);
        SetBkMode(dc, TRANSPARENT);
        TextOutA(dc, x, y, text, static_cast<int>(std::strlen(text)));
    }

    void draw_developer_overlay() {
        HDC dc = GetDC(hwnd_);
        if (!dc) return;

        HFONT font = CreateFontA(16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
            DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, "Consolas");
        HFONT old_font = static_cast<HFONT>(SelectObject(dc, font));

        char line[128];
        std::snprintf(line, sizeof(line), "Objects: %d", object_count_);
        draw_text(dc, width_ - 140, 20, line, RGB(235, 235, 235));
        std::snprintf(line, sizeof(line), "FPS: %.1f", fps_);
        draw_text(dc, width_ - 140, 42, line, RGB(235, 235, 235));

        const int button_w = 112, button_h = 28;
        const int button_x = width_ - button_w - 18, button_y = 16;
        RECT button{button_x, button_y, button_x + button_w, button_y + button_h};
        FillRect(dc, &button, static_cast<HBRUSH>(GetStockObject(BLACK_BRUSH)));
        FrameRect(dc, &button, static_cast<HBRUSH>(GetStockObject(WHITE_BRUSH)));
        draw_text(dc, button_x + 10, button_y + 6, "Diagnostics", RGB(255, 255, 255));

        if (diagnostics_open_) {
            const int panel_w = 360, panel_h = 150;
            const int panel_x = width_ - panel_w - 18, panel_y = 52;
            RECT panel{panel_x, panel_y, panel_x + panel_w, panel_y + panel_h};
            FillRect(dc, &panel, static_cast<HBRUSH>(GetStockObject(BLACK_BRUSH)));
            FrameRect(dc, &panel, static_cast<HBRUSH>(GetStockObject(WHITE_BRUSH)));

            draw_text(dc, panel_x + 12, panel_y + 12, "Paralox3D Diagnostics", RGB(255, 255, 255));
            std::snprintf(line, sizeof(line), "Currently doing: %s", current_task_.c_str());
            draw_text(dc, panel_x + 12, panel_y + 38, line, RGB(225, 225, 225));
            std::snprintf(line, sizeof(line), "Objects: %d", object_count_);
            draw_text(dc, panel_x + 12, panel_y + 62, line, RGB(225, 225, 225));
            std::snprintf(line, sizeof(line), "FPS: %.1f", fps_);
            draw_text(dc, panel_x + 12, panel_y + 86, line, RGB(225, 225, 225));
            std::snprintf(line, sizeof(line), "Warnings: %d", warning_count_);
            draw_text(dc, panel_x + 12, panel_y + 110, line,
                warning_count_ ? RGB(255, 210, 80) : RGB(140, 255, 140));
        }

        SelectObject(dc, old_font);
        DeleteObject(font);
        ReleaseDC(hwnd_, dc);
    }

    void resize(int width, int height) {
        if (height <= 0) height = 1;
        glViewport(0, 0, width, height);
        const float aspect = static_cast<float>(width) / height;
        const float near_plane = 0.1f;
        const float far_plane = 1000.0f;
        const float top = near_plane * std::tan(60.0f * 3.14159265f / 360.0f);
        const float right = top * aspect;
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        glFrustum(-right, right, -top, top, near_plane, far_plane);
    }

    static LRESULT CALLBACK window_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
        auto* self = reinterpret_cast<Win32OpenGLRenderer*>(
            GetWindowLongPtrA(hwnd, GWLP_USERDATA));
        if (msg == WM_NCCREATE) {
            auto* cs = reinterpret_cast<CREATESTRUCTA*>(lparam);
            self = static_cast<Win32OpenGLRenderer*>(cs->lpCreateParams);
            SetWindowLongPtrA(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(self));
            self->hwnd_ = hwnd;
        }
        if (self) {
            if (msg == WM_CLOSE) {
                self->running_ = false;
                DestroyWindow(hwnd);
                return 0;
            }
            if (msg == WM_DESTROY) {
                PostQuitMessage(0);
                return 0;
            }
            if (msg == WM_LBUTTONDOWN && self->camera_enabled_) {
                SetCapture(hwnd);
                self->left_drag_ = true;
                self->last_mouse_x_ = static_cast<int>(static_cast<short>(LOWORD(lparam)));
                self->last_mouse_y_ = static_cast<int>(static_cast<short>(HIWORD(lparam)));
                return 0;
            }
            if (msg == WM_RBUTTONDOWN && self->camera_enabled_) {
                SetCapture(hwnd);
                self->right_drag_ = true;
                self->last_mouse_x_ = static_cast<int>(static_cast<short>(LOWORD(lparam)));
                self->last_mouse_y_ = static_cast<int>(static_cast<short>(HIWORD(lparam)));
                return 0;
            }
            if (msg == WM_LBUTTONUP) {
                self->left_drag_ = false;
                if (!self->right_drag_) ReleaseCapture();
                return 0;
            }
            if (msg == WM_RBUTTONUP) {
                self->right_drag_ = false;
                if (!self->left_drag_) ReleaseCapture();
                return 0;
            }
            if (msg == WM_MOUSEMOVE && self->camera_enabled_ &&
                (self->left_drag_ || self->right_drag_)) {
                const int x = static_cast<int>(static_cast<short>(LOWORD(lparam)));
                const int y = static_cast<int>(static_cast<short>(HIWORD(lparam)));
                const float dx = static_cast<float>(x - self->last_mouse_x_);
                const float dy = static_cast<float>(y - self->last_mouse_y_);
                self->last_mouse_x_ = x;
                self->last_mouse_y_ = y;

                if (self->left_drag_) {
                    self->camera_yaw_ += dx * 0.20f;
                    self->camera_pitch_ += dy * 0.20f;
                    if (self->camera_pitch_ > 89.0f) self->camera_pitch_ = 89.0f;
                    if (self->camera_pitch_ < -89.0f) self->camera_pitch_ = -89.0f;
                }
                if (self->right_drag_) {
                    self->camera_x_ -= dx * 0.005f;
                    self->camera_y_ += dy * 0.005f;
                }
                return 0;
            }
            if (msg == WM_LBUTTONDOWN && self->developer_overlay_) {
                const int x = LOWORD(lparam);
                const int y = HIWORD(lparam);
                const int button_w = 112, button_h = 28;
                const int button_x = self->width_ - button_w - 18, button_y = 16;
                if (x >= button_x && x <= button_x + button_w &&
                    y >= button_y && y <= button_y + button_h) {
                    self->diagnostics_open_ = !self->diagnostics_open_;
                    self->diagnostics_clicked_ = true;
                    return 0;
                }
            }
            if (msg == WM_SIZE && self->hglrc_) {
                const int w = LOWORD(lparam), h = HIWORD(lparam);
                if (w && h) self->resize(w, h);
                return 0;
            }
        }
        return DefWindowProcA(hwnd, msg, wparam, lparam);
    }

    HWND hwnd_ = nullptr;
    HDC hdc_ = nullptr;
    HGLRC hglrc_ = nullptr;
    int width_ = 1280, height_ = 720;
    bool running_ = false;
    bool developer_overlay_ = false;
    bool diagnostics_open_ = false;
    bool diagnostics_clicked_ = false;
    int object_count_ = 0;
    float fps_ = 0.0f;
    int warning_count_ = 0;
    std::string current_task_ = "Idle";

    bool camera_enabled_ = false;
    float camera_x_ = 0.0f, camera_y_ = 0.0f, camera_z_ = 0.0f;
    float camera_pitch_ = 0.0f, camera_yaw_ = 0.0f, camera_roll_ = 0.0f;
    bool left_drag_ = false, right_drag_ = false;
    int last_mouse_x_ = 0, last_mouse_y_ = 0;
};

#endif

Renderer* create_platform_renderer() {
#ifdef _WIN32
    return new Win32OpenGLRenderer();
#else
    return nullptr;
#endif
}
