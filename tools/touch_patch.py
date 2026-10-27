import re

base = "Game/dependencies/RSDKv5/RSDKv5/RSDK/"


def patch(path, pattern, make):
    s = open(path, newline="").read()
    new, n = re.subn(pattern, make, s, flags=re.M)
    if n != 1:
        raise SystemExit("PATCH FAILED (%d matches) in %s for pattern %s" % (n, path, pattern))
    open(path, "w", newline="").write(new)


decl = r"""struct IOSCircle {
    float x, y, r;
};

extern IOSCircle iosLayout[12];
extern bool32 iosHeld[12];
extern bool32 iosDir[4];
extern bool32 iosStickOn;
extern float iosKnobX, iosKnobY;
extern float iosScale, iosOpacity;
extern float iosPos[4][2];
extern int32 iosHide, iosEdit, iosPadMode, iosDragIdx, iosFps, iosStrip;
extern int32 iosScreenW, iosScreenH;
void IOSComputeLayout();
void IOSTouchUpdate();
void ProcessInputReal();

"""

logic = r"""#include <math.h>
#include <stdio.h>

RSDK::IOSCircle RSDK::iosLayout[12];
bool32 RSDK::iosHeld[12] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
bool32 RSDK::iosDir[4]   = { 0, 0, 0, 0 };
bool32 RSDK::iosStickOn  = false;
float RSDK::iosKnobX     = 0;
float RSDK::iosKnobY     = 0;
float RSDK::iosScale     = 1.0f;
float RSDK::iosOpacity   = 0.45f;
float RSDK::iosPos[4][2] = { { -1, -1 }, { -1, -1 }, { -1, -1 }, { -1, -1 } };
int32 RSDK::iosHide      = 0;
int32 RSDK::iosEdit      = 0;
int32 RSDK::iosPadMode   = 0;
int32 RSDK::iosDragIdx   = -1;
int32 RSDK::iosFps       = 1;
int32 RSDK::iosStrip     = 1;
int32 RSDK::iosScreenW   = 2048;
int32 RSDK::iosScreenH   = 1536;

static void IOSCfgSave()
{
    char path[1100];
    snprintf(path, sizeof(path), "%s/touchcontrols.ini", getResourcesPath());
    FILE *f = fopen(path, "w");
    if (!f)
        return;
    fprintf(f, "scale=%.2f\nopacity=%.2f\nhide=%d\npad=%d\nfps=%d\nstrip=%d\n", RSDK::iosScale, RSDK::iosOpacity, (int)RSDK::iosHide, (int)RSDK::iosPadMode,
            (int)RSDK::iosFps, (int)RSDK::iosStrip);
    for (int i = 0; i < 4; ++i)
        fprintf(f, "pos%d=%.4f,%.4f\n", i, RSDK::iosPos[i][0], RSDK::iosPos[i][1]);
    fclose(f);
}

static void IOSCfgLoad()
{
    char path[1100];
    snprintf(path, sizeof(path), "%s/touchcontrols.ini", getResourcesPath());
    FILE *f = fopen(path, "r");
    if (!f) {
        IOSCfgSave();
        return;
    }
    char line[128];
    while (fgets(line, sizeof(line), f)) {
        float v = 0, w = 0;
        int i = 0;
        if (sscanf(line, "scale=%f", &v) == 1)
            RSDK::iosScale = v;
        else if (sscanf(line, "opacity=%f", &v) == 1)
            RSDK::iosOpacity = v;
        else if (sscanf(line, "hide=%f", &v) == 1)
            RSDK::iosHide = v > 0.5f ? 1 : 0;
        else if (sscanf(line, "pad=%f", &v) == 1)
            RSDK::iosPadMode = v > 0.5f ? 1 : 0;
        else if (sscanf(line, "fps=%f", &v) == 1)
            RSDK::iosFps = v > 0.5f ? 1 : 0;
        else if (sscanf(line, "strip=%f", &v) == 1)
            RSDK::iosStrip = v > 0.5f ? 1 : 0;
        else if (sscanf(line, "pos%d=%f,%f", &i, &v, &w) == 3 && i >= 0 && i < 4) {
            RSDK::iosPos[i][0] = v;
            RSDK::iosPos[i][1] = w;
        }
    }
    fclose(f);
    if (RSDK::iosScale < 0.5f)
        RSDK::iosScale = 0.5f;
    if (RSDK::iosScale > 2.0f)
        RSDK::iosScale = 2.0f;
    if (RSDK::iosOpacity < 0.1f)
        RSDK::iosOpacity = 0.1f;
    if (RSDK::iosOpacity > 1.0f)
        RSDK::iosOpacity = 1.0f;
}

void RSDK::IOSComputeLayout()
{
    float W = (float)iosScreenW;
    float H = (float)iosScreenH;
    float s = iosScale;
    float m = 0.05f * H;

    float rStick = 0.085f * H * s;
    float rA     = 0.065f * H * s;
    float rB     = 0.050f * H * s;
    float rStart = 0.032f * H * s;
    float rSmall = 0.026f * H;

    iosLayout[0].r = rStick;
    iosLayout[0].x = m + rStick * 1.5f;
    iosLayout[0].y = H - m - rStick * 1.5f;

    iosLayout[1].r = rA;
    iosLayout[1].x = W - m - rA * 1.4f;
    iosLayout[1].y = H - m - rA * 1.5f;

    iosLayout[2].r = rB;
    iosLayout[2].x = iosLayout[1].x - rA - rB * 1.5f;
    iosLayout[2].y = iosLayout[1].y + rA * 0.45f;

    iosLayout[3].r = rStart;
    iosLayout[3].x = W * 0.5f;
    iosLayout[3].y = m * 0.5f + rStart;

    for (int32 i = 0; i < 4; ++i) {
        if (iosPos[i][0] >= 0.0f && iosPos[i][1] >= 0.0f) {
            iosLayout[i].x = iosPos[i][0] * W;
            iosLayout[i].y = iosPos[i][1] * H;
        }
    }

    // top-right strip, right to left: handle, eye, plus, minus, move, pad-mode, fps
    float sy = m * 0.5f + rSmall;
    float sg = rSmall * 2.8f;
    iosLayout[10].x = W - m * 0.6f - rSmall;
    iosLayout[6].x  = iosLayout[10].x - sg;
    iosLayout[5].x  = iosLayout[6].x - sg;
    iosLayout[4].x  = iosLayout[5].x - sg;
    iosLayout[7].x  = iosLayout[4].x - sg;
    iosLayout[8].x  = iosLayout[7].x - sg;
    iosLayout[9].x  = iosLayout[8].x - sg;
    for (int32 i = 4; i < 11; ++i) {
        iosLayout[i].y = sy;
        iosLayout[i].r = rSmall;
    }
}

void RSDK::IOSTouchUpdate()
{
    static bool32 loaded     = false;
    static bool32 prev[12]   = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
    static bool32 prevDir[4] = { 0, 0, 0, 0 };
    static int32 prevMask    = 0;
    static float dragOffX    = 0;
    static float dragOffY    = 0;
    if (!loaded) {
        loaded = true;
        IOSCfgLoad();
    }

    IOSComputeLayout();
    float W = (float)iosScreenW;
    float H = (float)iosScreenH;

    bool32 now[12] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
    bool32 dir[4]  = { 0, 0, 0, 0 }; // up, down, left, right
    bool32 stickOn = false;
    float knobX    = iosLayout[0].x;
    float knobY    = iosLayout[0].y;
    int32 firstTouch = -1;

    for (int32 t = 0; t < touchInfo.count; ++t) {
        if (!touchInfo.down[t])
            continue;
        if (firstTouch < 0)
            firstTouch = t;
        float px = touchInfo.x[t] * W;
        float py = touchInfo.y[t] * H;

        for (int32 b = 1; b < 11; ++b) {
            if (b >= 4 && b <= 9 && !iosStrip)
                continue;
            if (iosHide && b != 6 && b != 10)
                continue;
            if (iosEdit && b < 4)
                continue;
            float dx    = px - iosLayout[b].x;
            float dy    = py - iosLayout[b].y;
            float reach = iosLayout[b].r * (b >= 4 ? 1.7f : 1.3f);
            if (dx * dx + dy * dy <= reach * reach)
                now[b] = true;
        }

        if (!iosHide && !iosEdit && !stickOn) {
            float dx    = px - iosLayout[0].x;
            float dy    = py - iosLayout[0].y;
            float reach = iosLayout[0].r * (iosPadMode ? 1.9f : 2.4f);
            if (dx * dx + dy * dy <= reach * reach) {
                stickOn    = true;
                float rr   = iosLayout[0].r;
                float dist = sqrtf(dx * dx + dy * dy);
                float kmax = rr * 0.9f;
                float k    = dist > kmax ? kmax / dist : 1.0f;
                knobX      = iosLayout[0].x + dx * k;
                knobY      = iosLayout[0].y + dy * k;
                if (!iosPadMode) {
                    float thrH = rr * 0.3f;
                    float thrV = rr * 0.5f;
                    if (dx < -thrH)
                        dir[2] = true;
                    if (dx > thrH)
                        dir[3] = true;
                    if (dy < -thrV)
                        dir[0] = true;
                    if (dy > thrV)
                        dir[1] = true;
                }
                else {
                    float ax = fabsf(dx);
                    float ay = fabsf(dy);
                    float dz = rr * 0.22f;
                    if (ax > dz && ax > ay * 0.42f) {
                        if (dx < 0)
                            dir[2] = true;
                        else
                            dir[3] = true;
                    }
                    if (ay > dz && ay > ax * 0.42f) {
                        if (dy < 0)
                            dir[0] = true;
                        else
                            dir[1] = true;
                    }
                }
            }
        }
    }

    // drag controls around while in move mode
    if (iosEdit && !iosHide && firstTouch >= 0) {
        float px = touchInfo.x[firstTouch] * W;
        float py = touchInfo.y[firstTouch] * H;
        if (iosDragIdx < 0) {
            float best = 1e18f;
            for (int32 b = 0; b < 4; ++b) {
                float dx    = px - iosLayout[b].x;
                float dy    = py - iosLayout[b].y;
                float reach = iosLayout[b].r * (b == 0 ? 2.0f : 1.4f);
                float d2    = dx * dx + dy * dy;
                if (d2 <= reach * reach && d2 < best) {
                    best        = d2;
                    iosDragIdx  = b;
                }
            }
            if (iosDragIdx >= 0) {
                dragOffX = iosLayout[iosDragIdx].x - px;
                dragOffY = iosLayout[iosDragIdx].y - py;
            }
        }
        if (iosDragIdx >= 0) {
            float nx = (px + dragOffX) / W;
            float ny = (py + dragOffY) / H;
            if (nx < 0.03f)
                nx = 0.03f;
            if (nx > 0.97f)
                nx = 0.97f;
            if (ny < 0.03f)
                ny = 0.03f;
            if (ny > 0.97f)
                ny = 0.97f;
            iosPos[iosDragIdx][0] = nx;
            iosPos[iosDragIdx][1] = ny;
        }
    }
    else if (iosDragIdx >= 0) {
        iosDragIdx = -1;
        IOSCfgSave();
    }

    if (now[4] && !prev[4]) {
        iosScale -= 0.1f;
        if (iosScale < 0.5f)
            iosScale = 0.5f;
        IOSCfgSave();
    }
    if (now[5] && !prev[5]) {
        iosScale += 0.1f;
        if (iosScale > 2.0f)
            iosScale = 2.0f;
        IOSCfgSave();
    }
    if (now[6] && !prev[6]) {
        iosHide = iosHide ? 0 : 1;
        if (iosHide)
            iosEdit = 0;
        IOSCfgSave();
    }
    if (now[7] && !prev[7]) {
        iosEdit = iosEdit ? 0 : 1;
        if (!iosEdit)
            IOSCfgSave();
    }
    if (now[8] && !prev[8]) {
        iosPadMode = iosPadMode ? 0 : 1;
        IOSCfgSave();
    }
    if (now[9] && !prev[9]) {
        iosFps = iosFps ? 0 : 1;
        IOSCfgSave();
    }
    if (now[10] && !prev[10]) {
        iosStrip = iosStrip ? 0 : 1;
        if (!iosStrip)
            iosEdit = 0;
        IOSCfgSave();
    }

    int32 mask = 0;
    for (int32 d = 0; d < 4; ++d) {
        if (dir[d])
            mask |= (1 << d);
    }
    for (int32 b = 1; b < 4; ++b) {
        if (now[b])
            mask |= (1 << (b + 3));
    }
    if (mask != prevMask) {
        PrintLog(PRINT_NORMAL, "touch mask: %d", mask);
        prevMask = mask;
    }

    auto apply = [&](InputState *k0, InputState *k1, bool32 nowv, bool32 prevv) {
        if (nowv) {
            k0->down = true;
            k1->down = true;
            if (!prevv) {
                k0->press = true;
                k1->press = true;
            }
        }
    };
    if (!iosEdit) {
        apply(&controller[0].keyUp, &controller[1].keyUp, dir[0], prevDir[0]);
        apply(&controller[0].keyDown, &controller[1].keyDown, dir[1], prevDir[1]);
        apply(&controller[0].keyLeft, &controller[1].keyLeft, dir[2], prevDir[2]);
        apply(&controller[0].keyRight, &controller[1].keyRight, dir[3], prevDir[3]);
        apply(&controller[0].keyA, &controller[1].keyA, now[1], prev[1]);
        apply(&controller[0].keyB, &controller[1].keyB, now[2], prev[2]);
        apply(&controller[0].keyStart, &controller[1].keyStart, now[3], prev[3]);
    }

    for (int32 b = 0; b < 12; ++b) {
        prev[b]    = now[b];
        iosHeld[b] = now[b];
    }
    for (int32 d = 0; d < 4; ++d) {
        prevDir[d] = dir[d];
        iosDir[d]  = dir[d];
    }
    iosStickOn = stickOn;
    iosKnobX   = knobX;
    iosKnobY   = knobY;
}

"""

