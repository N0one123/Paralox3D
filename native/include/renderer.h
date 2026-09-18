#pragma once

class Renderer {
public:
    virtual ~Renderer() = default;
    virtual bool create(int width, int height, const char* title) = 0;
    virtual bool begin_frame() = 0;
    virtual void draw_cube(float x, float y, float z) = 0;
    virtual void end_frame() = 0;
    virtual bool running() const = 0;
};

Renderer* create_platform_renderer();
