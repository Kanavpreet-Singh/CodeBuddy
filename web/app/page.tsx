import { redirect } from "next/navigation";

import { auth } from "@/auth";
import GenerateForm from "@/components/GenerateForm";

export default async function Home() {
  const session = await auth();
  if (!session?.user) redirect("/login");

  return (
    <main className="mx-auto max-w-3xl px-5 py-14 sm:px-8 sm:py-20">
      <div className="animate-rise">
        <p className="kicker">Build · one prompt → running app</p>
        <h1 className="font-display mt-4 text-4xl font-semibold leading-[1.05] tracking-tight sm:text-[3.25rem]">
          Describe an app.
          <br />
          Watch the agent <span className="text-accent">build it.</span>
        </h1>
        <p className="mt-4 max-w-xl text-muted">
          A three-stage agent plans your idea, breaks it into tasks, and writes every file, live.
          When it&apos;s done, run it in a sandbox without leaving the page.
        </p>
      </div>

      <GenerateForm />
    </main>
  );
}
