// Safely extracts a human-readable error message from an Axios/FastAPI error.
// FastAPI returns `detail` as a plain string for normal errors (e.g.
// "Email already registered"), but as an ARRAY of Pydantic validation
// objects ({type, loc, msg, input, ctx}) for 422 validation errors.
// Rendering that array directly (e.g. via toast.error) crashes React with
// "Objects are not valid as a React child" - this always returns a string.
export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const detail = error?.response?.data?.detail;

  if (!detail) return fallback;

  if (Array.isArray(detail)) {
    return detail.map(d => (typeof d === 'string' ? d : d.msg || JSON.stringify(d))).join(', ');
  }

  if (typeof detail === 'string') return detail;

  return fallback;
}
