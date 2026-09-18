#include "vertex3d.h"

#include <vector>
#include <cstdint>
#include <memory>

struct Transform {
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct V3DEngine {
    int width;
    int height;
    std::vector<Transform> transforms;
    bool running = true;
};

extern "C" {

V3DEngine* v3d_engine_create(int width, int height, const char*) {
    auto* engine = new V3DEngine{};
    engine->width = width;
    engine->height = height;
    engine->transforms.reserve(1024);
    return engine;
}

void v3d_engine_destroy(V3DEngine* engine) {
    delete engine;
}

uint32_t v3d_entity_create(V3DEngine* engine) {
    if (!engine) return 0;
    engine->transforms.emplace_back();
    return static_cast<uint32_t>(engine->transforms.size());
}

void v3d_entity_set_position(
    V3DEngine* engine,
    uint32_t entity,
    float x,
    float y,
    float z
) {
    if (!engine || entity == 0 || entity > engine->transforms.size()) return;
    auto& t = engine->transforms[entity - 1];
    t.x = x;
    t.y = y;
    t.z = z;
}

int v3d_engine_step(V3DEngine* engine) {
    if (!engine || !engine->running) return 0;

    /*
     * Renderer/window/input backends will plug into this boundary.
     * Keeping the simulation step native from day one lets us add rendering
     * without redesigning the Python API.
     */
    return 0;
}

}
