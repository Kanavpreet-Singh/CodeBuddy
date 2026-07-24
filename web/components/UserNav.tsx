"use client";

import { signOut } from "next-auth/react";

export default function UserNav({ email }: { email: string }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      {email && <span className="opacity-60">{email}</span>}
      <button
        onClick={() => signOut({ callbackUrl: "/login" })}
        className="underline opacity-70 hover:opacity-100"
      >
        Sign out
      </button>
    </div>
  );
}
