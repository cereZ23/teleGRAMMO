/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  typescript: {
    // Type errors are handled by IDE and separate CI job
    ignoreBuildErrors: true,
  },
  eslint: {
    // ESLint is run separately in CI
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://api:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
