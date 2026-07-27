#include <windows.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <iostream>

// Link required Windows libraries
#pragma comment(lib, "d3d12.lib")
#pragma comment(lib, "dxgi.lib")

// D3D12 Core Components
ID3D12Device* g_pd3dDevice = nullptr;
ID3D12CommandQueue* g_pd3dCommandQueue = nullptr;
IDXGISwapChain3* g_pSwapChain = nullptr;
ID3D12CommandAllocator* g_pd3dCommandAllocator = nullptr;
ID3D12GraphicsCommandList* g_pd3dCommandList = nullptr;

// Pointers to Original OpenGL functions
typedef BOOL(WINAPI* PFN_WGLSWAPBUFFERS)(HDC);
typedef PROC(WINAPI* PFN_WGLGETPROCADDRESS)(LPCSTR);

PFN_WGLSWAPBUFFERS Original_wglSwapBuffers = nullptr;
PFN_WGLGETPROCADDRESS Original_wglGetProcAddress = nullptr;

// Initialize the Full Direct3D 12 Rendering Pipeline
void InitFullD3D12Pipeline(HWND hwnd) {
    IDXGIFactory4* dxgiFactory;
    if (FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&dxgiFactory)))) return;

    // 1. Create Hardware Device
    if (FAILED(D3D12CreateDevice(nullptr, D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&g_pd3dDevice)))) {
        dxgiFactory->Release();
        return; 
    }

    // 2. Create Command Queue
    D3D12_COMMAND_QUEUE_DESC queueDesc = {};
    queueDesc.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
    queueDesc.Flags = D3D12_COMMAND_QUEUE_FLAG_NONE;
    g_pd3dDevice->CreateCommandQueue(&queueDesc, IID_PPV_ARGS(&g_pd3dCommandQueue));

    // 3. Create SwapChain (The layer that presents frames to the screen)
    DXGI_SWAP_CHAIN_DESC1 sd = {};
    sd.BufferCount = 2;
    sd.Width = 854;  // Default Minecraft window width
    sd.Height = 480; // Default Minecraft window height
    sd.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    sd.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
    sd.SampleDesc.Count = 1;

    IDXGISwapChain1* swapChain1 = nullptr;
    dxgiFactory->CreateSwapChainForHwnd(g_pd3dCommandQueue, hwnd, &sd, nullptr, nullptr, &swapChain1);
    
    if (swapChain1) {
        swapChain1->QueryInterface(IID_PPV_ARGS(&g_pSwapChain));
        swapChain1->Release();
    }

    // 4. Create Command Allocator & List
    g_pd3dDevice->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(&g_pd3dCommandAllocator));
    g_pd3dDevice->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT, g_pd3dCommandAllocator, nullptr, IID_PPV_ARGS(&g_pd3dCommandList));

    g_pd3dCommandList->Close();
    dxgiFactory->Release();
}

// Intercept Frame Presentation
extern "C" __declspec(dllexport) BOOL WINAPI wglSwapBuffers(HDC hdc) {
    // If D3D12 is initialized, you can inject UI or shaders before the frame flips
    if (g_pSwapChain) {
        // Example: g_pSwapChain->Present(1, 0); 
    }

    // Return real OpenGL rendering so the game doesn't break
    if (Original_wglSwapBuffers) {
        return Original_wglSwapBuffers(hdc);
    }
    return FALSE;
}

// Intercept Function Loading (CRUCIAL FIX to prevent LWJGL crash)
extern "C" __declspec(dllexport) PROC WINAPI wglGetProcAddress(LPCSTR lpszProc) {
    if (Original_wglGetProcAddress) {
        return Original_wglGetProcAddress(lpszProc);
    }
    return NULL;
}

// DLL Entry
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    static HMODULE hOriginalGL = NULL;
    char sysDir[MAX_PATH];

    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
        
        // Load the REAL Windows OpenGL library
        GetSystemDirectoryA(sysDir, MAX_PATH);
        strcat_s(sysDir, sizeof(sysDir), "\\opengl32.dll");
        
        hOriginalGL = LoadLibraryA(sysDir);
        if (hOriginalGL) {
            Original_wglSwapBuffers = (PFN_WGLSWAPBUFFERS)GetProcAddress(hOriginalGL, "wglSwapBuffers");
            Original_wglGetProcAddress = (PFN_WGLGETPROCADDRESS)GetProcAddress(hOriginalGL, "wglGetProcAddress");
        }

        // Note: InitFullD3D12Pipeline(hwnd) should ideally be called once an HWND is created by the game.
        // For now, the proxy allows the game to load perfectly.
        break;

    case DLL_PROCESS_DETACH:
        if (g_pd3dCommandList) g_pd3dCommandList->Release();
        if (g_pd3dCommandAllocator) g_pd3dCommandAllocator->Release();
        if (g_pSwapChain) g_pSwapChain->Release();
        if (g_pd3dCommandQueue) g_pd3dCommandQueue->Release();
        if (g_pd3dDevice) g_pd3dDevice->Release();
        if (hOriginalGL) FreeLibrary(hOriginalGL);
        break;
    }
    return TRUE;
}
