"use client";

import { signOut } from "next-auth/react";
import { useState } from "react";

export default function UserNav({ email, image }: { email: string; image: string | null }) {
  const [open, setOpen] = useState(false);
  const initial = (email?.[0] ?? "?").toUpperCase();

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full border border-line bg-raised py-1 pl-1 pr-3 transition-colors hover:border-accent/50"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={image} alt="" className="h-6 w-6 rounded-full" />
        ) : (
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent text-xs font-semibold text-[#0b0d12]">
            {initial}
          </span>
        )}
        <span className="hidden max-w-[140px] truncate text-xs text-muted sm:block">{email}</span>
      </button>

      {open && (
        <>
          <button
            className="fixed inset-0 z-40 cursor-default"
            aria-hidden
            tabIndex={-1}
            onClick={() => setOpen(false)}
          />
          <div className="panel absolute right-0 z-50 mt-2 w-56 overflow-hidden p-1 shadow-2xl">
            <div className="px-3 py-2">
              <p className="kicker">Signed in as</p>
              <p className="mt-0.5 truncate text-sm text-ink">{email}</p>
            </div>
            <div className="my-1 h-px bg-line" />
            <button
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="w-full rounded-lg px-3 py-2 text-left text-sm text-muted transition-colors hover:bg-raised hover:text-ink"
            >
              Sign out
            </button>
          </div>
        </>
      )}
    </div>
  );
}
