#include "paralox3d.h"
#include "renderer.h"

#include <cstdint>
#include <memory>
#include <vector>

struct Transform { float x=0.0f, y=0.0f, z=0.0f; };

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

int p3d_engine_step(P3DEngine* engine) {
    if (!engine || !engine->running || !engine->renderer) return 0;
    if (!engine->renderer->begin_frame()) {
        engine->running = false;
        return 0;
    }
    for (const auto& t : engine->transforms)
        engine->renderer->draw_cube(t.x, t.y, t.z);
    engine->renderer->end_frame();
    engine->running = engine->renderer->running();
    return engine->running ? 1 : 0;
}

}
