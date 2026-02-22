import { auth } from "@/lib/auth";
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const PROXY_SECRET = process.env.PROXY_SECRET || "";

async function proxyRequest(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const session = await auth();
  const apiPath = path.join("/");
  const url = `${BACKEND_URL}/api/${apiPath}${req.nextUrl.search}`;

  const headers: Record<string, string> = {};

  // Forward content-type
  const contentType = req.headers.get("Content-Type");
  if (contentType) {
    headers["Content-Type"] = contentType;
  }

  // Add auth headers
  if (PROXY_SECRET) {
    headers["X-Proxy-Secret"] = PROXY_SECRET;
  }
  if (session?.user?.id) {
    headers["X-User-Id"] = session.user.id;
    headers["X-User-Email"] = session.user.email || "";
  }

  const body = ["GET", "HEAD"].includes(req.method)
    ? undefined
    : await req.arrayBuffer();

  const response = await fetch(url, {
    method: req.method,
    headers,
    body: body ? Buffer.from(body) : undefined,
  });

  // Handle SSE streaming responses
  const responseContentType = response.headers.get("Content-Type") || "";
  if (responseContentType.includes("text/event-stream")) {
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  }

  // Forward regular responses
  const responseBody = await response.arrayBuffer();
  const responseHeaders = new Headers();
  response.headers.forEach((value, key) => {
    // Skip hop-by-hop headers
    if (!["transfer-encoding", "connection"].includes(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  return new NextResponse(responseBody, {
    status: response.status,
    headers: responseHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
export const PUT = proxyRequest;
