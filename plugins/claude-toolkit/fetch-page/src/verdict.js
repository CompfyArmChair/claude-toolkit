// Verdicts are routing advice, not gates (spec section 4.2): whatever was
// extracted is always deposited, and a wrong threshold mis-routes visibly
// rather than corrupting silently.
export const THIN_CONTENT_CHARS = 200;

export const BOT_BLOCK_MARKERS = [
  'just a moment',
  'attention required',
  'verify you are human',
  'verifying you are human',
  'enable javascript and cookies',
  'access denied',
  'request blocked',
];

export function classify({ httpStatus, title, markdown }) {
  const reasons = [];

  if (httpStatus === 403 || httpStatus === 429 || httpStatus >= 500) {
    reasons.push(`http-${httpStatus}`);
  }

  // Full-body search: the spec escalates on markers anywhere in the body,
  // and a block notice can sit below a boilerplate preamble.
  const haystack = `${title}\n${markdown}`.toLowerCase();
  const marker = BOT_BLOCK_MARKERS.find((m) => haystack.includes(m));
  if (marker) reasons.push(`bot-marker:${marker}`);

  const chars = markdown.trim().length;
  if (chars < THIN_CONTENT_CHARS) reasons.push(`thin-content:${chars}chars`);

  return { verdict: reasons.length > 0 ? 'ESCALATE' : 'OK', reasons };
}
