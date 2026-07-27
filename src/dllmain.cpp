#include <windows.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <iostream>

// Link necessary libraries via pragma
#pragma comment(lib, "d3d12.lib")
#pragma comment(lib, "dxgi.lib")

// Global Direct3D 12 Variables
ID3D12Device* g_pd3dDevice = nullptr;
IDXGIFactory4* g_pFactory = nullptr;

// Function pointer for the original OpenGL SwapBuffers
typedef BOOL(WINAPI* PFN_WGLSWAPBUFFERS)(HDC);
PFN_WGLSWAPBUFFERS Original_wglSwapBuffers = nullptr;

// Initialize Direct3D 12 Device
void InitD3D12() {
    if (FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&g_pFactory)))) {
        return; // Failed to create DXGI Factory
    }
    
    // Attempt to create a D3D12 hardware device
    if (FAILED(D3D12CreateDevice(nullptr, D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&g_pd3dDevice)))) {
        return; // D3D12 is not supported on this system
    }
    
    // Future Expansion: Create CommandQueue, SwapChain, and RenderTargets here
}

// Hooked wglSwapBuffers - This runs every time a frame is rendered in Minecraft
extern "C" __declspec(dllexport) BOOL WINAPI wglSwapBuffers(HDC hdc) {
    
    // TODO: Add your D3D12 rendering, overlays, or engine logic here!
    // This executes right before the game presents the frame to the screen.

    // Call the original OpenGL function so the game doesn't break/crash
    if (Original_wglSwapBuffers) {
        return Original_wglSwapBuffers(hdc);
    }
    return FALSE;
}

// DLL Entry Point
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    HMODULE hOriginalGL = NULL;
    char sysDir[MAX_PATH];

    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
        
        // 1. Get path to the REAL opengl32.dll in Windows System32 folder
        GetSystemDirectoryA(sysDir, MAX_PATH);
        strcat_s(sysDir, sizeof(sysDir), "\\opengl32.dll");
        
        // 2. Load the real OpenGL library to act as a proxy
        hOriginalGL = LoadLibraryA(sysDir);
        if (hOriginalGL) {
            // Find the original function address
            Original_wglSwapBuffers = (PFN_WGLSWAPBUFFERS)GetProcAddress(hOriginalGL, "wglSwapBuffers");
        }

        // 3. Initialize our custom D3D12 layer
        InitD3D12();
        break;

    case DLL_PROCESS_DETACH:
        // Cleanup memory to prevent leaks when the game closes
        if (g_pd3dDevice) g_pd3dDevice->Release();
        if (g_pFactory) g_pFactory->Release();
        break;
    }
    return TRUE;
}
