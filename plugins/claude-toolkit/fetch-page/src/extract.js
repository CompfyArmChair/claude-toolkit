import { Defuddle } from 'defuddle/node';
import { JSDOM, VirtualConsole } from 'jsdom';

// Named so extractReadable's third parameter can default to it while a test
// injects a throwing replacement to reach the catch below - Defuddle
// swallows its own internal errors internally and never actually rejects,
// so the catch path is otherwise unreachable from real input.
function defuddleParse(document, url) {
  return Defuddle(document, url, { markdown: true, useAsync: false });
}

// JSDOM, not linkedom: it synthesizes documentElement so degenerate input
// cannot throw, and { url } is required for Defuddle's domain resolution.
// useAsync: false keeps tier 1 to exactly one outbound request.
// Defuddle never signals failure - empty/garbage extraction surfaces as
// thin content in the verdict, and the try/catch covers internal errors.
export async function extractReadable(html, url, parse = defuddleParse) {
  // Defuddle logs its own caught-internal errors via console.error
  // unconditionally, even when extraction fully succeeds (a known internal
  // nwsapi selector issue) - silence it for the call so a successful fetch
  // never prints text that reads like a crash. The markdown result and the
  // downstream thinness check remain the real success/failure signal. This
  // is a global mutation held across an await, which is safe only because
  // this CLI is single-flight (one extraction per process, never
  // concurrent) - a second in-flight call would race it.
  const originalConsoleError = console.error;
  console.error = () => {};
  let dom;
  try {
    // Inside the try: JSDOM's own URL validation throws synchronously (a
    // TypeError from whatwg-url) on a malformed url, and that must surface
    // as an extraction failure like any other, not escape extractReadable.
    dom = new JSDOM(html, { url, virtualConsole: new VirtualConsole() });
    const result = await parse(dom.window.document, url);
    return { markdown: result.content ?? '', title: result.title ?? '', error: null };
  } catch (error) {
    return { markdown: '', title: '', error };
  } finally {
    console.error = originalConsoleError;
    dom?.window.close();
  }
}