draw = r"""    {
        static SDL_Texture *iosDisc      = NULL;
        static SDL_Texture *iosRing      = NULL;
        static SDL_Renderer *iosTexOwner = NULL;
        static bool iosLogged            = false;
        int outW = 0, outH = 0, lw = 0, lh = 0;
        float sx = 1.0f, sy = 1.0f;
        SDL_GetRendererOutputSize(renderer, &outW, &outH);
        SDL_RenderGetLogicalSize(renderer, &lw, &lh);
        SDL_RenderGetScale(renderer, &sx, &sy);
        SDL_RenderSetClipRect(renderer, NULL);
        SDL_RenderSetViewport(renderer, NULL);
        int W = lw ? lw : (int)(outW / sx);
        int H = lh ? lh : (int)(outH / sy);
        iosScreenW = W;
        iosScreenH = H;
        IOSComputeLayout();
        static Uint32 fpsLast = 0;
        static int fpsFrames  = 0;
        static int fpsShown   = 0;
        Uint32 nowT           = SDL_GetTicks();
        ++fpsFrames;
        if (fpsLast == 0)
            fpsLast = nowT;
        if (nowT - fpsLast >= 500) {
            fpsShown  = (int)((fpsFrames * 1000) / (nowT - fpsLast));
            fpsFrames = 0;
            fpsLast   = nowT;
        }
        if (!iosLogged) {
            iosLogged = true;
            PrintLog(PRINT_NORMAL, "IOSOVERLAY v0.7 screen=%dx%d", W, H);
        }

        if (iosTexOwner != renderer) {
            iosTexOwner = renderer;
            iosDisc     = NULL;
            iosRing     = NULL;
            const int N = 128;
            static Uint32 px[128 * 128];
            SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "linear");
            for (int pass = 0; pass < 2; ++pass) {
                for (int y = 0; y < N; ++y) {
                    for (int x = 0; x < N; ++x) {
                        float dx = x + 0.5f - N / 2.0f;
                        float dy = y + 0.5f - N / 2.0f;
                        float d  = (float)SDL_sqrt(dx * dx + dy * dy);
                        float R  = N / 2.0f - 1.0f;
                        float a  = R - d + 0.5f;
                        if (pass == 1) {
                            float a2 = d - (R - 7.0f) + 0.5f;
                            if (a2 < a)
                                a = a2;
                        }
                        if (a < 0.0f)
                            a = 0.0f;
                        if (a > 1.0f)
                            a = 1.0f;
                        px[y * N + x] = ((Uint32)(a * 255.0f) << 24) | 0x00FFFFFF;
                    }
                }
                SDL_Texture *tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STATIC, N, N);
                if (tex) {
                    SDL_UpdateTexture(tex, NULL, px, N * 4);
                    SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND);
                }
                if (pass == 0)
                    iosDisc = tex;
                else
                    iosRing = tex;
            }
            SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "nearest");
        }

        if (iosDisc && iosRing) {
            float op = iosOpacity;
            auto drawTex = [&](SDL_Texture *tex, float cx, float cy, float r, float alpha) {
                if (alpha < 0.0f)
                    alpha = 0.0f;
                if (alpha > 1.0f)
                    alpha = 1.0f;
                SDL_SetTextureAlphaMod(tex, (Uint8)(alpha * 255.0f));
                SDL_Rect d;
                d.x = (int)(cx - r);
                d.y = (int)(cy - r);
                d.w = (int)(r * 2.0f);
                d.h = (int)(r * 2.0f);
                SDL_RenderCopy(renderer, tex, NULL, &d);
            };
            auto bar = [&](float cx, float cy, float w, float h, float alpha) {
                if (alpha > 1.0f)
                    alpha = 1.0f;
                SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
                SDL_SetRenderDrawColor(renderer, 255, 255, 255, (Uint8)(alpha * 255.0f));
                SDL_Rect d;
                d.x = (int)(cx - w / 2.0f);
                d.y = (int)(cy - h / 2.0f);
                d.w = (int)w;
                d.h = (int)h;
                SDL_RenderFillRect(renderer, &d);
            };

            if (!iosHide) {
                IOSCircle &sb = iosLayout[0];
                if (!iosPadMode) {
                    drawTex(iosDisc, sb.x, sb.y, sb.r, op * 0.3f);
                    drawTex(iosRing, sb.x, sb.y, sb.r, op * 1.4f);
                    drawTex(iosDisc, iosKnobX, iosKnobY, sb.r * 0.42f, op * (iosStickOn ? 1.5f : 0.9f));
                }
                else {
                    drawTex(iosRing, sb.x, sb.y, sb.r, op * 0.6f);
                    drawTex(iosDisc, sb.x, sb.y, sb.r * 0.3f, op * 0.4f);
                    float off = sb.r * 0.62f;
                    float ar  = sb.r * 0.42f;
                    float ox[4] = { 0.0f, 0.0f, -off, off };
                    float oy[4] = { -off, off, 0.0f, 0.0f };
                    for (int d = 0; d < 4; ++d) {
                        drawTex(iosDisc, sb.x + ox[d], sb.y + oy[d], ar, iosDir[d] ? op * 1.5f : op * 0.45f);
                        drawTex(iosRing, sb.x + ox[d], sb.y + oy[d], ar, op * 1.2f);
                    }
                }

                for (int b = 1; b < 4; ++b) {
                    IOSCircle &c = iosLayout[b];
                    drawTex(iosDisc, c.x, c.y, c.r, iosHeld[b] ? op * 1.4f : op * 0.4f);
                    drawTex(iosRing, c.x, c.y, c.r, op * 1.4f);
                }

                if (iosEdit) {
                    for (int b = 0; b < 4; ++b) {
                        IOSCircle &c = iosLayout[b];
                        drawTex(iosRing, c.x, c.y, c.r * 1.18f, iosDragIdx == b ? 1.0f : 0.7f);
                    }
                }

            }
            if (iosStrip) {
                if (!iosHide) {
                    const int sb[5] = { 4, 5, 7, 8, 9 };
                    for (int k = 0; k < 5; ++k) {
                        int b        = sb[k];
                        IOSCircle &c = iosLayout[b];
                        bool lit     = iosHeld[b] || (b == 7 && iosEdit) || (b == 9 && iosFps);
                        drawTex(iosDisc, c.x, c.y, c.r, lit ? op * 1.5f : op * 0.4f);
                    }
                    IOSCircle &mi = iosLayout[4];
                    IOSCircle &pl = iosLayout[5];
                    IOSCircle &mv = iosLayout[7];
                    IOSCircle &pm = iosLayout[8];
                    IOSCircle &fp = iosLayout[9];
                    bar(mi.x, mi.y, mi.r * 1.0f, mi.r * 0.2f, op * 2.2f);
                    bar(pl.x, pl.y, pl.r * 1.0f, pl.r * 0.2f, op * 2.2f);
                    bar(pl.x, pl.y, pl.r * 0.2f, pl.r * 1.0f, op * 2.2f);
                    for (int d = 0; d < 4; ++d) {
                        float dx = d == 2 ? -1.0f : (d == 3 ? 1.0f : 0.0f);
                        float dy = d == 0 ? -1.0f : (d == 1 ? 1.0f : 0.0f);
                        drawTex(iosDisc, mv.x + dx * mv.r * 0.55f, mv.y + dy * mv.r * 0.55f, mv.r * 0.17f, op * 2.4f);
                    }
                    if (iosPadMode) {
                        bar(pm.x, pm.y, pm.r * 1.0f, pm.r * 0.28f, op * 2.2f);
                        bar(pm.x, pm.y, pm.r * 0.28f, pm.r * 1.0f, op * 2.2f);
                    }
                    else {
                        drawTex(iosDisc, pm.x, pm.y, pm.r * 0.4f, op * 2.2f);
                    }
                    const float bh[3] = { 0.5f, 0.9f, 0.7f };
                    for (int k = 0; k < 3; ++k)
                        bar(fp.x + (k - 1) * fp.r * 0.45f, fp.y + fp.r * 0.45f - fp.r * bh[k] / 2.0f, fp.r * 0.28f, fp.r * bh[k], op * 2.4f);
                }
                IOSCircle &ey = iosLayout[6];
                float ea      = iosHide ? op * 0.8f : op * 1.4f;
                drawTex(iosRing, ey.x, ey.y, ey.r, ea);
                drawTex(iosDisc, ey.x, ey.y, ey.r * 0.38f, iosHeld[6] ? ea * 1.5f : ea);
            }

            IOSCircle &hd = iosLayout[10];
            if (iosStrip) {
                drawTex(iosDisc, hd.x, hd.y, hd.r, iosHeld[10] ? op * 1.5f : op * 0.4f);
                for (int k = -1; k <= 1; ++k)
                    drawTex(iosDisc, hd.x + k * hd.r * 0.5f, hd.y, hd.r * 0.14f, op * 2.4f);
            }
            else {
                drawTex(iosRing, hd.x, hd.y, hd.r * 0.5f, op * 0.9f);
                drawTex(iosDisc, hd.x, hd.y, hd.r * 0.2f, op * 0.9f);
            }

            if (iosFps) {
                static const unsigned short fpsFont[10] = { 0x7B6F, 0x2C97, 0x73E7, 0x73CF, 0x5BC9, 0x79CF, 0x79EF, 0x7249, 0x7BEF, 0x7BCF };
                int val = fpsShown;
                if (val > 999)
                    val = 999;
                int digits[3];
                int nd = 0;
                if (val >= 100)
                    digits[nd++] = val / 100;
                if (val >= 10)
                    digits[nd++] = (val / 10) % 10;
                digits[nd++] = val % 10;
                int ps = H / 170;
                if (ps < 3)
                    ps = 3;
                int x0 = (int)(0.025f * H);
                int y0 = (int)(0.02f * H);
                SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
                SDL_SetRenderDrawColor(renderer, 0, 0, 0, 120);
                SDL_Rect bg;
                bg.x = x0 - ps;
                bg.y = y0 - ps;
                bg.w = nd * 4 * ps + ps;
                bg.h = 7 * ps;
                SDL_RenderFillRect(renderer, &bg);
                SDL_SetRenderDrawColor(renderer, 255, 255, 255, 230);
                for (int i = 0; i < nd; ++i) {
                    for (int row = 0; row < 5; ++row) {
                        for (int col = 0; col < 3; ++col) {
                            if (fpsFont[digits[i]] & (1 << (14 - (row * 3 + col)))) {
                                SDL_Rect cell;
                                cell.x = x0 + i * 4 * ps + col * ps;
                                cell.y = y0 + row * ps;
                                cell.w = ps;
                                cell.h = ps;
                                SDL_RenderFillRect(renderer, &cell);
                            }
                        }
                    }
                }
            }
        }
    }
"""

patch(base + "Input/Input.hpp", r"^struct ControllerState \{", lambda m: decl + m.group(0))
patch(base + "Input/Input.cpp", r"^void RSDK::ProcessInput\(\)", lambda m: logic + "void RSDK::ProcessInputReal()")
patch(base + "Input/Input.cpp", r"^void RSDK::ProcessInputDevices\(\)",
      lambda m: "void RSDK::ProcessInput()\n{\n    ProcessInputReal();\n    IOSTouchUpdate();\n}\n\n" + m.group(0))
patch(base + "Graphics/SDL2/SDL2RenderDevice.cpp", r"^(\s*)SDL_RenderPresent\(renderer\);", lambda m: draw + m.group(0))
print("all touch patches applied")
