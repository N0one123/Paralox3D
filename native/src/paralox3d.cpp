#include "paralox3d.h"
#include "renderer.h"

#include <cstdint>
#include <memory>
#include <vector>

struct Transform { float x=0.0f,y=0.0f,z=0.0f; float sx=1.0f,sy=1.0f,sz=1.0f; float pitch=0.0f,yaw=0.0f,roll=0.0f; float r=1.0f,g=1.0f,b=1.0f,a=1.0f; bool enabled=true,visible=true; };

struct P3DEngine {
    int width=1280, height=720;
    std::vector<Transform> transforms;
    std::unique_ptr<Renderer> renderer;
    bool running=false;
};

extern "C" {

P3DEngine* p3d_engine_create(int width, int height, const char* title) {
    auto* engine = new P3DEngine{};
    engine->width = width;
    engine->height = height;
    engine->transforms.reserve(1024);
    engine->renderer.reset(create_platform_renderer());
    if (!engine->renderer || !engine->renderer->create(width, height, title)) {
        delete engine;
        return nullptr;
    }
    engine->running = true;
    return engine;
}

void p3d_engine_destroy(P3DEngine* engine) { delete engine; }

uint32_t p3d_entity_create(P3DEngine* engine) {
    if (!engine) return 0;
    engine->transforms.emplace_back();
    return static_cast<uint32_t>(engine->transforms.size());
}

void p3d_entity_set_position(P3DEngine* engine, uint32_t entity,
                             float x, float y, float z) {
    if (!engine || entity == 0 || entity > engine->transforms.size()) return;
    auto& t = engine->transforms[entity - 1];
    t.x=x; t.y=y; t.z=z;
}

void p3d_entity_set_rotation(P3DEngine* engine,uint32_t entity,float pitch,float yaw,float roll){ if(!engine||!entity||entity>engine->transforms.size())return; auto& t=engine->transforms[entity-1];t.pitch=pitch;t.yaw=yaw;t.roll=roll; }\nvoid p3d_entity_set_color(P3DEngine* engine,uint32_t entity,float r,float g,float b,float a){ if(!engine||!entity||entity>engine->transforms.size())return; auto& t=engine->transforms[entity-1];t.r=r;t.g=g;t.b=b;t.a=a; }\nvoid p3d_entity_set_enabled(P3DEngine* engine,uint32_t entity,int enabled,int visible){ if(!engine||!entity||entity>engine->transforms.size())return; auto& t=engine->transforms[entity-1];t.enabled=enabled!=0;t.visible=visible!=0; }\nvoid p3d_mouse_state(P3DEngine* engine,float* x,float* y,int* buttons){ if(!engine||!engine->renderer)return;engine->renderer->mouse_state(*x,*y,*buttons); }\nvoid p3d_entity_set_scale(P3DEngine* engine, uint32_t entity, float x, float y, float z) {
    if (!engine || entity == 0 || entity > engine->transforms.size()) return;
    auto& t = engine->transforms[entity - 1];
    t.sx=x; t.sy=y; t.sz=z;
}

void p3d_camera_set_enabled(P3DEngine* engine, int enabled) {
    if (!engine || !engine->renderer) return;
    engine->renderer->camera_set_enabled(enabled != 0);
}

void p3d_camera_set_transform(P3DEngine* engine, float x, float y, float z, float pitch, float yaw, float roll) {
    if (!engine || !engine->renderer) return;
    engine->renderer->camera_set_transform(x, y, z, pitch, yaw, roll);
}

int p3d_input_key_held(P3DEngine* engine, int key_code) {
    if (!engine || !engine->renderer) return 0;
    return engine->renderer->key_held(key_code) ? 1 : 0;
}

void p3d_engine_set_developer_overlay(P3DEngine* engine, int enabled, int object_count,
                                      float fps, const char* current_task, int warning_count) {
    if (!engine || !engine->renderer) return;
    engine->renderer->set_developer_overlay(
        enabled != 0, object_count, fps, current_task, warning_count);
}

int p3d_engine_diagnostics_clicked(P3DEngine* engine) {
    if (!engine || !engine->renderer) return 0;
    return engine->renderer->diagnostics_clicked() ? 1 : 0;
}

void p3d_engine_set_debug_colliders(P3DEngine* engine, const float* bounds, int count) {
    if (!engine || !engine->renderer) return;
    engine->renderer->set_debug_colliders(bounds, count);
}

int p3d_engine_step(P3DEngine* engine) {
    if (!engine || !engine->running || !engine->renderer) return 0;
    if (!engine->renderer->begin_frame()) {
        engine->running = false;
        return 0;
    }
    for (const auto& t : engine->transforms)
        engine->renderer->draw_cube(t.x, t.y, t.z, t.sx, t.sy, t.sz);
    engine->renderer->end_frame();
    engine->running = engine->renderer->running();
    return engine->running ? 1 : 0;
}

}
