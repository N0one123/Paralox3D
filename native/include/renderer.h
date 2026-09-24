#pragma once

class Renderer {
public:
    virtual ~Renderer() = default;
    virtual bool create(int width, int height, const char* title) = 0;
    virtual bool begin_frame() = 0;
    virtual void draw_cube(float x, float y, float z, float sx, float sy, float sz) = 0;
    virtual void end_frame() = 0;
    virtual bool running() const = 0;
    virtual bool key_held(int key_code) const = 0;
    virtual void camera_set_enabled(bool enabled) = 0;
    virtual void camera_set_transform(float x, float y, float z, float pitch, float yaw, float roll) = 0;
    virtual void set_developer_overlay(bool enabled, int object_count, float fps,
                                        const char* current_task, int warning_count) = 0;
    virtual bool diagnostics_clicked() = 0;
    virtual void set_debug_colliders(const float* bounds, int count) = 0;
};

Renderer* create_platform_renderer();
