#pragma once

#include <stdint.h>

#ifdef _WIN32
    #ifdef V3D_BUILD
        #define V3D_API __declspec(dllexport)
    #else
        #define V3D_API __declspec(dllimport)
    #endif
#else
    #define V3D_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct V3DEngine V3DEngine;

V3D_API V3DEngine* v3d_engine_create(int width, int height, const char* title);
V3D_API void v3d_engine_destroy(V3DEngine* engine);

V3D_API uint32_t v3d_entity_create(V3DEngine* engine);
V3D_API void v3d_entity_set_position(
    V3DEngine* engine,
    uint32_t entity,
    float x,
    float y,
    float z
);

/* Returns 1 while the engine should continue running, 0 when it should stop. */
V3D_API int v3d_engine_step(V3DEngine* engine);

#ifdef __cplusplus
}
#endif
