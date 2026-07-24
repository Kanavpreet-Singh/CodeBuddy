import GenerateForm from "@/components/GenerateForm";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-16">
      <h1 className="text-2xl font-semibold tracking-tight">CodeBuddy</h1>
      <p className="mt-2 text-sm opacity-70">
        Describe an app and watch the agent plan, architect, and code it.
      </p>
      <GenerateForm />
    </main>
  );
}
