import { sha256Hex } from './sha256.js';

// Canonical JSON: sorted keys, undefined dropped, non-finite numbers refused.
// The same value always yields the same bytes, so hashes are stable across machines.
export function canonicalJson(value) {
  if (value === null) return 'null';
  switch (typeof value) {
    case 'string':
      return JSON.stringify(value);
    case 'boolean':
      return value ? 'true' : 'false';
    case 'number':
      if (!Number.isFinite(value)) throw new TypeError('non-finite number is not canonical');
      return JSON.stringify(value);
    case 'object':
      if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(',') + ']';
      return '{' + Object.keys(value)
        .filter((k) => value[k] !== undefined)
        .sort()
        .map((k) => JSON.stringify(k) + ':' + canonicalJson(value[k]))
        .join(',') + '}';
    default:
      throw new TypeError(`value of type ${typeof value} is not canonical JSON`);
  }
}

export const hashOf = (value) => 'sha256:' + sha256Hex(canonicalJson(value));

// Round-trips through canonical JSON: a detached copy that is guaranteed to be plain data.
export const plainCopy = (value) => JSON.parse(canonicalJson(value));

export function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const k of Object.keys(value)) deepFreeze(value[k]);
  }
  return value;
}

// Returns the dotted path of the first forbidden key found, or null.
export function findForbiddenKey(value, forbidden, path = '') {
  if (!value || typeof value !== 'object') return null;
  for (const k of Object.keys(value)) {
    const here = path ? `${path}.${k}` : k;
    if (forbidden.includes(k.toLowerCase())) return here;
    const inner = findForbiddenKey(value[k], forbidden, here);
    if (inner) return inner;
  }
  return null;
}
