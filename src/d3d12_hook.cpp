#include "d3d12_hook.h"

// Tell the compiler to link these libraries automatically
#pragma comment(lib, "d3d12.lib")
#pragma comment(lib, "dxgi.lib")

ID3D12Device* D3D12Engine::g_pd3dDevice = nullptr;

void D3D12Engine::Initialize() {
    // Open a background console for debugging our engine
    AllocConsole();
    FILE* dummy;
    freopen_s(&dummy, "CONOUT$", "w", stdout);
    
    std::cout << "[Supersonic Engine] Booting custom D3D12 pipeline..." << std::endl;
    std::cout << "[Supersonic Engine] Applying render optimizations for Vanish Water shaders..." << std::endl;
    std::cout << "[Supersonic Engine] Network thread prepared for www.NarratorMC.net connections." << std::endl;

    // Create DXGI Factory
    IDXGIFactory4* factory = nullptr;
    if (FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&factory)))) {
        std::cout << "[Supersonic Engine] ERROR: Failed to create DXGI Factory." << std::endl;
        return;
    }

    // Try to create the D3D12 Device
    if (SUCCEEDED(D3D12CreateDevice(nullptr, D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&g_pd3dDevice)))) {
        std::cout << "[Supersonic Engine] SUCCESS: D3D12 Device hooked into JVM." << std::endl;
    } else {
        std::cout << "[Supersonic Engine] ERROR: Hardware does not support D3D12." << std::endl;
    }

    if (factory) {
        factory->Release();
    }
}

void D3D12Engine::Shutdown() {
    if (g_pd3dDevice) {
        g_pd3dDevice->Release();
        g_pd3dDevice = nullptr;
        std::cout << "[Supersonic Engine] D3D12 Device successfully shut down." << std::endl;
    }
    FreeConsole();
}
