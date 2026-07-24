import { NextRequest } from "next/server";

import { mintServiceToken } from "@/lib/api";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

async function proxy(req: NextRequest, path: string[]): Promise<Response> {
  const token = await mintServiceToken();
  if (!token) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json" },
    });
  }

  const targetUrl = `${API_BASE_URL}/api/${path.join("/")}${req.nextUrl.search}`;

  const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
  const contentType = req.headers.get("content-type");
  if (contentType) headers["content-type"] = contentType;

  const init: RequestInit = { method: req.method, headers };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  const upstream = await fetch(targetUrl, init);

  const respHeaders = new Headers();
  const upstreamContentType = upstream.headers.get("content-type");
  if (upstreamContentType) respHeaders.set("content-type", upstreamContentType);
  respHeaders.set("cache-control", "no-cache, no-transform");
  respHeaders.set("x-accel-buffering", "no"); // disable proxy buffering for SSE

  if (!upstream.body) {
    return new Response(null, { status: upstream.status, headers: respHeaders });
  }

  // Explicitly pump the upstream body so chunks flush as they arrive (SSE) rather
  // than being buffered until the whole response completes.
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const reader = upstream.body!.getReader();
      try {
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }
        controller.close();
      } catch (err) {
        controller.error(err);
      }
    },
  });

  return new Response(stream, { status: upstream.status, headers: respHeaders });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
