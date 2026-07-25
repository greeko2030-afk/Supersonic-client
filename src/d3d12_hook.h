#pragma once
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <iostream>

class D3D12Engine {
public:
    static void Initialize();
    static void Shutdown();
private:
    static ID3D12Device* g_pd3dDevice;
};
