import type { NextConfig } from "next";


const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/intelligent_chat/:path*',
        destination: 'http://localhost:8000/api/v1/intelligent_chat/:path*',
      },
    ];
  },
};

export default nextConfig;
