/** Rating colors for strength display. */
export const RATING_COLORS: Record<number, string> = {
	0: '#dc2626', // red-600
	1: '#ea580c', // orange-600
	2: '#ca8a04', // yellow-600
	3: '#16a34a', // green-600
	4: '#059669' // emerald-600
};

export const RATING_BG_COLORS: Record<number, string> = {
	0: '#450a0a', // red-950
	1: '#431407', // orange-950
	2: '#422006', // yellow-950
	3: '#052e16', // green-950
	4: '#022c22' // emerald-950
};

/** Format large numbers with commas. */
export function formatNumber(n: number | null): string {
	if (n === null) return 'N/A';
	return n.toLocaleString();
}

/** Format hash rate for display. */
export function formatRate(rate: number): string {
	if (rate >= 1e12) return `${(rate / 1e12).toFixed(1)}T H/s`;
	if (rate >= 1e9) return `${(rate / 1e9).toFixed(1)}G H/s`;
	if (rate >= 1e6) return `${(rate / 1e6).toFixed(1)}M H/s`;
	if (rate >= 1e3) return `${(rate / 1e3).toFixed(1)}K H/s`;
	return `${rate.toFixed(0)} H/s`;
}

/** Convert algorithm name to display label. */
export function algorithmLabel(name: string): string {
	return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Convert hardware tier name to display label. */
export function tierLabel(name: string): string {
	return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
