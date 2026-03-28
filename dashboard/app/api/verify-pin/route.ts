import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const { pin } = await request.json();
  const correct = process.env.PIN_CODE;

  if (!correct) {
    return NextResponse.json({ ok: false }, { status: 500 });
  }

  return NextResponse.json({ ok: pin === correct });
}
