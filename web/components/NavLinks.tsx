"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Build" },
  { href: "/apps", label: "My apps" },
];

export default function NavLinks() {
  const pathname = usePathname();

  return (
    <nav className="hidden items-center gap-1 sm:flex">
      {LINKS.map((link) => {
        const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
              active ? "text-ink" : "text-muted hover:text-ink"
            }`}
          >
            {link.label}
            {active && <span className="mx-3 block h-px bg-accent" aria-hidden />}
          </Link>
        );
      })}
    </nav>
  );
}
