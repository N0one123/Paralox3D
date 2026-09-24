#pragma once

#include <stdint.h>

#ifdef _WIN32
    #ifdef P3D_BUILD
        #define P3D_API __declspec(dllexport)
    #else
        #define P3D_API __declspec(dllimport)
    #endif
#else
    #define P3D_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct P3DEngine P3DEngine;

P3D_API P3DEngine* p3d_engine_create(int width, int height, const char* title);
P3D_API void p3d_engine_destroy(P3DEngine* engine);
P3D_API uint32_t p3d_entity_create(P3DEngine* engine);
P3D_API void p3d_entity_set_position(P3DEngine* engine, uint32_t entity, float x, float y, float z);
P3D_API int p3d_input_key_held(P3DEngine* engine, int key_code);
P3D_API void p3d_camera_set_enabled(P3DEngine* engine, int enabled);
P3D_API void p3d_camera_set_transform(P3DEngine* engine, float x, float y, float z, float pitch, float yaw, float roll);
P3D_API void p3d_engine_set_developer_overlay(P3DEngine* engine, int enabled, int object_count,
                                              float fps, const char* current_task, int warning_count);
P3D_API int p3d_engine_diagnostics_clicked(P3DEngine* engine);
P3D_API int p3d_engine_step(P3DEngine* engine);

#ifdef __cplusplus
}
#endif
