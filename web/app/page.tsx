import Link from "next/link";
import { redirect } from "next/navigation";

import { auth } from "@/auth";
import GenerateForm from "@/components/GenerateForm";
import UserNav from "@/components/UserNav";

export default async function Home() {
  const session = await auth();
  if (!session?.user) redirect("/login");

  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-16">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">CodeBuddy</h1>
        <UserNav email={session.user.email ?? ""} />
      </div>
      <p className="mt-2 text-sm opacity-70">
        Describe an app and watch the agent plan, architect, and code it.
      </p>
      <Link href="/apps" className="mt-3 inline-block text-sm underline opacity-70 hover:opacity-100">
        My apps →
      </Link>
      <GenerateForm />
    </main>
  );
}
