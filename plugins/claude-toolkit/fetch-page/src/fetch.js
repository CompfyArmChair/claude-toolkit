export const FETCH_TIMEOUT_MS = 30_000;
export const BROWSER_UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

// Content-Type subtypes, beyond text/*, that are structured text rather
// than binary (Important I2 / spec section 4.2's text passthrough scope).
const TEXT_SUBTYPES = new Set([
  'application/json', 'application/xml', 'application/javascript',
  'application/ecmascript', 'application/yaml', 'application/x-yaml',
]);

export async function fetchUrl(url) {
  const res = await fetch(url, {
    redirect: 'follow',
    headers: {
      'user-agent': BROWSER_UA,
      accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.9,*/*;q=0.8',
      'accept-language': 'en-GB,en;q=0.9',
    },
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  });
  const contentType = res.headers.get('content-type') ?? '';
  return { status: res.status, finalUrl: res.url, body: await readBody(res, contentType) };
}

// The media type alone (Content-Type with parameters - charset, boundary,
// etc. - stripped, lower-cased). Charset is resolved separately below.
function mediaTypeOf(contentType) {
  return contentType.split(';')[0].trim().toLowerCase();
}

// Four body kinds, discriminated by media type:
//   pdf         - raw-bytes passthrough (the Read tool renders PDFs natively)
//   html        - goes through Defuddle extraction
//   text        - non-HTML text (raw.githubusercontent.com, .md, .json, ...)
//                 deposited verbatim; HTML-parsing raw source would eat
//                 angle-bracket content (List<string> parses as a tag and
//                 vanishes)
//   unsupported - anything else (images, archives, fonts, ...): not text,
//                 so decoding it as text would silently deposit a wall of
//                 U+FFFD replacement characters under verdict OK
function bodyKindFor(mediaType) {
  if (mediaType === 'application/pdf') return 'pdf';
  if (mediaType === '' || mediaType === 'text/html' || mediaType === 'application/xhtml+xml') return 'html';
  if (mediaType.startsWith('text/') || TEXT_SUBTYPES.has(mediaType) || /\+(json|xml)$/.test(mediaType)) return 'text';
  return 'unsupported';
}

async function readBody(res, contentType) {
  const mediaType = mediaTypeOf(contentType);
  const kind = bodyKindFor(mediaType);

  if (kind === 'unsupported') {
    // Never buffer a body we are not going to use - a multi-MB binary
    // costs nothing beyond the headers already read.
    await res.body?.cancel();
    return { kind, mediaType };
  }
  if (kind === 'pdf') {
    return { kind, bytes: Buffer.from(await res.arrayBuffer()) };
  }

  // html/text: read the body once as bytes and decode with the resolved
  // charset. Response.text() always decodes as UTF-8 and silently replaces
  // every byte of a legacy-encoded page (windows-1252, ISO-8859-*,
  // Shift_JIS, ...) with U+FFFD - resolve the real charset first instead.
  const bytes = Buffer.from(await res.arrayBuffer());
  return { kind, text: decodeBody(bytes, contentType, kind) };
}

// Charset label resolution order: the Content-Type charset parameter; for
// HTML only, a <meta charset> / http-equiv content-type sniff of the first
// 1KB; else utf-8. An unrecognized label falls back to utf-8 rather than
// throwing.
function resolveCharsetLabel(contentType, bytes, kind) {
  const headerMatch = contentType.match(/charset=\s*"?([^;"]+)"?/i);
  if (headerMatch) return headerMatch[1].trim().toLowerCase();
  if (kind === 'html') {
    const head = bytes.subarray(0, 1024).toString('latin1');
    const metaMatch = head.match(/<meta[^>]+charset=["']?([\w-]+)/i);
    if (metaMatch) return metaMatch[1].toLowerCase();
  }
  return 'utf-8';
}

function decodeBody(bytes, contentType, kind) {
  const label = resolveCharsetLabel(contentType, bytes, kind);
  try {
    return new TextDecoder(label).decode(bytes);
  } catch (err) {
    if (err instanceof RangeError) return new TextDecoder('utf-8').decode(bytes);
    throw err;
  }
}
