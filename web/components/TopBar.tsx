import Link from "next/link";

import { auth } from "@/auth";
import NavLinks from "@/components/NavLinks";
import UserNav from "@/components/UserNav";

function Wordmark() {
  return (
    <Link href="/" className="group flex items-center gap-2.5" aria-label="CodeBuddy home">
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
        <rect
          x="11"
          y="1.5"
          width="13.4"
          height="13.4"
          rx="2"
          transform="rotate(45 11 1.5)"
          stroke="var(--color-accent)"
          strokeWidth="1.6"
        />
        <circle cx="11" cy="11" r="2.4" fill="var(--color-live)" />
      </svg>
      <span className="font-display text-[0.98rem] font-semibold tracking-tight text-ink">
        codebuddy
      </span>
    </Link>
  );
}

export default async function TopBar() {
  const session = await auth();

  return (
    <header className="sticky top-0 z-30 border-b border-line/80 bg-ground/70 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5 sm:px-8">
        <div className="flex items-center gap-8">
          <Wordmark />
          {session?.user && <NavLinks />}
        </div>
        {session?.user ? (
          <UserNav email={session.user.email ?? ""} image={session.user.image ?? null} />
        ) : (
          <span className="kicker hidden sm:block">agentic app builder</span>
        )}
      </div>
    </header>
  );
}
