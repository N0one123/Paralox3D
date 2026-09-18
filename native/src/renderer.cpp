#include "renderer.h"

#ifdef _WIN32
#include <windows.h>
#include <GL/gl.h>
#include <cmath>

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

    void end_frame() override { SwapBuffers(hdc_); }
    bool running() const override { return running_; }

    ~Win32OpenGLRenderer() override {
        if (hglrc_) { wglMakeCurrent(nullptr, nullptr); wglDeleteContext(hglrc_); }
        if (hdc_ && hwnd_) ReleaseDC(hwnd_, hdc_);
        if (hwnd_) DestroyWindow(hwnd_);
    }

private:
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
};

#endif

Renderer* create_platform_renderer() {
#ifdef _WIN32
    return new Win32OpenGLRenderer();
#else
    return nullptr;
#endif
}
