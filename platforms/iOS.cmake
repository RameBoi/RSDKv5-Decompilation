enable_language(OBJCXX)

set(DEP_PATH ios)
set(RETRO_SUBSYSTEM "SDL2")
set(RETRO_OUTPUT_NAME "RSDKv5U")

set(IOS_GEN ${CMAKE_CURRENT_BINARY_DIR}/gen)
file(MAKE_DIRECTORY ${IOS_GEN}/ogg)

# ogg type header (generated, standard stdint version)
file(WRITE ${IOS_GEN}/ogg/config_types.h [=[
#ifndef __CONFIG_TYPES_H__
#define __CONFIG_TYPES_H__
#include <stdint.h>
typedef int16_t ogg_int16_t;
typedef uint16_t ogg_uint16_t;
typedef int32_t ogg_int32_t;
typedef uint32_t ogg_uint32_t;
typedef int64_t ogg_int64_t;
typedef uint64_t ogg_uint64_t;
#endif
]=])

# stubs for iOS 10+ UIKit methods that SDL calls but the 10.3 SDK does not declare
file(WRITE ${IOS_GEN}/ios_compat.h [=[
#ifdef __OBJC__
#import <UIKit/UIKit.h>
@interface UIViewController (iOS11CompatStubs)
- (void)setNeedsUpdateOfHomeIndicatorAutoHidden;
- (void)setNeedsUpdateOfScreenEdgesDeferringSystemGestures;
- (BOOL)prefersHomeIndicatorAutoHidden;
- (UIRectEdge)preferredScreenEdgesDeferringSystemGestures;
@end
#endif
]=])

# symbol the new libc++ headers call that iOS's old libc++ lacks
file(WRITE ${IOS_GEN}/ios_stubs.cpp [=[
extern "C" void abort(void);
namespace std { inline namespace __1 {
__attribute__((noreturn)) void __libcpp_verbose_abort(const char*, ...) { abort(); }
} }
]=])

add_compile_options("$<$<COMPILE_LANGUAGE:OBJC,OBJCXX>:-include;${IOS_GEN}/ios_compat.h>")

# SDL2 (static)
set(SDL_SHARED OFF CACHE BOOL "" FORCE)
set(SDL_STATIC ON CACHE BOOL "" FORCE)
set(SDL_TEST OFF CACHE BOOL "" FORCE)
add_subdirectory(dependencies/ios/SDL EXCLUDE_FROM_ALL)

# make <SDL2/SDL.h> resolve
file(MAKE_DIRECTORY ${IOS_GEN}/sdlinc)
file(CREATE_LINK ${CMAKE_CURRENT_SOURCE_DIR}/dependencies/ios/SDL/include ${IOS_GEN}/sdlinc/SDL2 SYMBOLIC)

# ogg
set(OGG_DIR ${CMAKE_CURRENT_SOURCE_DIR}/dependencies/ios/ogg)
add_library(iosogg STATIC ${OGG_DIR}/src/bitwise.c ${OGG_DIR}/src/framing.c)
target_include_directories(iosogg PRIVATE ${IOS_GEN} ${OGG_DIR}/include)
target_compile_options(iosogg PRIVATE -ffast-math -fsigned-char -O2 -DBYTE_ORDER=LITTLE_ENDIAN -w)

# theora (decoder)
set(THEORA_DIR ${CMAKE_CURRENT_SOURCE_DIR}/dependencies/ios/theora)
add_library(iostheora STATIC
    ${THEORA_DIR}/lib/analyze.c ${THEORA_DIR}/lib/apiwrapper.c ${THEORA_DIR}/lib/bitpack.c
    ${THEORA_DIR}/lib/cpu.c ${THEORA_DIR}/lib/decapiwrapper.c ${THEORA_DIR}/lib/decinfo.c
    ${THEORA_DIR}/lib/decode.c ${THEORA_DIR}/lib/dequant.c ${THEORA_DIR}/lib/encapiwrapper.c
    ${THEORA_DIR}/lib/encfrag.c ${THEORA_DIR}/lib/encinfo.c ${THEORA_DIR}/lib/encode.c
    ${THEORA_DIR}/lib/encoder_disabled.c ${THEORA_DIR}/lib/enquant.c ${THEORA_DIR}/lib/fdct.c
    ${THEORA_DIR}/lib/fragment.c ${THEORA_DIR}/lib/huffdec.c ${THEORA_DIR}/lib/huffenc.c
    ${THEORA_DIR}/lib/idct.c ${THEORA_DIR}/lib/info.c ${THEORA_DIR}/lib/internal.c
    ${THEORA_DIR}/lib/mathops.c ${THEORA_DIR}/lib/mcenc.c ${THEORA_DIR}/lib/quant.c
    ${THEORA_DIR}/lib/rate.c ${THEORA_DIR}/lib/state.c ${THEORA_DIR}/lib/tokenize.c)
target_include_directories(iostheora PRIVATE ${THEORA_DIR}/include ${IOS_GEN} ${OGG_DIR}/include)
target_compile_options(iostheora PRIVATE -ffast-math -fsigned-char -O2 -DBYTE_ORDER=LITTLE_ENDIAN -w)

# the app itself
add_executable(RetroEngine ${RETRO_FILES} RSDKv5/cocoaHelpers.mm ${IOS_GEN}/ios_stubs.cpp)
set_source_files_properties(RSDKv5/cocoaHelpers.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")

target_include_directories(RetroEngine PRIVATE
    ${IOS_GEN}/sdlinc ${CMAKE_CURRENT_SOURCE_DIR}/dependencies/ios/SDL/include
    ${IOS_GEN} ${OGG_DIR}/include ${THEORA_DIR}/include)

target_link_libraries(RetroEngine SDL2-static iostheora iosogg
    "-framework UIKit" "-framework Foundation" "-framework OpenGLES" "-framework QuartzCore"
    "-framework AudioToolbox" "-framework AVFoundation" "-framework GameController"
    "-framework CoreGraphics" "-framework CoreMotion" "-framework CoreAudio"
    "-framework CoreVideo" "-framework CoreBluetooth"
    -lc++ -lSystem)
