import { spawn } from "child_process";
import path from "path";

export async function POST(request: Request) {
  const { mode, url, skipEnrich, maxPosts } = await request.json();

  // Next.js dev server cwd is dashboard/, project root is one level up
  const projectRoot = path.resolve(process.cwd(), "..");

  const args = ["-u", "-m"];
  if (mode === "csv") {
    args.push("scripts.run_from_csv");
    if (maxPosts) args.push("--max-posts", String(maxPosts));
    if (skipEnrich) args.push("--skip-enrich");
  } else {
    args.push("scripts.run_pipeline", "--profile", url);
    if (maxPosts) args.push("--max-posts", String(maxPosts));
    if (skipEnrich) args.push("--skip-enrich");
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const proc = spawn("python3", args, {
        cwd: projectRoot,
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
      });

      const send = (obj: object) => {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(obj)}\n\n`)
        );
      };

      proc.stdout.on("data", (data: Buffer) => {
        send({ log: data.toString() });
      });

      proc.stderr.on("data", (data: Buffer) => {
        send({ log: data.toString() });
      });

      proc.on("close", (code: number) => {
        send({ done: true, code });
        controller.close();
      });

      proc.on("error", (err: Error) => {
        send({ error: err.message });
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}
