

const nextConfig = {
  // This repo has its own root-level CLAUDE.md; don't let Next.js generate
  // a second, conflicting one under frontend/.
  agentRules: false,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://localhost:8000/api/:path*"
            : "/api/:path*",
      },
    ];
  },
};

export default nextConfig;
