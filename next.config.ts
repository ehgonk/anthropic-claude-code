import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Deck.gl e MapLibre precisam ser transpilados no bundle do Next.js
  transpilePackages: ["@deck.gl/core", "@deck.gl/layers", "@deck.gl/geo-layers", "@deck.gl/react"],

  // Evita que o Prisma client seja incluído no bundle do browser
  serverExternalPackages: ["@prisma/client", "@prisma/adapter-neon", "@neondatabase/serverless"],
}

export default nextConfig
