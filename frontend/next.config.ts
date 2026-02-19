import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the Next.js dev server to proxy API requests to Flask
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:5000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
