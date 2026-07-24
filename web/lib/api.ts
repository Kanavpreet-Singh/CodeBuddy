import "server-only";

import jwt from "jsonwebtoken";

import { auth } from "@/auth";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

/** Mint a short-lived service token for the current signed-in user. */
export async function mintServiceToken(): Promise<string | null> {
  const session = await auth();
  if (!session?.user?.id) return null;
  return jwt.sign(
    { sub: session.user.id, email: session.user.email },
    process.env.SERVICE_JWT_SECRET as string,
    { algorithm: "HS256", expiresIn: "60s" },
  );
}

/** Server-side fetch against the FastAPI service, authenticated as the current user. */
export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const token = await mintServiceToken();
  if (!token) throw new Error("Unauthorized");
  return fetch(`${API_BASE_URL}/api/${path}`, {
    ...init,
    headers: { ...(init?.headers ?? {}), Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
}
